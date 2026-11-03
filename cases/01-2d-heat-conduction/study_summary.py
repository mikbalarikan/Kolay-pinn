"""
Sağlamlık çalışmasının özeti: tohum değişkenliği + kapasite / eğitim süresi.
Önce: python study_runs.py   (ve seed 0 koşuları: uniform, corner, skip)
Çıktı: figures/fig03_robustness.{pdf,svg,png}, data/summary_study.json
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from kolay_pinn.style import C, INK, MM, MUTED, panel_letter, save_figure, use_style  # noqa: E402

use_style()
M = lambda tag: json.loads((HERE / "runs" / tag / "metrics.json").read_text())  # noqa: E731

GROUPS = {  # strateji -> tohum koşuları
    "düzgün": ["uniform", "uniform_s1", "uniform_s2"],
    "köşe dışlama": ["skip", "skip_s1", "skip_s2"],
    "köşe sıklaştırma": ["corner", "corner_s1", "corner_s2"],
}
COL = {"düzgün": C["plan"], "köşe dışlama": C["lila"], "köşe sıklaştırma": C["parca_mandalina"]}
CAP = {  # temel ayara göre tek değişiklik (tohum 0)
    "4×50, temel": "uniform",
    "uzun L-BFGS (6000)": "long",
    "geniş 4×100": "wide4x100",
    "derin 8×50": "deep8x50",
}
KEYS = ["rel_L2", "rel_L2_interior", "max_err", "Q_rel_err", "final_loss", "t_total_s"]

S = {"seeds": {}, "capacity": {}}
for g, tags in GROUPS.items():
    vals = {k: np.array([M(t)[k] for t in tags]) for k in KEYS}
    S["seeds"][g] = {k: {"mean": float(v.mean()), "std": float(v.std(ddof=1)), "min": float(v.min()),
                         "max": float(v.max()), "values": v.tolist()} for k, v in vals.items()}
for name, tag in CAP.items():
    m = M(tag)
    S["capacity"][name] = {k: m[k] for k in KEYS} | {"n_params": None}
# parameter counts
for name, (w, d) in {"4×50, temel": (50, 4), "uzun L-BFGS (6000)": (50, 4), "geniş 4×100": (100, 4), "derin 8×50": (50, 8)}.items():
    S["capacity"][name]["n_params"] = 2 * w + w + (d - 1) * (w * w + w) + w + 1

u, k, s = (S["seeds"][g]["rel_L2"] for g in ("düzgün", "köşe sıklaştırma", "köşe dışlama"))
S["verdict"] = {
    "corner_vs_uniform_ratio_of_means": k["mean"] / u["mean"],
    "corner_worse_in_every_seed": bool(k["min"] > u["max"]),
    "skip_vs_uniform_ratio_of_means": s["mean"] / u["mean"],
    "skip_uniform_ranges_overlap": bool(not (s["min"] > u["max"] or s["max"] < u["min"])),
    "loss_ratio_uniform_over_skip": S["seeds"]["düzgün"]["final_loss"]["mean"] / S["seeds"]["köşe dışlama"]["final_loss"]["mean"],
    "uniform_cv_rel_L2": u["std"] / u["mean"],
}
(HERE / "data" / "summary_study.json").write_text(json.dumps(S, indent=1, ensure_ascii=False))

# ------------------------------------------------------------------ Fig. 3
fig, axs = plt.subplots(1, 3, figsize=(183 * MM, 62 * MM), gridspec_kw={"width_ratios": [1, 1, 1.25]})
rng = np.random.default_rng(1)
for ax, key, ylab in [(axs[0], "rel_L2", "bağıl L$_2$ hata"), (axs[1], "final_loss", "son toplam kayıp")]:
    for i, g in enumerate(GROUPS):
        v = np.array(S["seeds"][g][key]["values"])
        ax.scatter(i + rng.uniform(-0.08, 0.08, v.size), v, s=12, color=COL[g], zorder=3, linewidths=0)
        ax.plot([i - 0.22, i + 0.22], [np.exp(np.log(v).mean())] * 2, color=INK, lw=0.9, zorder=4)
    ax.set_yscale("log")
    ax.set_xticks(range(len(GROUPS)), [g.replace("köşe ", "köşe\n") for g in GROUPS], fontsize=6)
    ax.set_xlim(-0.5, len(GROUPS) - 0.5)
    ax.set_ylabel(ylab)
panel_letter(axs[0], "a", dx=-0.38, dy=1.02)
panel_letter(axs[1], "b", dx=-0.38, dy=1.02)
axs[0].set_title("3 tohum; çizgi: geometrik ortalama", fontsize=6, color=MUTED, pad=3)
axs[1].set_title("kayıp ile hata ayrışıyor", fontsize=6, color=MUTED, pad=3)

# c — capacity / training time vs error (seed spread of baseline shaded)
ax = axs[2]
ub = S["seeds"]["düzgün"]["rel_L2"]
ax.axhspan(ub["min"], ub["max"], color=C["krom"], zorder=0)
ax.text(0.98, ub["min"] * 1.06, "4×50 · 3 tohum aralığı", ha="right", fontsize=5.5, color=MUTED, transform=ax.get_yaxis_transform())
names = list(CAP)
for i, n in enumerate(names):
    c = S["capacity"][n]
    ax.scatter(i, c["rel_L2"], s=16, color=C["plan"], zorder=3, linewidths=0)
    ax.scatter(i, c["rel_L2_interior"], s=16, facecolor="white", edgecolor=C["plan"], lw=0.8, zorder=3)
    ax.text(i, c["rel_L2"] * 1.25, f"{c['t_total_s'] / 60:.0f} dk", ha="center", fontsize=5.5, color=INK)
ax.set_yscale("log")
ax.set_xticks(range(len(names)), [n.replace(" (", "\n(").replace(", ", "\n") for n in names], fontsize=5.5)
ax.set_xlim(-0.5, len(names) - 0.5)
ax.set_ylabel("bağıl L$_2$ hata")
ax.scatter([], [], s=16, color=C["plan"], label="tüm alan")
ax.scatter([], [], s=16, facecolor="white", edgecolor=C["plan"], lw=0.8, label="iç bölge")
ax.legend(loc="upper left", fontsize=5.5, handletextpad=0.2)
panel_letter(ax, "c", dx=-0.3, dy=1.02)
fig.tight_layout(pad=0.4, w_pad=1.2)
save_figure(fig, HERE / "figures" / "fig03_robustness")
plt.close(fig)

print(json.dumps({g: {k: f"{S['seeds'][g][k]['mean']:.2e} ± {S['seeds'][g][k]['std']:.1e}" for k in ("rel_L2", "rel_L2_interior", "Q_rel_err", "final_loss")} for g in GROUPS}, indent=1, ensure_ascii=False))
print(json.dumps({n: {k: (f"{v:.2e}" if isinstance(v, float) else v) for k, v in c.items() if k in ("rel_L2", "rel_L2_interior", "max_err", "t_total_s", "n_params")} for n, c in S["capacity"].items()}, indent=1, ensure_ascii=False))
print(json.dumps(S["verdict"], indent=1))
