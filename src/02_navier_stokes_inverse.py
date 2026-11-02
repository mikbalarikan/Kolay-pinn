"""
DERS 2 — Ters problem (inverse / identification): Silindir arkası akıştan
Navier–Stokes katsayılarını KEŞFET ve basıncı HİÇ basınç verisi olmadan bul.

    u_t + λ1 (u u_x + v u_y) = -p_x + λ2 (u_xx + u_yy)
    v_t + λ1 (u v_x + v v_y) = -p_y + λ2 (v_xx + v_yy)

Gerçek değerler: λ1 = 1 (konvektif terim), λ2 = 1/Re = 0.01 (Re = 100).
Veri: Nektar++ spektral/hp DNS çözümünden 5000 rastgele (x, y, t, u, v) ölçümü.

Üç kritik fikir:
  1) Ağ (u, v) yerine (ψ, p) üretir. u = ψ_y, v = -ψ_x  =>  süreklilik
     denklemi u_x + v_y = 0 OTOMATİK sağlanır (kayıp terimine gerek yok).
  2) λ1, λ2 eğitilebilir parametrelerdir; ağ ağırlıklarıyla birlikte öğrenilir.
  3) Basınç p için hiç veri yok; yalnızca momentum denklemleri onu "zorlar".
     Bu yüzden p ancak bir sabit farkla (p + C) belirlenebilir.

Orijinal: main/continuous_time_identification (Navier-Stokes)/NavierStokes.py
Kullanım:  python src/02_navier_stokes_inverse.py [--adam 1000] [--lbfgs 15000] [--noise 0.01 --tag noisy]
"""
import argparse, json, os, sys, time
import numpy as np
import scipy.io
import torch

sys.path.insert(0, os.path.dirname(__file__))
from pinn_core import MLP, grad, grads, as_tensor

ap = argparse.ArgumentParser()
ap.add_argument("--adam", type=int, default=1000)    # orijinal: 200000 Adam (GPU). CPU için kısa tutuldu
ap.add_argument("--lbfgs", type=int, default=15000)  # orijinal: 50000 L-BFGS. Platoyu L-BFGS kırar
ap.add_argument("--noise", type=float, default=0.0)  # orijinal 2. deney: 0.01 (%1)
ap.add_argument("--tag", default="clean")
args = ap.parse_args()

torch.manual_seed(1234); np.random.seed(1234)
torch.set_num_threads(max(1, os.cpu_count() - 1))
ROOT = os.path.join(os.path.dirname(__file__), "..")

# ------------------------------------------------------------------ 1) VERİ
N_train = 5000
layers = [3, 20, 20, 20, 20, 20, 20, 20, 20, 2]     # (x,y,t) -> (ψ, p)

data = scipy.io.loadmat(f"{ROOT}/data/cylinder_nektar_wake.mat")
U_star = data["U_star"]   # N x 2 x T   (u, v)
P_star = data["p_star"]   # N x T
t_star = data["t"]        # T x 1
X_star = data["X_star"]   # N x 2       N=5000 uzay noktası, T=200 zaman adımı
N, T = X_star.shape[0], t_star.shape[0]

XX = np.tile(X_star[:, 0:1], (1, T)); YY = np.tile(X_star[:, 1:2], (1, T))
TT = np.tile(t_star, (1, N)).T
x, y, t = XX.flatten()[:, None], YY.flatten()[:, None], TT.flatten()[:, None]
u, v = U_star[:, 0, :].flatten()[:, None], U_star[:, 1, :].flatten()[:, None]

# 1 000 000 uzay-zaman noktasından yalnızca 5000'i (%0.5) eğitimde kullanılır
idx = np.random.choice(N * T, N_train, replace=False)
x_tr, y_tr, t_tr, u_tr, v_tr = x[idx], y[idx], t[idx], u[idx], v[idx]
if args.noise > 0:
    u_tr = u_tr + args.noise * np.std(u_tr) * np.random.randn(*u_tr.shape)
    v_tr = v_tr + args.noise * np.std(v_tr) * np.random.randn(*v_tr.shape)

Xtr = np.concatenate([x_tr, y_tr, t_tr], 1)
net = MLP(layers, Xtr.min(0), Xtr.max(0))
lambda_1 = torch.nn.Parameter(torch.zeros(1))   # bilinmeyen fizik parametreleri
lambda_2 = torch.nn.Parameter(torch.zeros(1))
params = list(net.parameters()) + [lambda_1, lambda_2]

xt, yt, tt = as_tensor(x_tr, True), as_tensor(y_tr, True), as_tensor(t_tr, True)
ut, vt = as_tensor(u_tr), as_tensor(v_tr)


