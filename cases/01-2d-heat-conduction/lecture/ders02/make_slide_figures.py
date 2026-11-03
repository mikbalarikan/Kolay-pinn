"""
Ders 02 slayt görselleri (projeksiyon boyutu, Türkişi paleti).
Önce eğitim:  python pinn_forward.py --tag uniform ; python pinn_forward.py --corner --tag corner
Çalıştırma:   python lecture/ders02/make_slide_figures.py   ->  lecture/ders02/assets/*.png
"""

import json
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

HERE = Path(__file__).resolve().parent
CASE = HERE.parents[1]
ROOT = CASE.parents[1]
sys.path.insert(0, str(CASE))
sys.path.insert(0, str(ROOT))

from pinn_forward import collocation  # noqa: E402
from kolay_pinn.style import C, INK, MUTED, cmap_error, cmap_thermal, use_slide_style  # noqa: E402

use_slide_style()
OUT = HERE / "assets"
OUT.mkdir(exist_ok=True)
DPI = 220
UNI, COR = C["plan"], C["parca_mandalina"]


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=DPI)
    plt.close(fig)


# brand marks + mascot: reuse Ders 01 assets
for f in ("ti_light.png", "ti_dark.png", "maskot_normal.png", "maskot_mutlu.png"):
    shutil.copy(CASE / "lecture" / "assets" / f, OUT / f)

x = np.linspace(0, 1, 201)
X, Y = np.meshgrid(x, x)

# 1 — distance function d = ξ(1−ξ)(1−η) -------------------------------------------
fig, ax = plt.subplots(figsize=(5.4, 4.8))
d = X * (1 - X) * (1 - Y)
cf = ax.contourf(X, Y, d, levels=20, cmap=cmap_thermal)
for (x0, y0, x1, y1) in [(0, 0, 0, 1), (1, 0, 1, 1), (0, 1, 1, 1)]:
    ax.plot([x0, x1], [y0, y1], color=C["celik_mavisi"], lw=6, solid_capstyle="butt", clip_on=False)
ax.plot([0, 1], [0, 0], color=UNI, lw=6, solid_capstyle="butt", clip_on=False)
ax.text(0.5, 1.06, r"$d = 0 \;\Rightarrow\; \hat{\theta} = 1$", ha="center", fontsize=16)
ax.text(0.5, -0.27, "alt kenar serbest: Robin kaybı öğretir", ha="center", fontsize=13)
ax.set(aspect="equal", xticks=[0, 0.5, 1], yticks=[0, 0.5, 1], xlabel="ξ", ylabel="η")
cb = fig.colorbar(cf, ax=ax, fraction=0.046, pad=0.04)
cb.set_label("d(ξ, η)")
fig.tight_layout(pad=1.0)
save(fig, "01_distance")

# 2 — activations and their second derivatives -------------------------------------
z = np.linspace(-3, 3, 600)
fig, axs = plt.subplots(1, 2, figsize=(9.6, 3.9))
axs[0].plot(z, np.tanh(z), color=UNI, lw=2.6, label="tanh")
axs[0].plot(z, np.maximum(0, z), color=COR, lw=2.6, label="ReLU")
axs[0].set(title="σ(z)", xlabel="z", ylim=(-1.2, 3.1))
axs[0].legend(loc="upper left")
t = np.tanh(z)
axs[1].plot(z, -2 * t * (1 - t ** 2), color=UNI, lw=2.6, label="tanh″")
axs[1].plot(z, np.zeros_like(z), color=COR, lw=2.6, label="ReLU″ = 0")
axs[1].set(title="σ″(z)", xlabel="z", ylim=(-0.9, 0.9))
axs[1].legend(loc="upper right")
fig.tight_layout(pad=0.6)
save(fig, "02_activations")

# 3 — collocation clouds: three strategies -----------------------------------------
STRAT = [("uniform", dict(corner=False, skip=0.0), UNI, "düzgün Sobol"),
         ("corner", dict(corner=True, skip=0.0), COR, "köşe sıklaştırma"),
         ("skip", dict(corner=False, skip=0.02), C["lila"], "köşe dışlama, δ = 0.02")]
