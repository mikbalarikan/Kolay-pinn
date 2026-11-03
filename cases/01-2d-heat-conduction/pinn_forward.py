"""
Adım 4 — Forward PINN (veri yok, yalnız fizik).

Boyutsuz problem (README, Adım 2):
    θ_ξξ + θ_ηη = 0             (ξ, η) ∈ [0, 1]²
    θ = 1                       ξ = 0, ξ = 1, η = 1
    ∂θ/∂η = Bi θ                η = 0

Ağ:   N(ξ, η) — MLP, tanh, 4 × 50
Katı kısıt (Dirichlet kenarları kayba girmez, yapı gereği sağlanır):
    θ̂(ξ, η) = 1 + ξ(1 − ξ)(1 − η) · N(ξ, η)
Kayıp:
    L = mean(θ̂_ξξ + θ̂_ηη)²|iç  +  λ · mean(∂θ̂/∂η − Bi θ̂)²|η=0
Eğitim: Adam (üstel lr azalması) → L-BFGS (strong Wolfe)

Çalıştırma:
    python pinn_forward.py                       # düzgün kolokasyon (Sobol)
    python pinn_forward.py --corner --tag corner # alt köşelerde sıklaştırılmış noktalar
    python pinn_forward.py --skip 0.02 --tag skip # köşe şeridindeki Robin noktalarını dışla
Çıktı: runs/<tag>/{model.pt, history.npz, metrics.json, prediction.npz}
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
from scipy.stats import qmc

from fdm_solver import BI_DEFAULT, H_CONV, K_SOLID, L, T_INF, T_WALL, analytical, solve_fdm

HERE = Path(__file__).resolve().parent
torch.set_default_dtype(torch.float64)


# ------------------------------------------------------------------ model
class MLP(torch.nn.Module):
    def __init__(self, width=50, depth=4):
        super().__init__()
        layers, d_in = [], 2
        for _ in range(depth):
            layers += [torch.nn.Linear(d_in, width), torch.nn.Tanh()]
            d_in = width
        layers += [torch.nn.Linear(d_in, 1)]
        self.net = torch.nn.Sequential(*layers)
        for m in self.net:
            if isinstance(m, torch.nn.Linear):
                torch.nn.init.xavier_normal_(m.weight)
                torch.nn.init.zeros_(m.bias)

    def forward(self, X):
        return self.net(X)


def theta_hat(model, X):
    """Katı kısıtlı çıktı: üç Dirichlet kenarında tam olarak 1."""
    xi, eta = X[:, :1], X[:, 1:2]
    return 1.0 + xi * (1.0 - xi) * (1.0 - eta) * model(X)


def grad(u, X):
    return torch.autograd.grad(u, X, torch.ones_like(u), create_graph=True)[0]


def residuals(model, X_int, X_bot, Bi):
    """PDE artığı (iç noktalar) ve Robin artığı (alt kenar)."""
    th = theta_hat(model, X_int)
    g = grad(th, X_int)
    th_xx = grad(g[:, :1], X_int)[:, :1]
    th_yy = grad(g[:, 1:2], X_int)[:, 1:2]
    r_pde = th_xx + th_yy

    tb = theta_hat(model, X_bot)
    tb_eta = grad(tb, X_bot)[:, 1:2]
    r_rob = tb_eta - Bi * tb
    return r_pde, r_rob


# ------------------------------------------------------------------ collocation
def collocation(n_int, n_bot, corner=False, seed=0, skip=0.0):
    """İç noktalar Sobol; alt kenar Sobol.
    corner=True: alt köşelere log-yoğun ek noktalar.
    skip=δ: köşeden δ mesafedeki Robin noktalarını kayıptan çıkar (köşe çelişkisi; README Adım 5)."""
    rng = np.random.default_rng(seed)
    X_int = qmc.Sobol(2, scramble=True, seed=seed).random(n_int)
    xb = qmc.Sobol(1, scramble=True, seed=seed + 1).random(n_bot)[:, 0]
    if corner:
        n_c = n_int // 4                       # her köşe için n_int/8
        r = np.exp(rng.uniform(np.log(1e-3), np.log(0.2), n_c))
        phi = rng.uniform(0, np.pi / 2, n_c)
        cx, cy = r * np.cos(phi), r * np.sin(phi)
        half = n_c // 2
        cx[half:] = 1.0 - cx[half:]            # yarısı sağ köşeye
        X_int = np.vstack([X_int, np.column_stack([cx, cy])])
        nb_c = n_bot // 2
        s = np.exp(rng.uniform(np.log(1e-3), np.log(0.2), nb_c))
        s[nb_c // 2:] = 1.0 - s[nb_c // 2:]
        xb = np.concatenate([xb, s])
    if skip > 0:
        xb = xb[(xb > skip) & (xb < 1.0 - skip)]
    X_bot = np.column_stack([xb, np.zeros_like(xb)])
    t = lambda a: torch.tensor(a, requires_grad=True)   # noqa: E731
    return t(X_int), t(X_bot)


# ------------------------------------------------------------------ training
def train(args):
    torch.manual_seed(args.seed)
    model = MLP(args.width, args.depth)
    X_int, X_bot = collocation(args.n_int, args.n_bot, args.corner, args.seed, args.skip)
    hist = {"it": [], "loss": [], "pde": [], "rob": [], "phase": []}

    def loss_fn():
        r_pde, r_rob = residuals(model, X_int, X_bot, args.Bi)
        l_pde, l_rob = (r_pde ** 2).mean(), (r_rob ** 2).mean()
        return l_pde + args.lam * l_rob, l_pde, l_rob

    def log(it, phase, tot, lp, lr_):
        hist["it"].append(it); hist["phase"].append(phase)
        hist["loss"].append(tot.item()); hist["pde"].append(lp.item()); hist["rob"].append(lr_.item())

    t0 = time.perf_counter()
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    sched = torch.optim.lr_scheduler.ExponentialLR(opt, gamma=(0.1) ** (1 / args.adam))   # lr: 1e-3 -> 1e-4
    for it in range(args.adam):
        opt.zero_grad()
        tot, lp, lr_ = loss_fn()
        tot.backward()
        opt.step(); sched.step()
        if it % 50 == 0 or it == args.adam - 1:
            log(it, 0, tot, lp, lr_)
        if it % 1000 == 0:
            print(f"Adam  {it:6d}  L = {tot.item():.3e}  (PDE {lp.item():.2e}, Robin {lr_.item():.2e})", flush=True)
    t_adam = time.perf_counter() - t0

    lbfgs = torch.optim.LBFGS(model.parameters(), lr=1.0, max_iter=args.lbfgs, max_eval=int(args.lbfgs * 1.25),
                              history_size=50, tolerance_grad=1e-11, tolerance_change=1e-14,
                              line_search_fn="strong_wolfe")
    k = [args.adam]

    def closure():
        lbfgs.zero_grad()
        tot, lp, lr_ = loss_fn()
        tot.backward()
        if k[0] % 25 == 0:
            log(k[0], 1, tot, lp, lr_)
        k[0] += 1
        return tot

    lbfgs.step(closure)
    tot, lp, lr_ = loss_fn()
    log(k[0], 1, tot, lp, lr_)
    t_total = time.perf_counter() - t0
    print(f"L-BFGS bitti: {k[0] - args.adam} değerlendirme, L = {tot.item():.3e}  ·  süre {t_total:.0f} s", flush=True)
    return model, hist, {"t_adam_s": round(t_adam, 1), "t_total_s": round(t_total, 1),
                         "n_int": int(X_int.shape[0]), "n_bot": int(X_bot.shape[0]),
                         "final_loss": tot.item(), "final_pde": lp.item(), "final_robin": lr_.item()}


# ------------------------------------------------------------------ evaluation
def predict(model, N):
    x = np.linspace(0, 1, N)
    X, Y = np.meshgrid(x, x)
    pts = torch.tensor(np.column_stack([X.ravel(), Y.ravel()]))
    with torch.no_grad():
        th = theta_hat(model, pts).numpy().reshape(N, N)
    return x, th


def reference(N, Bi):
    """Seri çözüm N×N ağda (önbellekli) — doğrulamada 'gerçek' çözüm."""
    f = HERE / "data" / f"series_N{N}_Bi{Bi:.4f}.npz"
    if f.exists():
        return np.load(f)["theta"]
    x = np.linspace(0, 1, N)
    th = analytical(x, x, Bi)
    f.parent.mkdir(exist_ok=True)
    np.savez_compressed(f, theta=th)
    return th


def evaluate(model, Bi, N=201):
    x, th = predict(model, N)
    ex = reference(N, Bi)
    _, _, fdm = solve_fdm(N, Bi)
    e = th - ex
    j, i = np.unravel_index(np.abs(e).argmax(), e.shape)
    xf = np.linspace(0, 1, 4001)
    with torch.no_grad():
        tb = theta_hat(model, torch.tensor(np.column_stack([xf, np.zeros_like(xf)]))).numpy()[:, 0]
    I_pinn = float(np.trapezoid(tb, xf))
    I_ex = float(np.trapezoid(analytical(xf, np.array([0.0]), Bi)[0], xf))
    h = Bi * K_SOLID / L
    Q = lambda I: h * L * (T_WALL - T_INF) * I   # noqa: E731
    interior = (slice(10, -10), slice(10, -10))  # köşe/kenar şeridi hariç (0.05 L)
    m = {
        "Bi": Bi,
        "rel_L2": float(np.linalg.norm(e) / np.linalg.norm(ex)),
        "max_err": float(np.abs(e).max()),
        "max_err_at": [round(float(x[i]), 3), round(float(x[j]), 3)],
        "rel_L2_interior": float(np.linalg.norm(e[interior]) / np.linalg.norm(ex[interior])),
        "rel_L2_fdm_same_grid": float(np.linalg.norm(fdm - ex) / np.linalg.norm(ex)),
        "theta_mid_bottom": float(th[0, N // 2]), "theta_mid_bottom_exact": float(ex[0, N // 2]),
        "T_mid_bottom_C": float(T_INF + (T_WALL - T_INF) * th[0, N // 2]),
        "int_theta_bottom": I_pinn, "int_theta_bottom_exact": I_ex,
        "Q_W_m": Q(I_pinn), "Q_W_m_exact": Q(I_ex), "Q_rel_err": abs(I_pinn - I_ex) / I_ex,
        "h_W_m2K": H_CONV,
    }
    return m, x, th, ex, fdm


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--Bi", type=float, default=BI_DEFAULT)
    ap.add_argument("--width", type=int, default=50)
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--n-int", type=int, default=4096)
    ap.add_argument("--n-bot", type=int, default=256)
    ap.add_argument("--corner", action="store_true", help="alt köşelerde sıklaştırılmış kolokasyon")
    ap.add_argument("--skip", type=float, default=0.0, help="köşeden bu mesafedeki Robin noktalarını dışla")
    ap.add_argument("--lam", type=float, default=1.0, help="Robin kaybının ağırlığı")
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--adam", type=int, default=6000)
    ap.add_argument("--lbfgs", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tag", default="uniform")
    args = ap.parse_args()

    out = HERE / "runs" / args.tag
    out.mkdir(parents=True, exist_ok=True)
    print(f"[{args.tag}] Bi = {args.Bi:.3f}, ağ {args.depth}×{args.width}, köşe sıklaştırma = {args.corner}, Robin dışlama δ = {args.skip}", flush=True)

    model, hist, info = train(args)
    metrics, x, th, ex, fdm = evaluate(model, args.Bi)
    metrics.update(info)
    metrics["config"] = vars(args)

    torch.save(model.state_dict(), out / "model.pt")
    np.savez_compressed(out / "history.npz", **{k: np.array(v) for k, v in hist.items()})
    np.savez_compressed(out / "prediction.npz", x=x, theta=th, theta_exact=ex, theta_fdm=fdm)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=1))
    print(json.dumps({k: (round(v, 6) if isinstance(v, float) else v) for k, v in metrics.items() if k != "config"}, indent=1))
