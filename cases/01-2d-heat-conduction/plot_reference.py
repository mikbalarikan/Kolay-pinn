"""
Fig. 1 — FDM referans çözümü ve analitik doğrulama (Nature biçimi, Türkişi paleti).

Çıktılar:
  figures/fig01_fdm_reference.{pdf,svg,png}   (183 mm çift sütun, vektör + önizleme)
  data/summary.json                           (README ve PDF raporu bu sayıları okur)

Çalıştırma:  python plot_reference.py
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import LogLocator, NullFormatter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from fdm_solver import (BI_DEFAULT, H_CONV, K_SOLID, L, NU, RE, T_INF, T_WALL,  # noqa: E402
                        analytical, bottom_heat_rate, solve_fdm, to_celsius)
from kolay_pinn.style import (C, INK, MM, MUTED, cmap_error, cmap_thermal,  # noqa: E402
                              panel_letter, save_figure, use_style)

use_style()
S1, S2 = C["plan"], C["lila"]          # seri 1: FDM, seri 2: analitik / ikinci ölçüt

# ---------------------------------------------------------------- data
N = 101
x, y, th = solve_fdm(N)
th_ex = analytical(x, y)
X, Y = np.meshgrid(x, y)
T, T_ex = to_celsius(th), to_celsius(th_ex)

Ns = np.array([26, 51, 101, 201])
l2, linf, qs = [], [], []
for n in Ns:
    xn, yn, tn = solve_fdm(n)
    en = analytical(xn, yn)
    l2.append(np.linalg.norm(tn - en) / np.linalg.norm(en))
    linf.append(np.abs(tn - en).max())
    qs.append(bottom_heat_rate(xn, tn[0])[1])
l2, linf = np.array(l2), np.array(linf)
dx = 1.0 / (Ns - 1)
order_l2 = np.polyfit(np.log(dx), np.log(l2), 1)[0]
order_linf = np.polyfit(np.log(dx), np.log(linf), 1)[0]

x_fine = np.linspace(0, 1, 2001)
q_exact = np.trapezoid(analytical(x_fine, np.array([0.0]))[0], x_fine)
Q_fdm, q_fdm = bottom_heat_rate(x, th[0])

# ---------------------------------------------------------------- figure
fig = plt.figure(figsize=(183 * MM, 112 * MM))
gs = fig.add_gridspec(2, 3, width_ratios=[1.25, 1, 1], height_ratios=[1, 1],
                      left=0.075, right=0.985, bottom=0.085, top=0.93, wspace=0.55, hspace=0.62)
ax_a = fig.add_subplot(gs[:, 0])
ax_b = fig.add_subplot(gs[0, 1:])
ax_c = fig.add_subplot(gs[1, 1])
ax_d = fig.add_subplot(gs[1, 2])

# a — temperature field (hero)
levels = np.linspace(36, 70, 35)
cf = ax_a.contourf(X, Y, T, levels=levels, cmap=cmap_thermal)
iso = [40, 45, 50, 55, 60, 65, 68]
for lv in iso:
    col = INK if lv < 52 else C["krom"]
    cs = ax_a.contour(X, Y, T, levels=[lv], colors=[col], linewidths=0.5)
    ax_a.clabel(cs, fmt="%d", fontsize=5.5, inline_spacing=2,
                manual=[(0.5, float(np.interp(lv, T[:, N // 2], y)))])
ax_a.set_aspect("equal")
ax_a.set(xlim=(0, 1), ylim=(0, 1), xticks=[0, 0.5, 1], yticks=[0, 0.5, 1],
         xlabel="x/L", ylabel="y/L")
for s in ("top", "right"):
    ax_a.spines[s].set_visible(True)
# boundary conditions, written outside the plate
ax_a.text(0.5, 1.025, r"$T_w$ = 70 °C (top, left, right)", transform=ax_a.transAxes,
          ha="center", va="bottom", fontsize=6)
ax_a.annotate("", xy=(0.95, -0.25), xytext=(0.05, -0.25), xycoords="axes fraction",
              arrowprops=dict(arrowstyle="-|>", lw=0.6, color=MUTED, mutation_scale=6))
ax_a.text(0.5, -0.29, f"water, 1 m s$^{{-1}}$, 20 °C\nh = {H_CONV/1e3:.1f} kW m$^{{-2}}$ K$^{{-1}}$ (Bi = {BI_DEFAULT:.2f})",
          transform=ax_a.transAxes, ha="center", va="top", fontsize=6, linespacing=1.3)
cb = fig.colorbar(cf, ax=ax_a, fraction=0.046, pad=0.04, ticks=[40, 50, 60, 70])
cb.set_label("T (°C)", labelpad=2)
cb.outline.set_linewidth(0.4)
panel_letter(ax_a, "a", dx=-0.2, dy=1.06)

# b — bottom-surface temperature, FDM vs series
ax_b.plot(x, to_celsius(th[0]), color=S1, lw=1.2, zorder=2)
ax_b.plot(x[::5], T_ex[0, ::5], "o", ms=3.2, mfc="white", mec=S2, mew=0.8, zorder=3)
ax_b.set(xlim=(0, 1), ylim=(34, 72), xticks=np.linspace(0, 1, 6), yticks=[40, 50, 60, 70],
         xlabel="x/L", ylabel="T(x, 0) (°C)")
ax_b.margins(x=0.02)
ax_b.plot([0.40, 0.45], [66.5, 66.5], color=S1, lw=1.2)
ax_b.text(0.47, 66.5, f"FDM, N = {N}", fontsize=6, va="center")
ax_b.plot([0.425], [61.5], "o", ms=3.2, mfc="white", mec=S2, mew=0.8)
ax_b.text(0.47, 61.5, "series solution (4000 terms)", fontsize=6, va="center")
ax_b.annotate(f"min {T[0].min():.1f} °C", xy=(0.5, T[0].min()), xytext=(0.36, 52),
              fontsize=6, ha="center",
              arrowprops=dict(arrowstyle="-", lw=0.5, color=MUTED, shrinkA=1, shrinkB=2))
panel_letter(ax_b, "b", dx=-0.11, dy=1.04)

# c — log10 |error| map
err = np.abs(th - th_ex)
le = np.log10(np.maximum(err, 1e-8))
cl = np.arange(-7, -1.99, 0.5)
cc = ax_c.contourf(X, Y, le, levels=cl, cmap=cmap_error, extend="min")
ax_c.set_aspect("equal")
ax_c.set(xlim=(0, 1), ylim=(0, 1), xticks=[0, 0.5, 1], yticks=[0, 0.5, 1], xlabel="x/L", ylabel="y/L")
for s in ("top", "right"):
    ax_c.spines[s].set_visible(True)
cb2 = fig.colorbar(cc, ax=ax_c, fraction=0.05, pad=0.04, ticks=[-7, -5, -3])
cb2.set_label(r"log$_{10}$|θ$_{FDM}$ − θ$_{series}$|", labelpad=2)
cb2.outline.set_linewidth(0.4)
panel_letter(ax_c, "c", dx=-0.42, dy=1.04)

# d — grid convergence
ax_d.loglog(dx, l2, "o-", color=S1, ms=3, lw=1.0, mfc=S1)
ax_d.loglog(dx, linf, "s-", color=S2, ms=3, lw=1.0, mfc=S2)
xx = np.array([dx[-1], dx[0]])
ax_d.loglog(xx, l2[-1] * (xx / dx[-1]) ** 2 * 0.55, color=MUTED, lw=0.6, ls=(0, (3, 2)))
ax_d.loglog(xx, linf[-1] * (xx / dx[-1]) * 0.6, color=MUTED, lw=0.6, ls=(0, (1, 1.5)))
ax_d.text(dx[0] * 1.08, l2[0], f"rel. L$_2$\n(p = {order_l2:.2f})", fontsize=5.5, va="center")
ax_d.text(dx[0] * 1.08, linf[0], f"max\n(p = {order_linf:.2f})", fontsize=5.5, va="center")
xm = dx[2]
ax_d.text(xm * 1.08, l2[-1] * (xm / dx[-1]) ** 2 * 0.55 * 0.62, "slope 2", fontsize=5.5,
          color=MUTED, va="top", ha="left")
ax_d.text(xm * 1.08, linf[-1] * (xm / dx[-1]) * 0.6 * 0.66, "slope 1", fontsize=5.5,
          color=MUTED, va="top", ha="left")
ax_d.set(xlim=(dx[-1] * 0.7, dx[0] * 3.2), ylim=(8e-6, 5e-2),
         xlabel="grid spacing Δ (–)", ylabel="error vs series")
ax_d.xaxis.set_minor_formatter(NullFormatter())
ax_d.yaxis.set_major_locator(LogLocator(base=10, numticks=6))
panel_letter(ax_d, "d", dx=-0.42, dy=1.04)

save_figure(fig, HERE / "figures" / "fig01_fdm_reference")
plt.close(fig)

summary = {
    "inputs": {"L_m": L, "k_W_mK": K_SOLID, "T_wall_C": T_WALL, "T_inf_C": T_INF, "U_m_s": 1.0},
    "correlation": {"Re": round(RE), "Nu": round(NU, 1), "h_W_m2K": round(H_CONV), "Bi": round(BI_DEFAULT, 3)},
    "fdm_N101": {"theta_mid_bottom": round(float(th[0, N // 2]), 4),
                 "T_mid_bottom_C": round(float(T[0, N // 2]), 2),
                 "int_theta_bottom": round(float(q_fdm), 4),
                 "Q_per_depth_W_m": round(float(Q_fdm)),
                 "rel_L2": float(f"{l2[2]:.3g}"), "max_err": float(f"{linf[2]:.3g}")},
    "series": {"int_theta_bottom": round(float(q_exact), 4)},
    "convergence": {"N": Ns.tolist(), "rel_L2": [float(f"{v:.3g}") for v in l2],
                    "max_err": [float(f"{v:.3g}") for v in linf],
                    "order_L2": round(float(order_l2), 2), "order_max": round(float(order_linf), 2),
                    "int_theta_bottom": [round(float(v), 4) for v in qs]},
}
(HERE / "data").mkdir(exist_ok=True)
(HERE / "data" / "summary.json").write_text(json.dumps(summary, indent=1))
print(json.dumps(summary, indent=1))
