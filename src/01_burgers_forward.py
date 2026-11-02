"""
DERS 1 — İleri problem (forward / inference): Burgers denklemini PINN ile çöz.

    u_t + u u_x - nu u_xx = 0 ,   x in [-1, 1], t in [0, 1],  nu = 0.01/pi
    u(0, x) = -sin(pi x)         (başlangıç koşulu)
    u(t, -1) = u(t, 1) = 0        (sınır koşulları)

Burgers, Navier–Stokes'un 1 boyutlu "oyuncak" versiyonudur: adveksiyon (u u_x)
ve viskoz difüzyon (nu u_xx) aynı anda var; t≈0.4'ten sonra x=0'da keskin bir
şok (shock) oluşur. CFD'deki zorlukların özü burada.

Orijinal: appendix/continuous_time_inference (Burgers)/Burgers.py
"""
import json, time, sys, os
import numpy as np
import scipy.io
import torch

sys.path.insert(0, os.path.dirname(__file__))
from pinn_core import MLP, grad, as_tensor

torch.manual_seed(1234); np.random.seed(1234)
ROOT = os.path.join(os.path.dirname(__file__), "..")

# ------------------------------------------------------------------ 1) VERİ
nu = 0.01 / np.pi
N_u, N_f = 100, 10000                       # 100 sınır/başlangıç noktası, 10k fizik noktası
layers = [2, 20, 20, 20, 20, 20, 20, 20, 20, 1]   # (x,t) -> u

data = scipy.io.loadmat(f"{ROOT}/data/burgers_shock.mat")
t = data["t"].flatten()[:, None]            # 100 x 1
x = data["x"].flatten()[:, None]            # 256 x 1
Exact = np.real(data["usol"]).T             # 100 x 256  (yalnızca TEST için!)
X, T = np.meshgrid(x, t)
X_star = np.hstack((X.flatten()[:, None], T.flatten()[:, None]))
u_star = Exact.flatten()[:, None]
lb, ub = X_star.min(0), X_star.max(0)

# Başlangıç (t=0) + iki sınır (x=-1, x=1) -> etiketli noktalar
xx1 = np.hstack((X[0:1, :].T, T[0:1, :].T)); uu1 = Exact[0:1, :].T
xx2 = np.hstack((X[:, 0:1], T[:, 0:1]));     uu2 = Exact[:, 0:1]
xx3 = np.hstack((X[:, -1:], T[:, -1:]));     uu3 = Exact[:, -1:]
X_u_all = np.vstack([xx1, xx2, xx3]); u_all = np.vstack([uu1, uu2, uu3])
idx = np.random.choice(X_u_all.shape[0], N_u, replace=False)
X_u_train, u_train = X_u_all[idx], u_all[idx]

# Kollokasyon (fizik) noktaları: alanın içine rastgele serpiştirilir, ETİKET YOK
# (orijinal Latin Hypercube kullanır: pyDOE.lhs; burada eşdeğer düzgün rastgele örnek)
X_f_train = lb + (ub - lb) * np.random.rand(N_f, 2)
X_f_train = np.vstack((X_f_train, X_u_train))

# ------------------------------------------------------------------ 2) MODEL
net = MLP(layers, lb, ub)
xu, tu = as_tensor(X_u_train[:, 0:1]), as_tensor(X_u_train[:, 1:2])
uu = as_tensor(u_train)
xf = as_tensor(X_f_train[:, 0:1], True)    # requires_grad -> autograd ile türev alacağız
tf_ = as_tensor(X_f_train[:, 1:2], True)


def net_u(x, t):
    return net(torch.cat([x, t], 1))


def net_f(x, t):
    """PDE kalıntısı (residual). Ağ denklemi tam sağlıyorsa f = 0 olur."""
    u = net_u(x, t)
    u_t = grad(u, t)
    u_x = grad(u, x)
    u_xx = grad(u_x, x)
    return u_t + u * u_x - nu * u_xx


def loss_fn():
    mse_u = torch.mean((uu - net_u(xu, tu)) ** 2)     # veri kaybı (BC + IC)
    mse_f = torch.mean(net_f(xf, tf_) ** 2)           # fizik kaybı
    return mse_u + mse_f, mse_u, mse_f


# ------------------------------------------------------------------ 3) EĞİTİM
hist = {"it": [], "loss": [], "mse_u": [], "mse_f": [], "phase": []}
it = 0
t0 = time.time()


def log(l, a, b, phase):
    global it
    if it % 50 == 0:
        hist["it"].append(it); hist["loss"].append(l); hist["mse_u"].append(a)
        hist["mse_f"].append(b); hist["phase"].append(phase)
    if it % 500 == 0:
        print(f"[{phase}] it {it:6d}  loss {l:.3e}  mse_u {a:.3e}  mse_f {b:.3e}  ({time.time()-t0:.0f}s)", flush=True)
    it += 1


# 3a) Adam ile ısınma (orijinal Burgers betiği doğrudan L-BFGS kullanır; kısa Adam
#     ısınması PyTorch'ta L-BFGS'i daha kararlı başlatır)
opt = torch.optim.Adam(net.parameters(), lr=1e-3)
for _ in range(2000):
    opt.zero_grad(); l, a, b = loss_fn(); l.backward(); opt.step()
    log(l.item(), a.item(), b.item(), "adam")

# 3b) L-BFGS: PINN'lerde klasik "ince ayar" optimizasyonu (ikinci-derece yaklaşık)
lbfgs = torch.optim.LBFGS(net.parameters(), lr=1.0, max_iter=8000, max_eval=10000,
                          history_size=50, tolerance_grad=1e-9, tolerance_change=1e-12,
                          line_search_fn="strong_wolfe")


def closure():
    lbfgs.zero_grad(); l, a, b = loss_fn(); l.backward()
    log(l.item(), a.item(), b.item(), "lbfgs")
    return l


lbfgs.step(closure)
elapsed = time.time() - t0

# ------------------------------------------------------------------ 4) TEST
xs = as_tensor(X_star[:, 0:1], True); ts = as_tensor(X_star[:, 1:2], True)
u_pred = net_u(xs, ts).detach().numpy()
f_pred = net_f(xs, ts).detach().numpy()
err = np.linalg.norm(u_star - u_pred) / np.linalg.norm(u_star)
print(f"Eğitim süresi: {elapsed:.1f}s   Göreli L2 hata u: {err:.3e}")

np.savez(f"{ROOT}/results/burgers.npz", x=x, t=t, Exact=Exact,
         U_pred=u_pred.reshape(Exact.shape), F_pred=f_pred.reshape(Exact.shape),
         X_u_train=X_u_train, X_f_train=X_f_train[:N_f])
json.dump({"hist": hist, "error_u": float(err), "time_s": elapsed},
          open(f"{ROOT}/results/burgers_log.json", "w"))
