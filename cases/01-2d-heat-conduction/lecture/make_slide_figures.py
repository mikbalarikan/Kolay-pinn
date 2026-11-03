"""
Ders slaytları için kanıt görselleri (projeksiyon boyutu, Türkişi paleti).
Çıktı: lecture/assets/*.png   — build_lecture.js bunları kullanır.
Çalıştırma: python lecture/make_slide_figures.py
"""

import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

HERE = Path(__file__).resolve().parent
CASE = HERE.parent
ROOT = CASE.parents[1]
sys.path.insert(0, str(CASE))
sys.path.insert(0, str(ROOT))

from fdm_solver import BI_DEFAULT, H_CONV, analytical, solve_fdm, to_celsius  # noqa: E402
from kolay_pinn.style import C, INK, MUTED, cmap_error, cmap_thermal, use_slide_style  # noqa: E402

use_slide_style()
OUT = HERE / "assets"
OUT.mkdir(exist_ok=True)
S1, S2 = C["plan"], C["lila"]
DPI = 220


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=DPI, transparent=False)
    plt.close(fig)


N = 101
x, y, th = solve_fdm(N)
th_ex = analytical(x, y)
X, Y = np.meshgrid(x, y)
T = to_celsius(th)

# 1 — problem schematic ------------------------------------------------------
fig, ax = plt.subplots(figsize=(5.6, 5.0))
ax.add_patch(Rectangle((0, 0), 1, 1, fc=C["krom"], ec="none"))
for (x0, y0, x1, y1) in [(0, 0, 0, 1), (1, 0, 1, 1), (0, 1, 1, 1)]:
    ax.plot([x0, x1], [y0, y1], color=C["celik_mavisi"], lw=7, solid_capstyle="butt")
ax.plot([0, 1], [0, 0], color=S1, lw=7, solid_capstyle="butt")
ax.text(0.5, 1.07, "T = 70 °C", ha="center", fontsize=16, fontweight="bold")
ax.text(-0.09, 0.5, "T = 70 °C", ha="center", va="center", rotation=90, fontsize=16, fontweight="bold")
ax.text(1.09, 0.5, "T = 70 °C", ha="center", va="center", rotation=90, fontsize=16, fontweight="bold")
ax.text(0.5, 0.55, "çelik\nk = 49 W m$^{-1}$ K$^{-1}$", ha="center", va="center", fontsize=15, color=INK)
ax.annotate("", xy=(1.0, 0.12), xytext=(0.0, 0.12), xycoords="data",
            arrowprops=dict(arrowstyle="<->", lw=1.2, color=MUTED))
ax.text(0.5, 0.15, "L = 0.1 m", ha="center", va="bottom", fontsize=14, color=MUTED)
for yy in (-0.13, -0.21):
    ax.add_patch(FancyArrowPatch((0.05, yy), (0.95, yy), arrowstyle="-|>", mutation_scale=18,
                                 lw=1.6, color=S1))
ax.text(0.5, -0.27, "su · 1 m/s · 20 °C  →  konvektif soğutma", ha="center", va="top", fontsize=15)
ax.set(xlim=(-0.2, 1.2), ylim=(-0.36, 1.15), aspect="equal")
ax.axis("off")
fig.subplots_adjust(0, 0, 1, 1)
save(fig, "01_schematic")

# 2 — Bi regimes: bottom-surface profile for several Bi ----------------------
fig, ax = plt.subplots(figsize=(6.4, 4.4))
xs = np.linspace(0, 1, 401)
cases = [(0.006, "Bi = 0.006 · alüminyum, hava", C["gumus"]),
         (0.5, "Bi = 0.5", C["elektrik_isigi"]),
         (BI_DEFAULT, f"Bi = {BI_DEFAULT:.1f} · çelik, su (bu ders)", S1),
         (50, "Bi = 50", C["derin"])]
for bi, lab, col in cases:
    tb = analytical(xs, np.array([0.0]), Bi=bi, n_terms=3000)[0]
    lw = 3.2 if abs(bi - BI_DEFAULT) < 1e-6 else 1.8
    ax.plot(xs, tb, color=col, lw=lw, label=lab)