fig, axs = plt.subplots(1, 3, figsize=(12.4, 4.6))
for ax, (tag, kw, col, title) in zip(axs, STRAT):
    Xi, Xb = collocation(4096, 256, seed=0, **kw)
    Xi, Xb = Xi.detach().numpy(), Xb.detach().numpy()
    ax.scatter(Xi[:, 0], Xi[:, 1], s=3.0, color=col, alpha=0.85, linewidths=0)
    ax.scatter(Xb[:, 0], Xb[:, 1] - 0.03, s=9, color=INK, linewidths=0, clip_on=False)
    if kw["skip"]:
        for x0 in (0.0, 1.0 - kw["skip"]):
            ax.axvspan(x0, x0 + kw["skip"], ymin=0, ymax=0.08, color=C["hata"], alpha=0.6, lw=0)
    ax.set(aspect="equal", xlim=(0, 1), ylim=(-0.05, 1), xticks=[0, 0.5, 1], yticks=[0, 0.5, 1], xlabel="ξ",
           title=f"{title}\n{len(Xi)} iç · {len(Xb)} Robin")
    for sp_ in ("top", "right"):
        ax.spines[sp_].set_visible(True)
axs[0].set_ylabel("η")
fig.tight_layout(pad=0.6)
save(fig, "03_collocation")

# ---- run-dependent figures ----------------------------------------------------------
RUNS = [(t, col, lab) for t, _, col, lab in STRAT]
R = {}
for tag, _, _ in RUNS:
    d_ = CASE / "runs" / tag
    R[tag] = {"m": json.loads((d_ / "metrics.json").read_text()), "h": np.load(d_ / "history.npz"),
              "p": np.load(d_ / "prediction.npz")}
xs = R["uniform"]["p"]["x"]
XX, YY = np.meshgrid(xs, xs)
ex = R["uniform"]["p"]["theta_exact"]
fdm = R["uniform"]["p"]["theta_fdm"]

# 4 — loss history
fig, ax = plt.subplots(figsize=(7.6, 4.3))
h = R["uniform"]["h"]
n_adam = h["it"][h["phase"] == 0].max()
ax.axvspan(n_adam, max(R[t]["h"]["it"].max() for t in R) * 1.02, color=C["krom"], zorder=0)
for tag, col, lab in RUNS:
    hh = R[tag]["h"]
    ax.semilogy(hh["it"], hh["loss"], color=col, lw=1.8, label=lab)
ax.text(n_adam * 0.5, 3e2, "Adam", ha="center", color=MUTED, fontsize=14)
ax.text(n_adam + 900, 3e2, "L-BFGS", ha="left", color=MUTED, fontsize=14)
ax.set(xlabel="iterasyon", ylabel="toplam kayıp", ylim=(None, 2e3))
ax.legend(loc="lower left", fontsize=12)
fig.tight_layout(pad=0.5)
save(fig, "04_loss")

