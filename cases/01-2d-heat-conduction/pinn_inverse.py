"""
Adım 7 — Ters problem: Biot sayısını iç sıcaklık ölçümlerinden geri bul.

Adım 6'daki hibrit PINN'in kaybı aynen kullanılır; tek fark Robin koşulundaki Bi'nin artık bilinen bir sabit
değil, ağ ağırlıklarıyla birlikte öğrenilen bir parametre olması:

    L(w, Bi) = L_PDE(w) + λ L_Robin(w, Bi) + μ · mean(θ̂(x_i; w) − θ_i^ölçüm)²
    Bi = exp(β)            (β öğrenilir → Bi > 0 kendiliğinden sağlanır)

Ölçümler Adım 6 ile aynı kaynaktan (FDM, N = 201, gerçek Bi = 4.895) ve aynı gürültüyle gelir.
Başlangıç tahmini Bi₀ = 2, Adım 6'nın "yanlış fizik" değeri.

Çalıştırma:
    python pinn_inverse.py --n-data 20 --tag inv_n20_s0
    python pinn_inverse.py --n-data 20 --skip 0.02 --tag inv_skip_s0     # köşe şeridini Robin kaybından çıkar
Çıktı: runs/<tag>/{model.pt, history.npz, metrics.json, prediction.npz, data.npz}
"""

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
import torch

from fdm_solver import BI_DEFAULT, K_SOLID, L, T_INF, T_WALL
from pinn_forward import MLP, collocation, evaluate, residuals, theta_hat
from pinn_hybrid import sensors

HERE = Path(__file__).resolve().parent
torch.set_default_dtype(torch.float64)