ax.set(xlim=(0, 1), ylim=(0, 1.05), xlabel="ξ = x/L", ylabel="θ(ξ, 0)  alt yüzey")
ax.legend(loc="center", fontsize=12, ncol=1, bbox_to_anchor=(0.5, 0.64))
fig.tight_layout(pad=0.4)
save(fig, "02_bi_regimes")

# 3 — FDM stencil + ghost node ----------------------------------------------
fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.4))
for k, ax in enumerate(axs):
    ax.set(xlim=(-1.8, 1.8), ylim=(-1.8, 1.8), aspect="equal")
    ax.axis("off")
    for g in (-1, 0, 1):
        ax.plot([-1.5, 1.5], [g, g], color=C["gumus"], lw=0.8, zorder=0)
        ax.plot([g, g], [-1.5, 1.5], color=C["gumus"], lw=0.8, zorder=0)
ax = axs[0]
pts = {(0, 0): ("i, j", -4), (1, 0): ("i+1, j", 1), (-1, 0): ("i−1, j", 1), (0, 1): ("i, j+1", 1), (0, -1): ("i, j−1", 1)}
for (px, py), (lab, w) in pts.items():
    ax.add_patch(Circle((px, py), 0.16, fc=S1 if w == -4 else C["kagit"], ec=S1, lw=2, zorder=3))
    ax.text(px + 0.22, py + 0.22, lab, fontsize=12, zorder=4)
    ax.text(px, py - 0.42, f"{w:+d}" if w != 1 else "+1", ha="center", fontsize=12, color=MUTED, zorder=4)
ax.set_title("İç düğüm: 5 noktalı şablon", fontsize=15, pad=4)
ax = axs[1]
ax.axhspan(-1.8, 0.0, color=S1, alpha=0.10, zorder=0)       # water side (nodes here are fictitious)
ax.plot([-1.5, 1.5], [0.0, 0.0], color=S1, lw=3, zorder=1)  # cooled surface passes through row j = 0
ax.text(1.55, -0.12, "su", color=INK, fontsize=12, va="top", ha="right")
pts2 = {(0, 0): ("i, 0  (yüzey)", "c"), (1, 0): ("", "n"), (-1, 0): ("", "n"), (0, 1): ("i, 1", "n"), (0, -1): ("i, −1  hayalet", "g")}
for (px, py), (lab, kind) in pts2.items():
    fc = S1 if kind == "c" else (C["kagit"] if kind == "n" else "white")
    ls = "--" if kind == "g" else "-"
    ax.add_patch(Circle((px, py), 0.16, fc=fc, ec=S2 if kind == "g" else S1, lw=2, ls=ls, zorder=3))
    if lab:
        ax.text(px + 0.22, py + 0.22 if kind != "g" else py - 0.05, lab, fontsize=12, zorder=4, va="center" if kind == "g" else "bottom")
ax.set_title("Alt kenar: hayalet düğüm", fontsize=15, pad=4)
fig.tight_layout(pad=0.3)
save(fig, "03_stencil_ghost")

