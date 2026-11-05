"""
Ders 04 slayt görselleri (projeksiyon boyutu, Türkişi paleti).
Önce: python inverse_classical.py ; python inverse_runs.py ; python inverse_summary.py
Çalıştırma: python lecture/ders04/make_slide_figures.py   ->  lecture/ders04/assets/*.png
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

from fdm_solver import solve_fdm  # noqa: E402
from kolay_pinn.style import C, INK, MUTED, use_slide_style  # noqa: E402

use_slide_style()
OUT = HERE / "assets"
OUT.mkdir(exist_ok=True)
DPI = 220
S = json.loads((CASE / "data" / "summary_inverse.json").read_text())
CL = json.loads((CASE / "data" / "inverse_classical.json").read_text())
BI = S["Bi_true"]
G = S["groups"]
RUN = lambda tag, f: np.load(CASE / "runs" / tag / f)  # noqa: E731
COL = {"temel 20 düzgün": C["plan"], "köşe dışlama yok": C["hata"], "üst yarı": C["parca_mandalina"],
       "alt şerit": C["lila"], "5 sensör": C["titanyum"], "80 sensör": C["celik_mavisi"], "μ = 1": C["gecti"]}
LAB = {"temel 20 düzgün": "temel\n20 düzgün", "köşe dışlama yok": "köşe\ndışlanmaz", "üst yarı": "üst\nyarı",
       "alt şerit": "alt\nşerit", "5 sensör": "5\nsensör", "80 sensör": "80\nsensör", "μ = 1": "μ = 1"}


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=DPI)
    plt.close(fig)


for f in ("ti_light.png", "ti_dark.png", "maskot_normal.png", "maskot_mutlu.png"):
    shutil.copy(CASE / "lecture" / "assets" / f, OUT / f)

# 1 — duyarlılık haritası |∂θ/∂Bi| ve üç yerleşim ------------------------------------------
Sen = np.load(CASE / "data" / "sensitivity_dtheta_dBi.npy")
x, _, _ = solve_fdm(201, BI)
X, Y = np.meshgrid(x, x)
fig, axs = plt.subplots(1, 3, figsize=(12.4, 4.5))
for ax, (tag, key, lab) in zip(axs, [("inv_base_s0", "uniform_n20_s0.01", "düzgün"),
                                     ("inv_top_s0", "top_n20_s0.01", "üst yarı (η > 0.5)"),
                                     ("inv_bottom_s0", "bottom_n20_s0.01", "alt şerit (η < 0.1)")]):
    d = RUN(tag, "data.npz")
    cf = ax.contourf(X, Y, np.abs(Sen), levels=np.linspace(0, 0.05, 21), cmap="Blues")
    ax.contour(X, Y, np.abs(Sen), levels=[0.005, 0.01, 0.02, 0.04], colors=INK, linewidths=0.6, alpha=0.6)
    ax.scatter(d["X"][:, 0], d["X"][:, 1], s=55, facecolor="white", edgecolor=INK, lw=1.2, zorder=3)
    crb = 100 * CL["cases"][key]["crb_rel"]
    ax.set(aspect="equal", xticks=[0, 0.5, 1], yticks=[0, 0.5, 1], xlabel="ξ", title=f"{lab} · CRB %{crb:.1f}")
axs[0].set_ylabel("η")
cb = fig.colorbar(cf, ax=axs, fraction=0.02, pad=0.02, ticks=[0, 0.01, 0.02, 0.03, 0.04, 0.05])
cb.set_label("|∂θ/∂Bi|")
save(fig, "01_sensitivity")

# 2 — eğitim boyunca Bi ----------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.4, 4.6))
TR = [("inv_base_s0", C["plan"], "Bi₀ = 1 (temel, tohum 0)"), ("inv_base_s1", C["plan"], None),
      ("inv_base_s2", C["plan"], None), ("inv_bi10", C["celik_mavisi"], "Bi₀ = 10"),
      ("inv_mu1_s0", C["gecti"], "μ = 1")]
for tag, col, lab in TR:
    if not (CASE / "runs" / tag / "history.npz").exists():
        continue
    h = RUN(tag, "history.npz")
    ax.plot(h["it"], h["Bi"], color=col, lw=2.0 if lab else 1.2, alpha=1 if lab else 0.55, label=lab)
ax.axhline(BI, color=INK, lw=1.2, ls="dashed")
ax.axvspan(6000, 8200, color=C["krom"], zorder=0)
ax.text(6100, 0.32, "L-BFGS", fontsize=12, color=MUTED)
ax.text(150, BI * 1.07, f"gerçek Bi = {BI:.3f}", fontsize=12, color=INK)
ax.set(yscale="log", ylim=(0.25, 14), xlim=(0, 8200), xlabel="iterasyon", ylabel="Bi tahmini = eˢ")
ax.legend(loc="upper right", fontsize=11)
fig.tight_layout()
save(fig, "02_trajectory")

# 3 — hata ve Cramér–Rao sınırı -----------------------------------------------------------
names = [g for g in LAB if g in G and g not in ("köşe dışlama yok", "μ = 1")]
fig, ax = plt.subplots(figsize=(11.8, 4.6))
for i, g in enumerate(names):
    v = G[g]
    e = 100 * np.array([r["Bi_rel_err"] for r in v["runs"]])
    f = 100 * np.array([r["fdm_ls_rel_err"] for r in v["runs"]])
    ax.scatter([i - 0.13] * e.size, e, s=80, color=COL[g], zorder=3, linewidths=0)
    ax.scatter([i + 0.13] * f.size, f, s=80, facecolor="white", edgecolor=COL[g], lw=1.8, zorder=3)
    ax.plot([i - 0.35, i + 0.35], [100 * v["crb_rel"]] * 2, color=INK, lw=2.2, zorder=4)
ax.scatter([], [], s=80, color=INK, label="PINN")
ax.scatter([], [], s=80, facecolor="white", edgecolor=INK, lw=1.8, label="FDM + en küçük kareler")
ax.plot([], [], color=INK, lw=2.2, label="Cramér–Rao σ_Bi / Bi")
ax.set(yscale="log", ylim=(0.02, 200), xlim=(-0.5, len(names) - 0.5), ylabel="|Bi tahmini − Bi| / Bi  (%)")
ax.set_xticks(range(len(names)), [LAB[g].replace("\n", " ") for g in names])
ax.legend(loc="upper left", fontsize=11, ncol=3, frameon=False)
fig.tight_layout()
save(fig, "03_error_crb")

# 4 — PINN ile klasik yöntem aynı veriden aynı Bi --------------------------------------------
fig, ax = plt.subplots(figsize=(5.6, 5.0))
lo, hi = 3.3, 5.6
ax.plot([lo, hi], [lo, hi], color=INK, lw=1.2)
ax.axhline(BI, color=MUTED, lw=0.8, ls="dotted"); ax.axvline(BI, color=MUTED, lw=0.8, ls="dotted")
for g, v in G.items():
    ax.scatter([r["fdm_ls_Bi"] for r in v["runs"]], [r["Bi_hat"] for r in v["runs"]], s=60, color=COL[g],
               zorder=3, linewidths=0, label=g)
ax.set(xlim=(lo, hi), ylim=(lo, hi), aspect="equal", xlabel="FDM + EKK  Bi", ylabel="PINN  Bi")
ax.legend(loc="upper left", fontsize=9.5, labelspacing=0.3, handletextpad=0.1)
fig.tight_layout()
save(fig, "04_parity")

# 5 — köşe yanlılığı: aynı sensörler, δ = 0.02 ile δ = 0 ---------------------------------------
fig, ax = plt.subplots(figsize=(6.8, 4.6))
a, b_ = G["temel 20 düzgün"]["runs"], G["köşe dışlama yok"]["runs"]
for k, (ra, rb) in enumerate(zip(a, b_)):
    ax.plot([0, 1, 2], [ra["fdm_ls_Bi"], ra["Bi_hat"], rb["Bi_hat"]], color=MUTED, lw=1.0, zorder=1)
    ax.scatter([0], [ra["fdm_ls_Bi"]], s=80, facecolor="white", edgecolor=INK, lw=1.6, zorder=3)
    ax.scatter([1], [ra["Bi_hat"]], s=80, color=C["plan"], zorder=3, linewidths=0)
    ax.scatter([2], [rb["Bi_hat"]], s=80, color=C["hata"], zorder=3, linewidths=0)
    ax.text(2.08, rb["Bi_hat"], f"tohum {k}", fontsize=11, color=MUTED, va="center")
ax.axhline(BI, color=INK, lw=1.2, ls="dashed")
ax.text(2.5, BI * 1.005, "gerçek", fontsize=11, color=INK, va="bottom", ha="right")
ax.set_xticks([0, 1, 2], ["FDM + EKK", "PINN\nδ = 0.02", "PINN\nδ = 0"])
ax.set(xlim=(-0.4, 2.55), ylabel="Bi tahmini")
fig.tight_layout()
save(fig, "05_corner")

# 6 — gürültü düzeyi --------------------------------------------------------------------
NZ = S["noise"]
sig = [s for s in ("0.0", "0.01", "0.05") if s in NZ]
fig, ax = plt.subplots(figsize=(6.8, 4.6))
for i, s in enumerate(sig):
    r = NZ[s]
    ax.scatter(i - 0.1, max(100 * r["Bi_rel_err"], 5e-3), s=100, color=C["plan"], zorder=3, linewidths=0)
    ax.scatter(i + 0.1, max(100 * r["fdm_ls_rel_err"], 5e-3), s=100, facecolor="white", edgecolor=C["plan"], lw=1.8, zorder=3)
    if r["crb_rel"] > 0:
        ax.plot([i - 0.3, i + 0.3], [100 * r["crb_rel"]] * 2, color=INK, lw=2.2, zorder=4)
    ax.text(i + 0.22, max(100 * r["Bi_rel_err"], 5e-3), f"Q %{100 * r['Q_rel_err']:.2f}", fontsize=12, va="center")
ax.set(yscale="log", ylim=(3e-3, 60), xlim=(-0.5, len(sig) - 0.5), ylabel="|Bi tahmini − Bi| / Bi  (%)")
ax.set_xticks(range(len(sig)), [{"0.0": "σ = 0", "0.01": "σ = 0.01\n0.5 °C", "0.05": "σ = 0.05\n2.5 °C"}[s] for s in sig])
fig.tight_layout()
save(fig, "06_noise")

print(sorted(p.name for p in OUT.glob("*.png")))
