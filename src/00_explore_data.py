"""
DERS 0 — Veriyi tanı. Model kurmadan önce CFD verisine bak.

cylinder_nektar_wake.mat : Re=100'de silindir arkası akış (Kármán girdap caddesi),
Nektar++ ile yüksek doğrulukla çözülmüş; PINN eğitimi için silindirin
ARKASINDAKİ dikdörtgen bölge [1,8] x [-2,2] kesilmiş.
"""
import os
import numpy as np
import scipy.io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from scipy.interpolate import griddata

ROOT = os.path.join(os.path.dirname(__file__), "..")
FIG = f"{ROOT}/figures"
plt.rcParams.update({"font.size": 10, "figure.dpi": 130})

d = scipy.io.loadmat(f"{ROOT}/data/cylinder_nektar_wake.mat")
X, U, P, t = d["X_star"], d["U_star"], d["p_star"], d["t"].flatten()
print("X_star", X.shape, " U_star", U.shape, " p_star", P.shape, " t", t.shape)

nx, ny = 300, 170
gx, gy = np.meshgrid(np.linspace(1, 8, nx), np.linspace(-2, 2, ny))
grid = lambda f: griddata(X, f, (gx, gy), method="cubic")

# --- Şekil 1: Bölge + u, v, p, vorticity
snap = 100
u, v, p = grid(U[:, 0, snap]), grid(U[:, 1, snap]), grid(P[:, snap])
dx, dy = gx[0, 1] - gx[0, 0], gy[1, 0] - gy[0, 0]
w = np.gradient(v, dx, axis=1) - np.gradient(u, dy, axis=0)   # ω = v_x - u_y

fig, axs = plt.subplots(2, 2, figsize=(11, 6.2), constrained_layout=True)
for ax, f, name, cm in zip(axs.flat, [u, v, p, w],
                           ["u (x-hızı)", "v (y-hızı)", "p (basınç) — EĞİTİMDE YOK", "ω = v_x − u_y (girdaplık)"],
                           ["viridis", "RdBu_r", "magma", "RdBu_r"]):
    lim = np.nanmax(np.abs(f)) if cm == "RdBu_r" else None
    im = ax.pcolormesh(gx, gy, f, cmap=cm, shading="auto",
                       vmin=-lim if lim else None, vmax=lim)
    ax.set_title(f"{name}   t = {t[snap]:.1f}"); ax.set_aspect("equal")
    fig.colorbar(im, ax=ax, shrink=0.85)
fig.suptitle("Silindir arkası akış (Re=100) — Nektar++ DNS verisi", fontsize=12)
fig.savefig(f"{FIG}/00_wake_fields.png"); plt.close(fig)

# --- Şekil 2: Silindir + kesilen eğitim bölgesi şeması (vorticity ile)
fig, ax = plt.subplots(figsize=(10, 4), constrained_layout=True)
ax.pcolormesh(gx, gy, w, cmap="RdBu_r", vmin=-3, vmax=3, shading="auto")
ax.add_patch(Circle((0, 0), 0.5, color="0.3"))
ax.add_patch(Rectangle((1, -2), 7, 4, fill=False, ec="k", lw=2, ls="--"))
ax.annotate("silindir\n(D = 1)", (0, 0), (-1.3, 1.4), arrowprops=dict(arrowstyle="->"))
ax.annotate("", (0.6, -1.5), (-1.8, -1.5), arrowprops=dict(arrowstyle="->", lw=2))
ax.text(-1.8, -1.85, "U∞ = 1 giriş akışı")
ax.text(4.5, 2.15, "PINN eğitim bölgesi [1,8]×[−2,2]", ha="center")
idx = np.random.default_rng(0).choice(X.shape[0], 400, replace=False)
ax.scatter(X[idx, 0], X[idx, 1], s=3, c="k", alpha=0.5, label="ölçüm noktaları (örnek)")
ax.set_xlim(-2, 8.3); ax.set_ylim(-2.4, 2.6); ax.set_aspect("equal"); ax.legend(loc="lower right")
ax.set_title("Problem geometrisi: Kármán girdap caddesi")
fig.savefig(f"{FIG}/00_geometry.png"); plt.close(fig)

# --- Şekil 3: Bir noktada zaman sinyali -> periyodik girdap kopması
i = np.argmin(np.hypot(X[:, 0] - 3, X[:, 1] - 0.0))
fig, ax = plt.subplots(figsize=(9, 2.8), constrained_layout=True)
ax.plot(t, U[i, 0], label="u"); ax.plot(t, U[i, 1], label="v"); ax.plot(t, P[i], label="p")
ax.set_xlabel("t"); ax.set_title(f"(x, y) = ({X[i,0]:.2f}, {X[i,1]:.2f}) noktasında zaman serisi — periyodik girdap kopması")
ax.legend(ncol=3); ax.grid(alpha=0.3)
fig.savefig(f"{FIG}/00_timeseries.png"); plt.close(fig)

# --- Animasyon karesi (GIF): vorticity zaman içinde
try:
    from matplotlib.animation import FuncAnimation, PillowWriter
    fig, ax = plt.subplots(figsize=(6, 3.4), dpi=70, constrained_layout=True)
    def vort(k):
        uu, vv = grid(U[:, 0, k]), grid(U[:, 1, k])
        return np.gradient(vv, dx, axis=1) - np.gradient(uu, dy, axis=0)
    im = ax.pcolormesh(gx, gy, vort(0), cmap="RdBu_r", vmin=-3, vmax=3, shading="auto")
    ax.set_aspect("equal"); ttl = ax.set_title("")
    def upd(k):
        im.set_array(vort(k).ravel()); ttl.set_text(f"girdaplık ω, t = {t[k]:.1f}"); return im, ttl
    FuncAnimation(fig, upd, frames=range(0, 200, 5)).save(f"{FIG}/00_vorticity.gif", writer=PillowWriter(fps=8), dpi=70)
    plt.close(fig)
except Exception as e:
    print("GIF atlandı:", e)
print("Şekiller ->", FIG)