# 4 — temperature field (slide size) -----------------------------------------
fig, ax = plt.subplots(figsize=(5.6, 4.9))
cf = ax.contourf(X, Y, T, levels=np.linspace(36, 70, 35), cmap=cmap_thermal)
for lv in [40, 45, 50, 55, 60, 65, 68]:
    col = INK if lv < 52 else C["krom"]
    cs = ax.contour(X, Y, T, levels=[lv], colors=[col], linewidths=1.0)
    ax.clabel(cs, fmt="%d", fontsize=11, manual=[(0.5, float(np.interp(lv, T[:, N // 2], y)))])
ax.set(xlim=(0, 1), ylim=(0, 1), aspect="equal", xticks=[0, 0.5, 1], yticks=[0, 0.5, 1], xlabel="x/L", ylabel="y/L")
for s in ("top", "right"):
    ax.spines[s].set_visible(True)
cb = fig.colorbar(cf, ax=ax, ticks=[40, 50, 60, 70], fraction=0.046, pad=0.04)
cb.set_label("T (°C)")
fig.tight_layout(pad=0.4)
save(fig, "04_field")

# 5 — bottom profile ----------------------------------------------------------
fig, ax = plt.subplots(figsize=(7.6, 4.2))
ax.plot(x, T[0], color=S1, lw=2.6, label=f"FDM, N = {N}")
ax.plot(x[::5], to_celsius(th_ex[0, ::5]), "o", ms=7, mfc="white", mec=S2, mew=1.6, label="seri çözüm")
ax.set(xlim=(0, 1), ylim=(34, 72), yticks=[40, 50, 60, 70], xlabel="x/L", ylabel="T(x, 0) (°C)")
ax.legend(loc="upper center", ncol=2)
fig.tight_layout(pad=0.4)
save(fig, "05_bottom_profile")

# 6 — log error map -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(5.6, 4.9))
le = np.log10(np.maximum(np.abs(th - th_ex), 1e-8))
cc = ax.contourf(X, Y, le, levels=np.arange(-7, -1.99, 0.5), cmap=cmap_error, extend="min")
ax.set(xlim=(0, 1), ylim=(0, 1), aspect="equal", xticks=[0, 0.5, 1], yticks=[0, 0.5, 1], xlabel="x/L", ylabel="y/L")
for s in ("top", "right"):
    ax.spines[s].set_visible(True)
for cx in (0.0, 1.0):
    ax.add_patch(Circle((cx, 0.0), 0.09, fill=False, ec=C["parca_mandalina"], lw=2.4, clip_on=False))
cb = fig.colorbar(cc, ax=ax, ticks=[-7, -5, -3], fraction=0.046, pad=0.04)
cb.set_label("log₁₀ |hata|")
fig.tight_layout(pad=1.0)
save(fig, "06_error_map")

# 7 — convergence -----------------------------------------------------------------
Ns = np.array([26, 51, 101, 201])
l2, linf = [], []
for n in Ns:
    xn, yn, tn = solve_fdm(n)
    en = analytical(xn, yn)
    l2.append(np.linalg.norm(tn - en) / np.linalg.norm(en))
    linf.append(np.abs(tn - en).max())
d = 1 / (Ns - 1)
fig, ax = plt.subplots(figsize=(6.2, 4.4))
ax.loglog(d, l2, "o-", color=S1, label="bağıl L₂")
ax.loglog(d, linf, "s-", color=S2, label="maksimum")
xx = np.array([d[-1], d[0]])
ax.loglog(xx, l2[-1] * (xx / d[-1]) ** 2 * 0.55, color=MUTED, lw=1.2, ls="--", label="eğim 2")
ax.loglog(xx, linf[-1] * (xx / d[-1]) * 0.6, color=MUTED, lw=1.2, ls=":", label="eğim 1")
ax.set(xlabel="ağ aralığı Δ", ylabel="seri çözüme göre hata", ylim=(8e-6, 5e-2))
ax.legend(loc="lower right", fontsize=12, ncol=2)
fig.tight_layout(pad=0.4)
save(fig, "07_convergence")

# brand marks (from SVG) ----------------------------------------------------------
brand = ROOT / "brand"
ti = (brand / "ti_mark.svg")
hatch = "".join(f"M{v} 75.5 L{v - 5} 83 " for v in range(22, 83, 10))
for ink, name in [(C["krom"], "ti_light"), (C["derin"], "ti_dark")]:
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="10 16 82 70" width="328" height="280">'
           f'<rect x="16" y="20" width="42" height="11" fill="{ink}"/><rect x="31" y="20" width="12" height="52" fill="{ink}"/>'
           f'<rect x="64" y="38" width="12" height="34" fill="{ink}"/><circle cx="70" cy="27" r="6.5" fill="{C["kirmizi"]}"/>'
           f'<rect x="12" y="72" width="76" height="3.5" fill="{ink}"/><path d="{hatch}" stroke="{ink}" stroke-width="2.2" fill="none"/></svg>')
    p = OUT / f"{name}.svg"
    p.write_text(svg)
    subprocess.run(["rsvg-convert", "-o", str(OUT / f"{name}.png"), str(p)], check=True)
    p.unlink()
for expr in ("normal", "mutlu"):
    subprocess.run(["rsvg-convert", "-w", "600", "-o", str(OUT / f"maskot_{expr}.png"),
                    str(brand / f"maskot_kumpas_{expr}.svg")], check=True)
print(sorted(p.name for p in OUT.iterdir()))
