"""
Fig. 2 — Forward PINN ve doğrulama (Nature biçimi, Türkişi paleti).
Önce üç koşu:
    python pinn_forward.py --tag uniform
    python pinn_forward.py --corner --tag corner
    python pinn_forward.py --skip 0.02 --tag skip
Çıktı: figures/fig02_pinn_forward.{pdf,svg,png}, data/summary_pinn.json
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle
from matplotlib.ticker import LogLocator, NullFormatter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from kolay_pinn.style import C, INK, MM, MUTED, cmap_error, panel_letter, save_figure, use_style  # noqa: E402

use_style()
RUNS = {"uniform": ("düzgün", C["plan"]),
        "corner": ("köşe sıklaştırma", C["parca_mandalina"]),
        "skip": ("köşe dışlama, δ = 0.02", C["lila"])}
R = {}
for tag in RUNS:
    d = HERE / "runs" / tag
    R[tag] = {"m": json.loads((d / "metrics.json").read_text()), "h": np.load(d / "history.npz"),
              "p": np.load(d / "prediction.npz")}

x = R["uniform"]["p"]["x"]
X, Y = np.meshgrid(x, x)
ex = R["uniform"]["p"]["theta_exact"]
fdm = R["uniform"]["p"]["theta_fdm"]

fig = plt.figure(figsize=(183 * MM, 125 * MM))
gs = fig.add_gridspec(2, 3, height_ratios=[1, 1.15], left=0.07, right=0.915, bottom=0.07, top=0.95,
                      wspace=0.38, hspace=0.5)
ax_a = fig.add_subplot(gs[0, 0])
ax_b = fig.add_subplot(gs[0, 1:])
maps = [fig.add_subplot(gs[1, k]) for k in range(3)]

# a — total loss, three runs
n_adam = R["uniform"]["h"]["it"][R["uniform"]["h"]["phase"] == 0].max()
it_max = max(R[t]["h"]["it"].max() for t in R)
ax_a.axvspan(n_adam, it_max * 1.02, color=C["krom"], zorder=0)
short = {"uniform": "düzgün", "corner": "sıklaştırma", "skip": "dışlama"}
for tag, (lab, col) in RUNS.items():
    h = R[tag]["h"]
    ax_a.semilogy(h["it"], h["loss"], color=col, lw=0.9)
    ax_a.text(h["it"][-1] * 1.02, h["loss"][-1], short[tag], fontsize=5.5, va="center", color=INK)
ax_a.text(n_adam * 0.5, 3e2, "Adam", fontsize=6, ha="center", color=MUTED)
ax_a.text(n_adam + (it_max - n_adam) / 2, 3e2, "L-BFGS", fontsize=6, ha="center", color=MUTED)
ax_a.set(xlabel="iterasyon", ylabel="toplam kayıp", xlim=(0, it_max * 1.02), ylim=(None, 2e3))
ax_a.spines["right"].set_visible(False)
ax_a.yaxis.set_major_locator(LogLocator(base=10, numticks=7))
panel_letter(ax_a, "a", dx=-0.32, dy=1.02)

# b — error along the cooled surface
for tag, (lab, col) in RUNS.items():
    eb = np.abs(R[tag]["p"]["theta"][0] - ex[0])
    m = R[tag]["m"]
    ax_b.semilogy(x[1:-1], eb[1:-1], color=col, lw=0.9,
                  label=f"PINN, {lab}: L$_2$ {m['rel_L2']:.1e}, Q′ %{100 * m['Q_rel_err']:.2f}")
ax_b.semilogy(x[1:-1], np.abs(fdm[0] - ex[0])[1:-1], color=MUTED, lw=0.8, ls=(0, (2, 1.5)), label="FDM, N = 201")
ax_b.set(xlabel="x/L", ylabel="|θ − θ$_{seri}$|, alt yüzey", xlim=(0, 1), ylim=(1e-7, 1))
ax_b.yaxis.set_major_locator(LogLocator(base=10, numticks=8))
ax_b.yaxis.set_minor_formatter(NullFormatter())
ax_b.legend(loc="lower center", fontsize=5.5, ncol=2, columnspacing=1.0, handlelength=1.6)
panel_letter(ax_b, "b", dx=-0.1, dy=1.02)

# c, d, e — log10 |error| maps
levels = np.arange(-6, -0.99, 0.5)
for ax, (tag, (lab, col)), letter in zip(maps, RUNS.items(), "cde"):
    e = np.abs(R[tag]["p"]["theta"] - ex)
    cf = ax.contourf(X, Y, np.log10(np.maximum(e, 1e-8)), levels=levels, cmap=cmap_error, extend="both")
    ax.set(aspect="equal", xlim=(0, 1), ylim=(0, 1), xticks=[0, 0.5, 1], yticks=[0, 0.5, 1], xlabel="x/L")
    for s in ("top", "right"):
        ax.spines[s].set_visible(True)
    for cx in (0.0, 1.0):
        ax.add_patch(Circle((cx, 0.0), 0.09, fill=False, ec=MUTED, lw=0.9, ls=(0, (2, 1)), clip_on=False))
    ax.plot([0.08, 0.92], [1.04, 1.04], color=col, lw=2.2, transform=ax.transAxes, clip_on=False, solid_capstyle="butt")
    ax.set_title(lab, fontsize=6.5, pad=7)
    panel_letter(ax, letter, dx=-0.3 if letter == "c" else -0.12, dy=1.08)
maps[0].set_ylabel("y/L")
cax = fig.add_axes([0.93, 0.1, 0.011, 0.33])
cb = fig.colorbar(cf, cax=cax, ticks=[-6, -4, -2])
cb.set_label(r"log$_{10}$|θ$_{PINN}$ − θ$_{seri}$|", labelpad=2)
cb.outline.set_linewidth(0.4)

save_figure(fig, HERE / "figures" / "fig02_pinn_forward")
plt.close(fig)

keys = ("rel_L2", "max_err", "max_err_at", "rel_L2_interior", "theta_mid_bottom", "T_mid_bottom_C", "int_theta_bottom",
        "Q_W_m", "Q_rel_err", "t_total_s", "n_int", "n_bot", "final_loss", "final_pde", "final_robin")
summary = {tag: {k: R[tag]["m"][k] for k in keys} for tag in RUNS}
summary["reference"] = {"theta_mid_bottom": R["uniform"]["m"]["theta_mid_bottom_exact"],
                        "int_theta_bottom": R["uniform"]["m"]["int_theta_bottom_exact"],
                        "Q_W_m": R["uniform"]["m"]["Q_W_m_exact"],
                        "rel_L2_fdm_N201": R["uniform"]["m"]["rel_L2_fdm_same_grid"]}
(HERE / "data" / "summary_pinn.json").write_text(json.dumps(summary, indent=1))
print(json.dumps({t: {k: summary[t][k] for k in ("rel_L2", "rel_L2_interior", "max_err", "Q_rel_err")} for t in RUNS}, indent=1))
