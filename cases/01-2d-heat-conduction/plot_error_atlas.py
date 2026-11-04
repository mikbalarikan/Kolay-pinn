"""
Hata atlası: şimdiye kadarki tüm PINN koşularında |T_seri − T_PINN| haritası, ortak renk ölçeğiyle.
Önce: Adım 4–6 koşuları (pinn_forward.py, study_runs.py, hybrid_runs.py)
Çıktı: figures/fig05_error_atlas.{pdf,svg,png}, figures/fig06_error_ranking.{pdf,svg,png}, data/summary_atlas.json
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from kolay_pinn.style import C, INK, MM, MUTED, cmap_error, panel_letter, save_figure, use_style  # noqa: E402

use_style()
DT = 50.0                      # T_w − T_∞ (K): θ hatası → °C
P = lambda t: np.load(HERE / "runs" / t / "prediction.npz")  # noqa: E731
M = lambda t: json.loads((HERE / "runs" / t / "metrics.json").read_text())  # noqa: E731

# (etiket, koşu, grup, aynı ayarın tohum koşuları)
G_REF, G_FWD, G_CAP, G_HYB, G_WRG = "referans", "forward · kolokasyon", "forward · kapasite", "hibrit · doğru fizik", "hibrit · yanlış fizik (Bi = 2)"
RUNS = [
    ("FDM, N = 201", None, G_REF, None),
    ("düzgün", "uniform", G_FWD, ["uniform", "uniform_s1", "uniform_s2"]),
    ("köşe sıklaştırma", "corner", G_FWD, ["corner", "corner_s1", "corner_s2"]),
    ("köşe dışlama", "skip", G_FWD, ["skip", "skip_s1", "skip_s2"]),
    ("uzun L-BFGS", "long", G_CAP, None),
    ("geniş 4×100", "wide4x100", G_CAP, None),
    ("derin 8×50", "deep8x50", G_CAP, None),
    ("5 sensör", "hyb_n5_s0", G_HYB, [f"hyb_n5_s{s}" for s in range(3)]),
    ("20 sensör", "hyb_n20_s0", G_HYB, [f"hyb_n20_s{s}" for s in range(3)]),
    ("80 sensör", "hyb_n80_s0", G_HYB, [f"hyb_n80_s{s}" for s in range(3)]),
    ("20 · köşe", "hyb_corner_s0", G_HYB, [f"hyb_corner_s{s}" for s in range(3)]),
    ("20 · alt şerit", "hyb_bottom_s0", G_HYB, [f"hyb_bottom_s{s}" for s in range(3)]),
    ("20 · μ = 100", "hyb_mu100_s0", G_HYB, [f"hyb_mu100_s{s}" for s in range(3)]),
    ("20 · σ = 0", "hyb_clean", G_HYB, None),
    ("20 · σ = 0.05", "hyb_noisy05", G_HYB, None),
    ("veri yok", "wrongbi_n0", G_WRG, None),
    ("20 · μ = 1", "wrongbi_n20_mu1", G_WRG, None),
    ("20 · μ = 100", "wrongbi_n20_mu100", G_WRG, None),
    ("80 · μ = 100", "wrongbi_n80_mu100", G_WRG, None),
]
GCOL = {G_REF: C["derin"], G_FWD: C["plan"], G_CAP: C["titanyum"], G_HYB: C["lila"], G_WRG: C["parca_mandalina"]}

p0 = P("uniform")
x, ex = p0["x"], p0["theta_exact"]
X, Y = np.meshgrid(x, x)
interior = (X > 0.05) & (X < 0.95) & (Y > 0.05) & (Y < 0.95)
corner = (np.minimum(np.hypot(X, Y), np.hypot(1 - X, Y)) < 0.1)


def err_field(tag):
    if tag is None:
        return np.abs(p0["theta_fdm"] - ex) * DT
    return np.abs(P(tag)["theta"] - ex) * DT


rows = []
for lab, tag, grp, seeds in RUNS:
    e = err_field(tag)
    j, i = np.unravel_index(e.argmax(), e.shape)
    rec = {"label": lab, "group": grp, "tag": tag or "fdm_N201",
           "rel_L2": float(np.linalg.norm(e) / np.linalg.norm(ex * DT)),  # θ tabanlı bağıl L2 ile aynı oran
           "rms_C": float(np.sqrt(np.mean(e ** 2))), "max_C": float(e.max()), "max_at": [float(x[i]), float(x[j])],
           "rms_interior_C": float(np.sqrt(np.mean(e[interior] ** 2))), "rms_corner_C": float(np.sqrt(np.mean(e[corner] ** 2))),
           "rms_rest_C": float(np.sqrt(np.mean(e[~corner] ** 2)))}
    if seeds:
        v = [M(t)["rel_L2"] for t in seeds]
        rec["rel_L2_seeds"] = {"min": min(v), "max": max(v), "gmean": float(np.exp(np.mean(np.log(v))))}
    rows.append(rec)
(HERE / "data" / "summary_atlas.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))

# ------------------------------------------------------------------ Fig. 5 · atlas
levels = np.arange(-4, 1.51, 0.5)                      # log10 |ΔT| (°C): 1e-4 … 30 °C
norm = BoundaryNorm(levels, cmap_error.N, extend="both")
ncol, nrow = 5, 4
fig, axs = plt.subplots(nrow, ncol, figsize=(183 * MM, 160 * MM))
order = RUNS
for k, ax in enumerate(axs.flat):
    if k >= len(order):
        ax.set_axis_off()
        continue
    lab, tag, grp, _ = order[k]
    r = rows[k]
    e = err_field(tag)
    cf = ax.contourf(X, Y, np.log10(np.maximum(e, 1e-8)), levels=levels, cmap=cmap_error, norm=norm, extend="both")
    ax.contour(X, Y, np.log10(np.maximum(e, 1e-8)), levels=[-1.0], colors=[C["parca_mandalina"]], linewidths=0.5)  # 0.1 °C eş-çizgisi
    ax.plot(*r["max_at"], marker="x", ms=3, mew=0.8, color=C["parca_mandalina"], clip_on=False, zorder=5)
    ax.set(aspect="equal", xlim=(0, 1), ylim=(0, 1), xticks=[], yticks=[])
    for s in ax.spines.values():
        s.set_visible(True); s.set_color(GCOL[grp]); s.set_linewidth(1.4)
    ax.set_title(lab, fontsize=6, color=INK, pad=2)
    ax.text(0.5, -0.04, f"L$_2$ {r['rel_L2']:.1e} · maks {r['max_C']:.2g} °C", transform=ax.transAxes,
            ha="center", va="top", fontsize=5, color=INK)
# group labels on the left of each row start
starts = {}
for k, (_, _, grp, _) in enumerate(order):
    starts.setdefault(grp, k)
for grp, k in starts.items():
    ax = axs.flat[k]
    ax.text(0.0, 1.2, grp, transform=ax.transAxes, fontsize=6, fontweight="bold", color=GCOL[grp], ha="left", va="bottom")
ax = axs.flat[len(order)]
cax = ax.inset_axes([0.1, 0.62, 0.8, 0.09])
cb = fig.colorbar(cf, cax=cax, orientation="horizontal", ticks=[-4, -3, -2, -1, 0, 1])
cb.set_ticklabels(["10$^{-4}$", "10$^{-3}$", "0.01", "0.1", "1", "10"])
cb.ax.tick_params(labelsize=5)
cb.set_label("|T$_{seri}$ − T| (°C)", fontsize=6)
ax.text(0.1, 0.30, "turuncu çizgi: 0.1 °C\n× : en büyük hata\ntohum 0 · 201 × 201 ağ", transform=ax.transAxes, fontsize=5, color=MUTED, va="top")
fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.03, wspace=0.12, hspace=0.42)
save_figure(fig, HERE / "figures" / "fig05_error_atlas")
plt.close(fig)

# ------------------------------------------------------------------ Fig. 6 · ranking
srt = sorted(rows, key=lambda r: r["rel_L2"])
fig, axs = plt.subplots(1, 2, figsize=(183 * MM, 100 * MM), sharey=True, gridspec_kw={"width_ratios": [1.25, 1]})
yy = np.arange(len(srt))[::-1]
ax = axs[0]
for y, r in zip(yy, srt):
    col = GCOL[r["group"]]
    ax.scatter(r["rel_L2"], y, s=14, color=col, zorder=3, linewidths=0)
    if "rel_L2_seeds" in r:
        sd = r["rel_L2_seeds"]
        ax.plot([sd["min"], sd["max"]], [y, y], color=col, lw=1.2, alpha=0.45, zorder=2, solid_capstyle="round")
b = next(r for r in rows if r["tag"] == "uniform")["rel_L2_seeds"]
ax.axvspan(b["min"], b["max"], color=C["krom"], zorder=0)
ax.set_xscale("log")
ax.set_yticks(yy, [f"{r['label']}" for r in srt], fontsize=5.5)
for t, r in zip(ax.get_yticklabels(), srt):
    t.set_color(GCOL[r["group"]])
ax.set_xlabel("bağıl L$_2$ hata  (nokta: tohum 0 · çizgi: 3 tohum aralığı)")
ax.set_title("gri bant: forward düzgün, 3 tohum", fontsize=6, color=MUTED, pad=3)
fig.text(0.005, 0.975, "a", fontsize=8, fontweight="bold", color=INK, va="top")
ax = axs[1]
for y, r in zip(yy, srt):
    col = GCOL[r["group"]]
    ax.scatter(r["rms_corner_C"], y, s=14, color=col, zorder=3, linewidths=0)
    ax.scatter(r["rms_rest_C"], y, s=14, facecolor="white", edgecolor=col, lw=0.8, zorder=3)
    ax.plot([r["rms_rest_C"], r["rms_corner_C"]], [y, y], color=col, lw=0.6, alpha=0.5, zorder=2)
ax.set_xscale("log")
ax.set_xlabel("RMS |ΔT| (°C)")
ax.scatter([], [], s=14, color=INK, label="köşe bölgesi (r < 0.1)")
ax.scatter([], [], s=14, facecolor="white", edgecolor=INK, lw=0.8, label="alanın geri kalanı")
ax.legend(loc="upper right", fontsize=5.5, handletextpad=0.2)
ax.set_title("hata nerede: köşe mi, alan mı?", fontsize=6, color=MUTED, pad=3)
panel_letter(ax, "b", dx=-0.06, dy=1.01)
fig.tight_layout(pad=0.4, w_pad=1.0)
save_figure(fig, HERE / "figures" / "fig06_error_ranking")
plt.close(fig)

for r in srt:
    print(f"{r['label']:18s} {r['group']:30s} L2 {r['rel_L2']:.2e}  maks {r['max_C']:.3f} °C @ {r['max_at']}  "
          f"RMS köşe {r['rms_corner_C']:.3f} · geri kalan {r['rms_rest_C']:.4f} °C")
