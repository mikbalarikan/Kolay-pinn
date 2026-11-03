"""
Plots for the FDM reference solution + grid-convergence check.
Run after (or instead of) fdm_solver.py:  python plot_reference.py
Writes PNGs to ./figures
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from fdm_solver import BI_DEFAULT, analytical, bottom_heat_rate, solve_fdm, to_celsius

HERE = Path(__file__).parent
FIG = HERE / "figures"
FIG.mkdir(exist_ok=True)

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#e3e3e3", "grid.linewidth": 0.6})
INK = "#333333"
C1, C2 = "#2a6fdb", "#e0731f"   # FDM, analytical

N = 101
x, y, th = solve_fdm(N)
th_ex = analytical(x, y)
X, Y = np.meshgrid(x, y)

# 1) temperature field [C]
fig, ax = plt.subplots(figsize=(5.2, 4.4))
cf = ax.contourf(X, Y, to_celsius(th), levels=30, cmap="Oranges")
cs = ax.contour(X, Y, to_celsius(th), levels=[40, 50, 60, 65, 68], colors=INK, linewidths=0.6)
ax.clabel(cs, fmt="%.0f °C", fontsize=8)
fig.colorbar(cf, ax=ax, label="T [°C]")
ax.set(xlabel="x / L", ylabel="y / L", aspect="equal",
       title=f"FDM reference, N={N}, Bi={BI_DEFAULT:.2f}")
ax.grid(False)
fig.tight_layout(); fig.savefig(FIG / "temperature_field.png", dpi=160); plt.close(fig)

# 2) bottom surface temperature
fig, ax = plt.subplots(figsize=(5.6, 3.4))
ax.plot(x, to_celsius(th[0]), color=C1, lw=2, label="FDM")
ax.plot(x[::5], to_celsius(th_ex[0, ::5]), "o", ms=4, mfc="none", color=C2, label="Analytical series")
ax.set(xlabel="x / L", ylabel="T(x, 0) [°C]", title="Cooled (bottom) surface temperature")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(FIG / "bottom_profile.png", dpi=160); plt.close(fig)

# 3) error map (diverging, centred on 0)
err = th - th_ex
lim = np.abs(err).max()
fig, ax = plt.subplots(figsize=(5.2, 4.4))
cf = ax.contourf(X, Y, err, levels=np.linspace(-lim, lim, 31), cmap="RdBu_r")
fig.colorbar(cf, ax=ax, label="θ_FDM − θ_exact", format="%.0e", ticks=np.linspace(-lim, lim, 5))
ax.set(xlabel="x / L", ylabel="y / L", aspect="equal", title="FDM error (peaks at bottom corners)")
ax.grid(False)
fig.tight_layout(); fig.savefig(FIG / "error_map.png", dpi=160); plt.close(fig)

# 4) grid convergence
Ns = np.array([26, 51, 101, 201])
l2, linf = [], []
for n in Ns:
    xn, yn, tn = solve_fdm(n)
    en = analytical(xn, yn)
    l2.append(np.linalg.norm(tn - en) / np.linalg.norm(en))
    linf.append(np.abs(tn - en).max())
h = 1.0 / (Ns - 1)
fig, ax = plt.subplots(figsize=(5.2, 3.8))
ax.loglog(h, l2, "o-", color=C1, lw=2, ms=6, label="relative L2")
ax.loglog(h, linf, "s-", color=C2, lw=2, ms=6, label="max |error|")
ax.loglog(h, l2[0] * (h / h[0]) ** 2, ":", color="#888888", lw=1, label="slope 2")
ax.loglog(h, linf[0] * (h / h[0]), "--", color="#888888", lw=1, label="slope 1")
ax.set(xlabel="grid spacing Δ", ylabel="error vs analytical", title="Grid convergence")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(FIG / "grid_convergence.png", dpi=160); plt.close(fig)

for n, a, b in zip(Ns, l2, linf):
    print(f"N={n:4d}  L2={a:.2e}  Linf={b:.2e}")
print(f"Q' = {bottom_heat_rate(x, th[0])[0]:.0f} W/m")
print(f"figures -> {FIG}")