# 5 — PINN temperature field (uniform)
Tp = 20 + 50 * R["uniform"]["p"]["theta"]
fig, ax = plt.subplots(figsize=(5.6, 4.9))
cf = ax.contourf(XX, YY, Tp, levels=np.linspace(36, 70, 35), cmap=cmap_thermal)
N = len(xs)
for lv in [40, 45, 50, 55, 60, 65, 68]:
    cs = ax.contour(XX, YY, Tp, levels=[lv], colors=[INK if lv < 52 else C["krom"]], linewidths=1.0)
    ax.clabel(cs, fmt="%d", fontsize=11, manual=[(0.5, float(np.interp(lv, Tp[:, N // 2], xs)))])
ax.set(aspect="equal", xticks=[0, 0.5, 1], yticks=[0, 0.5, 1], xlabel="x/L", ylabel="y/L")
for sp_ in ("top", "right"):
    ax.spines[sp_].set_visible(True)
cb = fig.colorbar(cf, ax=ax, ticks=[40, 50, 60, 70], fraction=0.046, pad=0.04)
cb.set_label("T (°C)")
fig.tight_layout(pad=1.0)
save(fig, "05_pinn_field")

# 6 — error maps, three runs
fig, axs = plt.subplots(1, 3, figsize=(13.0, 4.6))
levels = np.arange(-6, -0.99, 0.5)
for ax, (tag, col, lab) in zip(axs, RUNS):
    e = np.abs(R[tag]["p"]["theta"] - ex)
    cf = ax.contourf(XX, YY, np.log10(np.maximum(e, 1e-8)), levels=levels, cmap=cmap_error, extend="both")
    m = R[tag]["m"]
    ax.set(aspect="equal", xticks=[0, 0.5, 1], yticks=[0, 0.5, 1], xlabel="x/L",
           title=f"{lab}\nL₂ {m['rel_L2']:.1e} · maks {m['max_err']:.1e}")
    for sp_ in ("top", "right"):
        ax.spines[sp_].set_visible(True)
    for cx in (0.0, 1.0):
        ax.add_patch(Circle((cx, 0.0), 0.09, fill=False, ec=MUTED, lw=2.0, ls="--", clip_on=False))
    ax.plot([0.1, 0.9], [-0.2, -0.2], color=col, lw=5, transform=ax.transAxes, clip_on=False, solid_capstyle="butt")
axs[0].set_ylabel("y/L")
fig.subplots_adjust(left=0.05, right=0.9, bottom=0.18, top=0.86, wspace=0.18)
cax = fig.add_axes([0.915, 0.2, 0.015, 0.6])
cb = fig.colorbar(cf, cax=cax, ticks=[-6, -4, -2])
cb.set_label("log₁₀ |hata|")
save(fig, "06_error_maps")

# 7 — error along bottom surface
fig, ax = plt.subplots(figsize=(7.6, 4.3))
for tag, col, lab in RUNS:
    ax.semilogy(xs[1:-1], np.abs(R[tag]["p"]["theta"][0] - ex[0])[1:-1], color=col, lw=2.0, label=lab)
ax.semilogy(xs[1:-1], np.abs(fdm[0] - ex[0])[1:-1], color=MUTED, lw=1.6, ls="--", label="FDM, N = 201")
ax.set(xlabel="x/L", ylabel="|θ − θ_seri|  alt yüzey", xlim=(0, 1), ylim=(1e-7, 1))
ax.legend(loc="lower center", ncol=2, fontsize=11)
fig.tight_layout(pad=0.5)
save(fig, "07_bottom_error")

# 8 — Robin residual along the bottom: where the loss floor comes from
import torch  # noqa: E402
from pinn_forward import MLP, grad, theta_hat  # noqa: E402
torch.set_default_dtype(torch.float64)
Bi = R["uniform"]["m"]["Bi"]
xb = np.linspace(0, 1, 20001)
fig, ax = plt.subplots(figsize=(7.6, 4.2))
shares = {}
for tag, col, lab in RUNS:
    net = MLP()
    net.load_state_dict(torch.load(CASE / "runs" / tag / "model.pt"))
    Xb = torch.tensor(np.column_stack([xb, np.zeros_like(xb)]), requires_grad=True)
    tb = theta_hat(net, Xb)
    r = (grad(tb, Xb)[:, 1:2] - Bi * tb).detach().numpy()[:, 0]
    edge = (xb < 0.01) | (xb > 0.99)
    shares[tag] = float((r[edge] ** 2).sum() / (r ** 2).sum())
    ax.semilogy(xb, np.abs(r) + 1e-12, color=col, lw=1.5, label=lab)
ax.axvspan(0, 0.01, color=C["krom"], zorder=0)
ax.axvspan(0.99, 1, color=C["krom"], zorder=0)
ax.axhline(Bi, color=MUTED, lw=1.2, ls="--")
ax.text(0.5, Bi * 1.35, rf"$|r| = \mathrm{{Bi}} = {Bi:.2f}$   (köşede $\hat\theta = 1,\ \partial\hat\theta/\partial\eta = 0$)", ha="center", fontsize=12, color=INK)
ax.set(xlabel="ξ", ylabel=r"$|\partial\hat\theta/\partial\eta - \mathrm{Bi}\,\hat\theta|$", xlim=(0, 1), ylim=(1e-4, 30))
ax.legend(loc="lower center", ncol=3, fontsize=11)
fig.tight_layout(pad=0.5)
save(fig, "08_robin_residual")
(OUT / "robin_share.json").write_text(json.dumps(shares, indent=1))
print("Robin kaybındaki köşe payı (kenarın %2'si):", shares)
print(sorted(p.name for p in OUT.glob("*.png")))