# ------------------------------------------------------------------ 2) FİZİK
def net_NS(x, y, t):
    psi_p = net(torch.cat([x, y, t], 1))
    psi, p = psi_p[:, 0:1], psi_p[:, 1:2]

    psi_x, psi_y = grads(psi, x, y)
    u = psi_y                 # u =  ∂ψ/∂y
    v = -psi_x                # v = -∂ψ/∂x   -> ∇·u = ψ_yx - ψ_xy = 0  (süreklilik bedava!)

    u_x, u_y, u_t = grads(u, x, y, t)       # birinci türevler
    v_x, v_y, v_t = grads(v, x, y, t)
    u_xx, u_yy = grad(u_x, x), grad(u_y, y)  # ikinci türevler (viskoz terim)
    v_xx, v_yy = grad(v_x, x), grad(v_y, y)
    p_x, p_y = grads(p, x, y)                # basınç gradyanı

    f_u = u_t + lambda_1 * (u * u_x + v * u_y) + p_x - lambda_2 * (u_xx + u_yy)
    f_v = v_t + lambda_1 * (u * v_x + v * v_y) + p_y - lambda_2 * (v_xx + v_yy)
    return u, v, p, f_u, f_v


def loss_fn():
    u_p, v_p, _, f_u, f_v = net_NS(xt, yt, tt)
    # Dikkat: orijinal kod MEAN değil SUM kullanır (reduce_sum)
    l_data = torch.sum((ut - u_p) ** 2) + torch.sum((vt - v_p) ** 2)
    l_phys = torch.sum(f_u ** 2) + torch.sum(f_v ** 2)
    return l_data + l_phys, l_data, l_phys


# ------------------------------------------------------------------ 3) EĞİTİM
hist = {k: [] for k in ["it", "loss", "data", "phys", "l1", "l2", "phase"]}
state = {"it": 0}
t0 = time.time()


def log(l, a, b, phase):
    i = state["it"]
    if i % 50 == 0:
        for k, val in zip(hist, [i, l, a, b, lambda_1.item(), lambda_2.item(), phase]):
            hist[k].append(val)
    if i % 500 == 0:
        print(f"[{phase}] it {i:6d} loss {l:.3e} data {a:.3e} phys {b:.3e} "
              f"λ1 {lambda_1.item():.4f} λ2 {lambda_2.item():.5f} ({time.time()-t0:.0f}s)", flush=True)
    state["it"] += 1


opt = torch.optim.Adam(params, lr=1e-3)
sched = torch.optim.lr_scheduler.StepLR(opt, step_size=max(1, args.adam // 3), gamma=0.5)
for _ in range(args.adam):
    opt.zero_grad(); l, a, b = loss_fn(); l.backward(); opt.step(); sched.step()
    log(l.item(), a.item(), b.item(), "adam")

if args.lbfgs > 0:
    lbfgs = torch.optim.LBFGS(params, lr=1.0, max_iter=args.lbfgs, max_eval=int(args.lbfgs * 1.25),
                              history_size=50, tolerance_grad=1e-9, tolerance_change=1e-12,
                              line_search_fn="strong_wolfe")

    def closure():
        lbfgs.zero_grad(); l, a, b = loss_fn(); l.backward()
        log(l.item(), a.item(), b.item(), "lbfgs")
        return l

    lbfgs.step(closure)
elapsed = time.time() - t0

# ------------------------------------------------------------------ 4) TEST (t = 10.0, snap 100)
snap = 100
xs, ys = as_tensor(X_star[:, 0:1], True), as_tensor(X_star[:, 1:2], True)
ts = as_tensor(TT[:, snap:snap + 1], True)
u_p, v_p, p_p, _, _ = net_NS(xs, ys, ts)
u_p, v_p, p_p = (z.detach().numpy() for z in (u_p, v_p, p_p))
u_e, v_e, p_e = U_star[:, 0, snap:snap + 1], U_star[:, 1, snap:snap + 1], P_star[:, snap:snap + 1]

rel = lambda a, b: float(np.linalg.norm(a - b) / np.linalg.norm(a))
p_shift = p_p - p_p.mean() + p_e.mean()    # basınç yalnızca bir sabite kadar belirli
res = {
    "tag": args.tag, "noise": args.noise, "time_s": elapsed,
    "lambda_1": lambda_1.item(), "lambda_2": lambda_2.item(),
    "err_l1_pct": abs(lambda_1.item() - 1.0) * 100,
    "err_l2_pct": abs(lambda_2.item() - 0.01) / 0.01 * 100,
    "err_u": rel(u_e, u_p), "err_v": rel(v_e, v_p),
    "err_p_raw": rel(p_e, p_p), "err_p_shifted": rel(p_e, p_shift),
    "p_offset": float(p_e.mean() - p_p.mean()),
}
print(json.dumps(res, indent=2))
json.dump({"hist": hist, "res": res}, open(f"{ROOT}/results/ns_{args.tag}_log.json", "w"))
np.savez(f"{ROOT}/results/ns_{args.tag}.npz", X_star=X_star, u_p=u_p, v_p=v_p, p_p=p_p,
         u_e=u_e, v_e=v_e, p_e=p_e, x_tr=x_tr, y_tr=y_tr, t_tr=t_tr)
torch.save({"net": net.state_dict(), "l1": lambda_1.data, "l2": lambda_2.data},
           f"{ROOT}/results/ns_{args.tag}.pt")