def train(args, X_d, y_d):
    torch.manual_seed(args.seed)
    model = MLP(args.width, args.depth)
    beta = torch.nn.Parameter(torch.tensor(math.log(args.bi0)))      # Bi = exp(β)
    X_int, X_bot = collocation(args.n_int, args.n_bot, False, args.seed, args.skip)
    Xd, yd = torch.tensor(X_d), torch.tensor(y_d)[:, None]
    hist = {"it": [], "loss": [], "pde": [], "rob": [], "data": [], "Bi": [], "phase": []}

    warm = [args.warmup > 0]                                         # ısınma: Robin kapalı, β dondurulmuş

    def loss_fn():
        Bi = beta.exp()
        r_pde, r_rob = residuals(model, X_int, X_bot, Bi)
        l_pde, l_rob = (r_pde ** 2).mean(), (r_rob ** 2).mean()
        l_dat = ((theta_hat(model, Xd) - yd) ** 2).mean()
        lam = 0.0 if warm[0] else args.lam
        return l_pde + lam * l_rob + args.mu * l_dat, l_pde, l_rob, l_dat

    def bi_least_squares():
        """Robin kaybı Bi'de ikinci derece: verili ağ için en iyi Bi = Σ θ̂_η θ̂ / Σ θ̂² (alt kenar noktaları)."""
        tb = theta_hat(model, X_bot)
        tb_eta = torch.autograd.grad(tb, X_bot, torch.ones_like(tb))[0][:, 1:2]
        return float((tb_eta * tb).sum() / (tb ** 2).sum())

    def log(it, phase, terms):
        hist["it"].append(it); hist["phase"].append(phase); hist["Bi"].append(beta.exp().item())
        for k, v in zip(("loss", "pde", "rob", "data"), terms):
            hist[k].append(v.item())

    t0 = time.perf_counter()
    opt = torch.optim.Adam([{"params": model.parameters(), "lr": args.lr},
                            {"params": [beta], "lr": args.lr_bi}])
    sched = torch.optim.lr_scheduler.ExponentialLR(opt, gamma=0.1 ** (1 / args.adam))
    bi_ls = None
    for it in range(args.adam):
        if warm[0] and it == args.warmup:
            warm[0] = False
            bi_ls = bi_least_squares()
            with torch.no_grad():
                beta.fill_(math.log(max(bi_ls, 1e-3)))
            print(f"ısınma bitti ({it}): en küçük kareler Bi = {bi_ls:.4f}", flush=True)
        if warm[0]:
            beta.grad = None
        opt.zero_grad()
        terms = loss_fn()
        terms[0].backward()
        if warm[0]:
            beta.grad = None                                         # β ısınmada güncellenmez
        opt.step(); sched.step()
        if it % 50 == 0 or it == args.adam - 1:
            log(it, 0, terms)
        if it % 1000 == 0:
            print(f"Adam {it:6d}  L = {terms[0].item():.3e}  (PDE {terms[1].item():.2e}, Robin {terms[2].item():.2e}, "
                  f"veri {terms[3].item():.2e})  Bi = {beta.exp().item():.4f}", flush=True)
    bi_adam = beta.exp().item()

    lbfgs = torch.optim.LBFGS([*model.parameters(), beta], lr=1.0, max_iter=args.lbfgs, max_eval=int(args.lbfgs * 1.25),
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
    bi = beta.exp().item()
    print(f"L-BFGS bitti: L = {terms[0].item():.3e} · veri {terms[3].item():.2e} · Bi = {bi:.4f} · süre {t_total:.0f} s",
          flush=True)
    return model, bi, hist, {"t_total_s": round(t_total, 1), "final_loss": terms[0].item(),
                             "final_pde": terms[1].item(), "final_robin": terms[2].item(),
                             "final_data": terms[3].item(), "Bi_after_adam": bi_adam,
                             "Bi_after_warmup": bi_ls,
                             "n_int": int(X_int.shape[0]), "n_bot": int(X_bot.shape[0])}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--Bi", type=float, default=BI_DEFAULT, help="gerçek Bi (yalnız ölçüm üretimi ve doğrulama için)")
    ap.add_argument("--bi0", type=float, default=2.0, help="öğrenilen Bi'nin başlangıç değeri")
    ap.add_argument("--n-data", type=int, default=20)
    ap.add_argument("--noise", type=float, default=0.01, help="ölçüm gürültüsü σ (θ biriminde; 0.01 ≙ 0.5 °C)")
    ap.add_argument("--where", default="uniform", choices=["uniform", "corner", "bottom", "top"])
    ap.add_argument("--mu", type=float, default=1.0, help="veri teriminin ağırlığı")
    ap.add_argument("--lam", type=float, default=1.0)
    ap.add_argument("--skip", type=float, default=0.0, help="köşeden bu mesafedeki Robin noktalarını dışla")
    ap.add_argument("--width", type=int, default=50)
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--n-int", type=int, default=4096)
    ap.add_argument("--n-bot", type=int, default=256)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--lr-bi", type=float, default=1e-2, help="β = ln Bi için Adam öğrenme oranı")
    ap.add_argument("--warmup", type=int, default=0,
                    help="ilk bu kadar Adam adımında Robin terimi kapalı ve Bi sabit; sonunda Bi en küçük karelerle başlatılır")
    ap.add_argument("--adam", type=int, default=6000)
    ap.add_argument("--lbfgs", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tag", required=True)
    args = ap.parse_args()

    out = HERE / "runs" / args.tag
    out.mkdir(parents=True, exist_ok=True)
    X_d, y_d, clean = sensors(args.n_data, args.where, args.noise, args.seed, args.Bi)
    print(f"[{args.tag}] {args.n_data} sensör ({args.where}), σ = {args.noise}, μ = {args.mu}, Bi₀ = {args.bi0}, "
          f"δ = {args.skip}, ısınma {args.warmup}, tohum {args.seed}", flush=True)

    model, bi, hist, info = train(args, X_d, y_d)
    metrics, x, th, ex, fdm = evaluate(model, args.Bi)      # alan, gerçek Bi'nin seri çözümüne karşı
    with torch.no_grad():
        fit = theta_hat(model, torch.tensor(X_d)).numpy()[:, 0]
    rms = lambda a: float(np.sqrt(np.mean(a ** 2))) if a.size else 0.0  # noqa: E731
    # ısı çıkışı tahmini: öğrenilen h ile (gerçek h bilinmiyor)
    h_est = bi * K_SOLID / L
    Q_est = h_est * L * (T_WALL - T_INF) * metrics["int_theta_bottom"]
    metrics.update(info)
    metrics.update({"Bi_true": args.Bi, "Bi_est": bi, "Bi_rel_err": (bi - args.Bi) / args.Bi,
                    "h_est_W_m2K": h_est, "Q_W_m_est": Q_est,
                    "Q_rel_err_est": (Q_est - metrics["Q_W_m_exact"]) / metrics["Q_W_m_exact"],
                    "n_data": args.n_data, "noise": args.noise, "where": args.where, "mu": args.mu,
                    "bi0": args.bi0, "skip": args.skip, "warmup": args.warmup,
                    "data_rmse_vs_noisy": rms(fit - y_d), "data_rmse_vs_clean": rms(fit - clean),
                    "noise_rms": rms(y_d - clean), "config": vars(args)})

    torch.save(model.state_dict(), out / "model.pt")
    np.savez_compressed(out / "history.npz", **{k: np.array(v) for k, v in hist.items()})
    np.savez_compressed(out / "prediction.npz", x=x, theta=th, theta_exact=ex, theta_fdm=fdm)
    np.savez_compressed(out / "data.npz", X=X_d, y=y_d, clean=clean)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=1))
    print(json.dumps({k: (round(v, 6) if isinstance(v, float) else v) for k, v in metrics.items() if k != "config"},
                     indent=1))
