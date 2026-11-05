"""
Sıcaklık atlası: seri çözüm, FDM ve tüm PINN koşularının T(x, y) konturları, ortak ölçek ve ortak eş-sıcaklık çizgileri.
Önce: Adım 4–6 koşuları. Çıktı: figures/fig07_temperature_atlas.{pdf,svg,png}
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
from plot_error_atlas import GCOL, G_REF, G_WRG, RUNS  # noqa: E402  (aynı koşu listesi ve grup renkleri)
from kolay_pinn.style import C, INK, MM, MUTED, cmap_thermal, save_figure, use_style  # noqa: E402

use_style()
T = lambda th: 20 + 50 * th  # noqa: E731
P = lambda t: np.load(HERE / "runs" / t / "prediction.npz")  # noqa: E731
p0 = P("uniform")
x = p0["x"]
X, Y = np.meshgrid(x, x)
T_ser = T(p0["theta_exact"])

FIELDS = [("seri çözüm (analitik)", T_ser, "analitik")]
for lab, tag, grp, _ in RUNS:
    FIELDS.append((lab, T(p0["theta_fdm"]) if tag is None else T(P(tag)["theta"]), grp))

LEV_F = np.arange(36, 70.01, 1.0)          # dolgu
LEV_L = np.arange(40, 66, 5.0)             # eş-sıcaklık çizgileri: 40, 45, …, 65 °C
GC = dict(GCOL, analitik=INK)

ncol, nrow = 6, 4
fig, axs = plt.subplots(nrow, ncol, figsize=(183 * MM, 140 * MM))
for k, ax in enumerate(axs.flat):
    ax.set(aspect="equal", xlim=(0, 1), ylim=(0, 1), xticks=[], yticks=[])
    if k < len(FIELDS):
        lab, F, grp = FIELDS[k]
        cf = ax.contourf(X, Y, F, levels=LEV_F, cmap=cmap_thermal, extend="min")
        ax.contour(X, Y, T_ser, levels=LEV_L, colors="white", linewidths=1.6, alpha=0.9)        # seri: beyaz alt çizgi
        cs = ax.contour(X, Y, F, levels=LEV_L, colors=[INK], linewidths=0.5)
        for s in ax.spines.values():
            s.set_visible(True); s.set_color(GC[grp]); s.set_linewidth(1.3)
        ax.set_title(lab, fontsize=5.8, color=INK, pad=2)
        ax.text(0.5, -0.04, f"alt orta {F[0, len(x) // 2]:.2f} °C", transform=ax.transAxes, ha="center", va="top",
                fontsize=5, color=INK)

# overlay panels: every method's isotherms on top of each other
for k, (xl, yl, ttl) in zip((len(FIELDS), len(FIELDS) + 1), [((0, 1), (0, 1), "tüm yöntemler üst üste"),
                                                           ((0, 0.25), (0, 0.25), "sol alt köşe, yakın plan")]):
    ax = axs.flat[k]
    for lab, F, grp in FIELDS[1:]:
        ax.contour(X, Y, F, levels=LEV_L, colors=[GC[grp]], linewidths=0.45, alpha=0.85)
    ax.contour(X, Y, T_ser, levels=LEV_L, colors=[INK], linewidths=1.0, linestyles="dashed")
    ax.set(xlim=xl, ylim=yl)
    for s in ax.spines.values():
        s.set_visible(True); s.set_color(MUTED); s.set_linewidth(0.8)
    ax.set_title(ttl, fontsize=5.8, color=INK, pad=2)
    if k == len(FIELDS) + 1:
        ax.contour(X, Y, T_ser, levels=np.arange(36, 70, 1.0), colors=[C["gumus"]], linewidths=0.2)
        ax.text(0.5, -0.04, "ince gri: seri, 1 °C aralık", transform=ax.transAxes, ha="center", va="top", fontsize=5, color=MUTED)
    else:
        ax.text(0.5, -0.04, "kesikli: seri · 40–65 °C", transform=ax.transAxes, ha="center", va="top", fontsize=5, color=INK)

# legend slot + colorbar slot
ax = axs.flat[-2]
ax.set_axis_off()
names = {"analitik": "seri çözüm", G_REF: "FDM", "forward · kolokasyon": "forward · kolokasyon",
         "forward · kapasite": "forward · kapasite", "hibrit · doğru fizik": "hibrit · doğru fizik", G_WRG: "hibrit · Bi = 2 (yanlış)"}
handles = [Line2D([], [], color=GC[g], lw=1.4) for g in names]
ax.legend(handles, list(names.values()), loc="center left", fontsize=5.5, frameon=False,
          handlelength=1.6, title="çerçeve / çizgi rengi", title_fontsize=5.5)
ax = axs.flat[-1]
ax.set_axis_off()
cax = ax.inset_axes([0.08, 0.70, 0.84, 0.08])
cb = fig.colorbar(cf, cax=cax, orientation="horizontal", ticks=[40, 50, 60, 70])
cb.ax.tick_params(labelsize=5)
cb.set_label("T (°C)", fontsize=6)
ax.text(0.08, 0.40, "eş-sıcaklık: 40, 45, …, 65 °C\nsiyah: yöntem\nbeyaz alt çizgi: seri\n201 × 201 ağ · tohum 0", transform=ax.transAxes,
        fontsize=5, color=MUTED, va="top")

fig.subplots_adjust(left=0.01, right=0.99, top=0.96, bottom=0.03, wspace=0.1, hspace=0.32)
save_figure(fig, HERE / "figures" / "fig07_temperature_atlas")
plt.close(fig)

mid = len(x) // 2
for lab, F, grp in FIELDS:
    print(f"{lab:24s} alt orta {F[0, mid]:6.2f} °C · merkez {F[mid, mid]:6.2f} °C · maks |T − T_seri| {np.abs(F - T_ser).max():.2f} °C")
