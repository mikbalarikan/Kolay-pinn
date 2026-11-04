"""
Adım 6 — Hibrit PINN: fizik + seyrek, gürültülü ölçümler.

Ölçümler FDM çözümünden (N = 201, CFD yerine geçen referans) alınır; "sensör" konumları
iç bölgedeki ağ düğümlerinden seçilir ve Gauss gürültüsü eklenir:
    θ_i^ölçüm = θ_FDM(x_i) + ε_i,     ε_i ~ N(0, σ²)       (σ = 0.01  ≙  ±0.5 °C)

Kayıp:
    L = L_PDE + λ L_Robin + μ · mean(θ̂(x_i) − θ_i^ölçüm)²

Ağ, katı kısıt, kolokasyon ve eğitim Adım 4 ile aynıdır (pinn_forward.py); tek fark veri terimi.

Çalıştırma:
    python pinn_hybrid.py --n-data 20 --noise 0.01 --where uniform --tag hyb_n20_s001
    python pinn_hybrid.py --n-data 20 --noise 0.01 --where corner  --tag hyb_n20_corner
Çıktı: runs/<tag>/{model.pt, history.npz, metrics.json, prediction.npz, data.npz}
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

from fdm_solver import BI_DEFAULT, solve_fdm
from pinn_forward import MLP, collocation, evaluate, residuals, theta_hat

HERE = Path(__file__).resolve().parent
torch.set_default_dtype(torch.float64)


def sensors(n, where="uniform", noise=0.0, seed=0, Bi=BI_DEFAULT, N=201):
    """FDM ağ düğümlerinden n sensör seç, gürültü ekle. where: uniform | corner | bottom | top."""
    rng = np.random.default_rng(1000 + seed)
    x, _, th = solve_fdm(N, Bi)
    i_all, j_all = np.meshgrid(np.arange(1, N - 1), np.arange(1, N - 1))   # Dirichlet kenarları hariç
    i_all, j_all = i_all.ravel(), j_all.ravel()
    xi, eta = x[i_all], x[j_all]
    if where == "uniform":
        w = np.ones_like(xi)
    elif where == "corner":                       # alt köşelere yakın (r < 0.2)
        r = np.minimum(np.hypot(xi, eta), np.hypot(1 - xi, eta))
        w = (r < 0.2).astype(float)
    elif where == "bottom":                       # alt yüzeye yakın şerit (η < 0.1)
        w = (eta < 0.1).astype(float)
    elif where == "top":                          # soğutulan yüzeyden uzak üst yarı (η > 0.5) — Adım 7
        w = (eta > 0.5).astype(float)
    else:
        raise ValueError(where)
    pick = rng.choice(len(xi), size=n, replace=False, p=w / w.sum())
    X = np.column_stack([xi[pick], eta[pick]])
    clean = th[j_all[pick], i_all[pick]]
    y = clean + rng.normal(0.0, noise, n) if noise > 0 else clean.copy()
    return X, y, clean


def train(args, X_d, y_d):
    torch.manual_seed(args.seed)
    model = MLP(args.width, args.depth)
    X_int, X_bot = collocation(args.n_int, args.n_bot, False, args.seed, args.skip)
    Xd, yd = torch.tensor(X_d), torch.tensor(y_d)[:, None]
    hist = {"it": [], "loss": [], "pde": [], "rob": [], "data": [], "phase": []}

    bi_model = args.Bi if args.bi_model is None else args.bi_model   # modelin "bildiği" Bi (yanlış olabilir)

    def loss_fn():
        r_pde, r_rob = residuals(model, X_int, X_bot, bi_model)
        l_pde, l_rob = (r_pde ** 2).mean(), (r_rob ** 2).mean()
        l_dat = ((theta_hat(model, Xd) - yd) ** 2).mean() if len(Xd) else torch.zeros(())
        return l_pde + args.lam * l_rob + args.mu * l_dat, l_pde, l_rob, l_dat

    def log(it, phase, terms):
        hist["it"].append(it); hist["phase"].append(phase)
        for k, v in zip(("loss", "pde", "rob", "data"), terms):
            hist[k].append(v.item())

    t0 = time.perf_counter()
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    sched = torch.optim.lr_scheduler.ExponentialLR(opt, gamma=0.1 ** (1 / args.adam))
    for it in range(args.adam):
        opt.zero_grad()
        terms = loss_fn()
        terms[0].backward()
        opt.step(); sched.step()
        if it % 50 == 0 or it == args.adam - 1:
            log(it, 0, terms)
        if it % 1000 == 0:
            print(f"Adam {it:6d}  L = {terms[0].item():.3e}  (PDE {terms[1].item():.2e}, Robin {terms[2].item():.2e}, veri {terms[3].item():.2e})", flush=True)

    lbfgs = torch.optim.LBFGS(model.parameters(), lr=1.0, max_iter=args.lbfgs, max_eval=int(args.lbfgs * 1.25),
                              history_size=50, tolerance_grad=1e-11, tolerance_change=1e-14, line_search_fn="strong_wolfe")
    k = [args.adam]

    def closure():
        lbfgs.zero_grad()
        terms = loss_fn()
        terms[0].backward()
        if k[0] % 25 == 0:
            log(k[0], 1, terms)
        k[0] += 1
        return terms[0]

    lbfgs.step(closure)
    terms = loss_fn()
    log(k[0], 1, terms)
    t_total = time.perf_counter() - t0
    print(f"L-BFGS bitti: L = {terms[0].item():.3e} · veri {terms[3].item():.2e} · süre {t_total:.0f} s", flush=True)
    return model, hist, {"t_total_s": round(t_total, 1), "final_loss": terms[0].item(), "final_pde": terms[1].item(),
                         "final_robin": terms[2].item(), "final_data": terms[3].item(),
                         "n_int": int(X_int.shape[0]), "n_bot": int(X_bot.shape[0])}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--Bi", type=float, default=BI_DEFAULT)
    ap.add_argument("--n-data", type=int, default=20)
    ap.add_argument("--noise", type=float, default=0.01, help="ölçüm gürültüsü σ (θ biriminde; 0.01 ≙ 0.5 °C)")
    ap.add_argument("--where", default="uniform", choices=["uniform", "corner", "bottom"])
    ap.add_argument("--mu", type=float, default=1.0, help="veri teriminin ağırlığı")
    ap.add_argument("--bi-model", type=float, default=None,
                    help="kayıptaki Robin koşulunda kullanılan Bi (yanlış fizik deneyi); ölçümler ve referans gerçek --Bi ile")
    ap.add_argument("--lam", type=float, default=1.0)
    ap.add_argument("--skip", type=float, default=0.0)
    ap.add_argument("--width", type=int, default=50)
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--n-int", type=int, default=4096)
    ap.add_argument("--n-bot", type=int, default=256)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--adam", type=int, default=6000)
    ap.add_argument("--lbfgs", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tag", required=True)
    args = ap.parse_args()

    out = HERE / "runs" / args.tag
    out.mkdir(parents=True, exist_ok=True)
    X_d, y_d, clean = sensors(args.n_data, args.where, args.noise, args.seed, args.Bi)
    print(f"[{args.tag}] {args.n_data} sensör ({args.where}), σ = {args.noise}, μ = {args.mu}, tohum {args.seed}", flush=True)

    model, hist, info = train(args, X_d, y_d)
    metrics, x, th, ex, fdm = evaluate(model, args.Bi)
    with torch.no_grad():
        fit = theta_hat(model, torch.tensor(X_d)).numpy()[:, 0]
    metrics.update(info)
    rms = lambda a: float(np.sqrt(np.mean(a ** 2))) if a.size else 0.0  # noqa: E731
    metrics.update({"n_data": args.n_data, "noise": args.noise, "where": args.where, "mu": args.mu,
                    "bi_model": args.Bi if args.bi_model is None else args.bi_model,
                    "data_rmse_vs_noisy": rms(fit - y_d), "data_rmse_vs_clean": rms(fit - clean),
                    "noise_rms": rms(y_d - clean), "config": vars(args)})

    torch.save(model.state_dict(), out / "model.pt")
    np.savez_compressed(out / "history.npz", **{k: np.array(v) for k, v in hist.items()})
    np.savez_compressed(out / "prediction.npz", x=x, theta=th, theta_exact=ex, theta_fdm=fdm)
    np.savez_compressed(out / "data.npz", X=X_d, y=y_d, clean=clean)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=1))
    print(json.dumps({k: (round(v, 6) if isinstance(v, float) else v) for k, v in metrics.items() if k != "config"}, indent=1))
