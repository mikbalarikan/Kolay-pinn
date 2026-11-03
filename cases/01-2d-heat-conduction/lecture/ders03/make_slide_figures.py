"""
Ders 03 slayt görselleri (projeksiyon boyutu, Türkişi paleti).
Önce: python hybrid_runs.py ; python hybrid_summary.py
Çalıştırma: python lecture/ders03/make_slide_figures.py   ->  lecture/ders03/assets/*.png
"""

import json
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
CASE = HERE.parents[1]
ROOT = CASE.parents[1]
sys.path.insert(0, str(CASE))
sys.path.insert(0, str(ROOT))

from fdm_solver import BI_DEFAULT, solve_fdm  # noqa: E402
from kolay_pinn.style import C, INK, MUTED, cmap_thermal, use_slide_style  # noqa: E402

use_slide_style()
OUT = HERE / "assets"
OUT.mkdir(exist_ok=True)
DPI = 220
S = json.loads((CASE / "data" / "summary_hybrid.json").read_text())
RUN = lambda tag, f: np.load(CASE / "runs" / tag / f)  # noqa: E731
T = lambda th: 20 + 50 * th  # noqa: E731
b = S["count"]["0"]["rel_L2"]


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=DPI)
    plt.close(fig)


def band(ax, text=True):
    ax.axhspan(b["min"], b["max"], color=C["krom"], zorder=0)
    if text:
        ax.text(0.98, b["max"] * 1.1, "veri yok · 3 tohum", ha="right", fontsize=12, color=MUTED,
                transform=ax.get_yaxis_transform())


def strip(ax, groups, colors):
    for i, (g, st) in enumerate(groups.items()):
        v = np.array(st["rel_L2"]["values"])
        ax.scatter([i] * v.size, v, s=70, color=colors[i], zorder=3, linewidths=0)
        ax.plot([i - 0.25, i + 0.25], [st["rel_L2"]["gmean"]] * 2, color=INK, lw=2, zorder=4)
    ax.set_yscale("log")
    ax.set_xlim(-0.5, len(groups) - 0.5)
    ax.set_ylabel("bağıl L$_2$ hata")


for f in ("ti_light.png", "ti_dark.png", "maskot_normal.png", "maskot_mutlu.png"):
    shutil.copy(CASE / "lecture" / "assets" / f, OUT / f)

# 1 — sensor placements on the FDM field ----------------------------------------------
x, _, th = solve_fdm(201, BI_DEFAULT)
X, Y = np.meshgrid(x, x)
fig, axs = plt.subplots(1, 3, figsize=(12.4, 4.4))
for ax, (tag, lab) in zip(axs, [("hyb_n20_s0", "düzgün"), ("hyb_corner_s0", "köşe (r < 0.2)"), ("hyb_bottom_s0", "alt şerit (η < 0.1)")]):
    d = RUN(tag, "data.npz")
    cf = ax.contourf(X, Y, T(th), levels=20, cmap=cmap_thermal)
    ax.scatter(d["X"][:, 0], d["X"][:, 1], s=55, facecolor="white", edgecolor=INK, lw=1.2, zorder=3)
    ax.set(aspect="equal", xticks=[0, 0.5, 1], yticks=[0, 0.5, 1], xlabel="ξ", title=f"{lab} · 20 sensör")
axs[0].set_ylabel("η")
cb = fig.colorbar(cf, ax=axs, fraction=0.02, pad=0.02)
cb.set_label("T (°C)")
save(fig, "01_sensors")

# 2 — loss terms during training: μ = 1 vs μ = 100 ------------------------------------
fig, axs = plt.subplots(1, 2, figsize=(11.6, 4.3), sharey=True)
for ax, (tag, mu) in zip(axs, [("hyb_n20_s0", 1), ("hyb_mu100_s0", 100)]):
    h = RUN(tag, "history.npz")
    ax.axvspan(6000, h["it"].max(), color=C["krom"], zorder=0)
    ax.semilogy(h["it"], h["pde"], color=C["celik_mavisi"], lw=1.8, label="PDE")
    ax.semilogy(h["it"], h["rob"], color=C["plan"], lw=1.8, label="Robin")
    ax.semilogy(h["it"], mu * h["data"], color=C["lila"], lw=1.8, label=f"μ · veri  (μ = {mu})")
    ax.set(xlabel="iterasyon", title=f"μ = {mu}")
    ax.legend(loc="upper right", fontsize=11)
