"""
Adım 7 — Ters problem: Bi'yi iç sıcaklık ölçümlerinden ağ ağırlıklarıyla birlikte öğren.

Bi pozitif kalsın diye logaritmik parametre:  Bi = exp(s),  s ∈ ℝ öğrenilir.
    min_{w, s}  L_PDE + λ L_Robin(e^s) + μ mean(θ̂(x_i) − θ_i^ölçüm)²

Ölçümler Adım 6 ile aynı: FDM (N = 201, gerçek Bi = 4.895) iç düğümleri + Gauss gürültüsü.
Ağ, katı kısıt, kolokasyon ve eğitim Adım 4 ile aynı. Doğrulama gerçek Bi'nin seri çözümüne karşı.

Çalıştırma:
    python pinn_inverse.py --bi0 1 --n-data 20 --noise 0.01 --mu 100 --skip 0.02 --tag inv_base_s0
Çıktı: runs/<tag>/{model.pt, history.npz, metrics.json, prediction.npz, data.npz}
"""

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
import torch

from fdm_solver import BI_DEFAULT
from pinn_forward import MLP, collocation, evaluate, residuals, theta_hat
from pinn_hybrid import sensors

HERE = Path(__file__).resolve().parent
torch.set_default_dtype(torch.float64)


def train(args, X_d, y_d):
    torch.manual_seed(args.seed)
    model = MLP(args.width, args.depth)
    s = torch.nn.Parameter(torch.tensor(math.log(args.bi0)))      # Bi = exp(s)
    X_int, X_bot = collocation(args.n_int, args.n_bot, False, args.seed, args.skip)
    Xd, yd = torch.tensor(X_d), torch.tensor(y_d)[:, None]
    hist = {k: [] for k in ("it", "loss", "pde", "rob", "data", "Bi", "phase")}

    def loss_fn():
        Bi = s.exp()
        r_pde, r_rob = residuals(model, X_int, X_bot, Bi)
        l_pde, l_rob = (r_pde ** 2).mean(), (r_rob ** 2).mean()
        l_dat = ((theta_hat(model, Xd) - yd) ** 2).mean() if len(Xd) else torch.zeros(())
        return l_pde + args.lam * l_rob + args.mu * l_dat, l_pde, l_rob, l_dat

    def log(it, phase, terms):
        hist["it"].append(it); hist["phase"].append(phase); hist["Bi"].append(s.exp().item())
        for k, v in zip(("loss", "pde", "rob", "data"), terms):
            hist[k].append(v.item())

    params = list(model.parameters()) + [s]
    t0 = time.perf_counter()
    opt = torch.optim.Adam([{"params": list(model.parameters())}, {"params": [s], "lr": args.lr_bi}], lr=args.lr)
    sched = torch.optim.lr_scheduler.ExponentialLR(opt, gamma=0.1 ** (1 / args.adam))
    for it in range(args.adam):
        opt.zero_grad()
        terms = loss_fn()
        terms[0].backward()
        opt.step(); sched.step()
        if it % 50 == 0 or it == args.adam - 1:
            log(it, 0, terms)
        if it % 1000 == 0:
            print(f"Adam {it:6d}  L = {terms[0].item():.3e}  Bi = {s.exp().item():.4f}  "
                  f"(PDE {terms[1].item():.2e}, Robin {terms[2].item():.2e}, veri {terms[3].item():.2e})", flush=True)

    lbfgs = torch.optim.LBFGS(params, lr=1.0, max_iter=args.lbfgs, max_eval=int(args.lbfgs * 1.25), history_size=50,
                              tolerance_grad=1e-11, tolerance_change=1e-14, line_search_fn="strong_wolfe")
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
    Bi_hat = s.exp().item()
    print(f"L-BFGS bitti: L = {terms[0].item():.3e} · Bi = {Bi_hat:.4f} (gerçek {args.Bi:.4f}) · süre {t_total:.0f} s", flush=True)
    return model, Bi_hat, hist, {"t_total_s": round(t_total, 1), "final_loss": terms[0].item(), "final_pde": terms[1].item(),
                                 "final_robin": terms[2].item(), "final_data": terms[3].item(),
                                 "n_int": int(X_int.shape[0]), "n_bot": int(X_bot.shape[0])}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--Bi", type=float, default=BI_DEFAULT, help="gerçek Bi (ölçümler ve doğrulama)")
    ap.add_argument("--bi0", type=float, default=1.0, help="Bi başlangıç tahmini")
    ap.add_argument("--n-data", type=int, default=20)
    ap.add_argument("--noise", type=float, default=0.01)
    ap.add_argument("--where", default="uniform", choices=["uniform", "corner", "bottom", "top"])
    ap.add_argument("--mu", type=float, default=100.0)
    ap.add_argument("--lam", type=float, default=1.0)
    ap.add_argument("--skip", type=float, default=0.02, help="köşeden δ mesafedeki Robin noktalarını çıkar")
    ap.add_argument("--width", type=int, default=50)
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--n-int", type=int, default=4096)
    ap.add_argument("--n-bot", type=int, default=256)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--lr-bi", type=float, default=1e-2, help="log Bi için Adam öğrenme oranı")
    ap.add_argument("--adam", type=int, default=6000)
    ap.add_argument("--lbfgs", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tag", required=True)
    args = ap.parse_args()

    out = HERE / "runs" / args.tag
    out.mkdir(parents=True, exist_ok=True)
    X_d, y_d, clean = sensors(args.n_data, args.where, args.noise, args.seed, args.Bi)
    print(f"[{args.tag}] Bi₀ = {args.bi0}, {args.n_data} sensör ({args.where}), σ = {args.noise}, μ = {args.mu}, "
          f"skip = {args.skip}, tohum {args.seed}", flush=True)

    model, Bi_hat, hist, info = train(args, X_d, y_d)
    metrics, x, th, ex, fdm = evaluate(model, args.Bi)
    with torch.no_grad():
        fit = theta_hat(model, torch.tensor(X_d)).numpy()[:, 0] if len(X_d) else np.zeros(0)
    rms = lambda a: float(np.sqrt(np.mean(a ** 2))) if a.size else 0.0  # noqa: E731
    metrics.update(info)
    metrics.update({"Bi_true": args.Bi, "Bi_hat": Bi_hat, "Bi_rel_err": abs(Bi_hat - args.Bi) / args.Bi,
                    "bi0": args.bi0, "n_data": args.n_data, "noise": args.noise, "where": args.where, "mu": args.mu,
                    "skip": args.skip, "data_rmse_vs_noisy": rms(fit - y_d), "data_rmse_vs_clean": rms(fit - clean),
                    "noise_rms": rms(y_d - clean), "config": vars(args)})

    torch.save(model.state_dict(), out / "model.pt")
    np.savez_compressed(out / "history.npz", **{k: np.array(v) for k, v in hist.items()})
    np.savez_compressed(out / "prediction.npz", x=x, theta=th, theta_exact=ex, theta_fdm=fdm)
    np.savez_compressed(out / "data.npz", X=X_d, y=y_d, clean=clean)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=1))
    print(json.dumps({k: (round(v, 6) if isinstance(v, float) else v) for k, v in metrics.items() if k != "config"}, indent=1))