axs[0].set_ylabel("kayıp terimi")
axs[0].text(6200, 3, "L-BFGS", fontsize=12, color=MUTED)
fig.tight_layout()
save(fig, "02_loss_terms")

# 3 — sensor count -------------------------------------------------------------------
fig, axs = plt.subplots(1, 2, figsize=(12.0, 4.4), gridspec_kw={"width_ratios": [1, 1.1]})
ax = axs[0]
band(ax)
strip(ax, S["count"], [C["titanyum"]] + [C["plan"]] * 3)
ax.set_xticks(range(4), ["0", "5", "20", "80"])
ax.set_xlabel("sensör sayısı $N_d$")
ax.set_title("σ = 0.01 · düzgün · μ = 1", fontsize=13, color=MUTED)
ax = axs[1]
band(ax, text=False)
strip(ax, S["config"], [C["plan"], C["parca_mandalina"], C["lila"], C["derin"]])
ax.set_xticks(range(4), ["düzgün\nμ = 1", "köşe\nμ = 1", "alt şerit\nμ = 1", "düzgün\nμ = 100"])
ax.set_title("$N_d$ = 20", fontsize=13, color=MUTED)
fig.tight_layout()
save(fig, "03_count_config")

# 4 — noise: fit vs measurement and vs truth --------------------------------------------
fig, ax = plt.subplots(figsize=(7.2, 4.6))
sig = ["0.0", "0.01", "0.05"]
nz = [S["noise"][s] for s in sig]
xs = np.arange(3)
ax.scatter(xs, [n["data_rmse_vs_noisy"] for n in nz], s=90, facecolor="white", edgecolor=C["plan"], lw=1.8, zorder=3, label="ölçüme göre")
ax.scatter(xs, [n["data_rmse_vs_clean"] for n in nz], s=90, color=C["plan"], zorder=3, linewidths=0, label="gerçeğe göre")
ax.scatter(xs, [n["noise_rms"] if n["noise_rms"] > 0 else np.nan for n in nz], marker="_", s=500, lw=2.2,
           color=C["titanyum"], zorder=2, label="gürültü düzeyi")
ax.set_yscale("log")
ax.set_xticks(xs, ["σ = 0", "σ = 0.01\n0.5 °C", "σ = 0.05\n2.5 °C"])
ax.set_xlim(-0.5, 2.5)
ax.set_ylabel("sensörlerde θ RMSE")
ax.legend(loc="upper left", fontsize=12)
fig.tight_layout()
save(fig, "04_noise")

# 5 — wrong physics: bottom profile + error bars --------------------------------------
WR = [("wrongbi_n0", "Bi = 2, veri yok", C["titanyum"], (0, (4, 2))),
      ("wrongbi_n20_mu1", "Bi = 2 + 20 sensör, μ = 1", C["elektrik"], "-"),
      ("wrongbi_n20_mu100", "Bi = 2 + 20 sensör, μ = 100", C["lila"], "-"),
      ("wrongbi_n80_mu100", "Bi = 2 + 80 sensör, μ = 100", C["derin"], "-")]
fig, axs = plt.subplots(1, 2, figsize=(12.4, 4.5), gridspec_kw={"width_ratios": [1.25, 1]})
ax = axs[0]
p0 = RUN("uniform", "prediction.npz")
ax.plot(p0["x"], T(p0["theta_exact"][0]), color=INK, lw=3.2, label="gerçek (Bi = 4.9)")
for tag, lab, col, ls in WR:
    p = RUN(tag, "prediction.npz")
    ax.plot(p["x"], T(p["theta"][0]), color=col, lw=1.9, ls=ls, label=lab)
ax.set(xlabel="ξ", ylabel="alt yüzey T (°C)", xlim=(0, 1))
ax.legend(loc="upper center", fontsize=10.5, ncol=1)
ax = axs[1]
names = ["veri\nyok", "20 · μ=1", "20 · μ=100", "80 · μ=100"]
vals = [S["wrong_bi"][k]["rel_L2"] for k in S["wrong_bi"]]
ax.bar(range(4), vals, width=0.6, color=[w[2] for w in WR], zorder=3)
ax.axhspan(b["min"], b["max"], color=C["krom"], zorder=0)
ax.text(3.45, b["max"] * 1.15, "doğru fizik · 3 tohum", ha="right", fontsize=11, color=MUTED)
ax.set_yscale("log")
ax.set_xticks(range(4), names, fontsize=12)
ax.set_ylabel("bağıl L$_2$ hata")
fig.tight_layout()
save(fig, "05_wrong_bi")

print(sorted(p.name for p in OUT.glob("*.png")))
