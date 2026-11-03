"""
Adım 6 özeti: hibrit PINN — veri ne zaman işe yarar?
Önce: python hybrid_runs.py   (veri yok karşılaştırması: uniform, uniform_s1, uniform_s2)
Çıktı: figures/fig04_hybrid.{pdf,svg,png}, data/summary_hybrid.json
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
SEEDS = (0, 1, 2)
KEYS = ["rel_L2", "rel_L2_interior", "max_err", "Q_rel_err", "final_loss", "final_data",
        "data_rmse_vs_noisy", "data_rmse_vs_clean", "noise_rms", "t_total_s"]
BASE = ["uniform", "uniform_s1", "uniform_s2"]           # N_d = 0, Ders 02

# grup adı -> tohum koşuları
COUNT = {"0": BASE} | {str(n): [f"hyb_n{n}_s{s}" for s in SEEDS] for n in (5, 20, 80)}
CONFIG = {
    "düzgün, μ = 1": [f"hyb_n20_s{s}" for s in SEEDS],
    "köşe, μ = 1": [f"hyb_corner_s{s}" for s in SEEDS],
    "alt şerit, μ = 1": [f"hyb_bottom_s{s}" for s in SEEDS],
    "düzgün, μ = 100": [f"hyb_mu100_s{s}" for s in SEEDS],
}
NOISE = {0.0: "hyb_clean", 0.01: "hyb_n20_s0", 0.05: "hyb_noisy05"}           # tohum 0, N_d = 20
WRONG = {"veri yok": "wrongbi_n0", "20 sensör\nμ = 1": "wrongbi_n20_mu1",
         "20 sensör\nμ = 100": "wrongbi_n20_mu100", "80 sensör\nμ = 100": "wrongbi_n80_mu100"}


def stats(tags):
    out = {}
    for k in KEYS:
        v = np.array([M(t).get(k, 0.0) for t in tags], dtype=float)
        out[k] = {"mean": float(v.mean()), "std": float(v.std(ddof=1)) if v.size > 1 else 0.0,
                  "gmean": float(np.exp(np.log(np.maximum(v, 1e-300)).mean())),
                  "min": float(v.min()), "max": float(v.max()), "values": v.tolist()}
    return out


S = {"count": {g: stats(t) for g, t in COUNT.items()},
     "config": {g: stats(t) for g, t in CONFIG.items()},
     "noise": {str(s): {k: M(t).get(k, 0.0) for k in KEYS} for s, t in NOISE.items()},
     "wrong_bi": {g.replace("\n", " "): {k: M(t).get(k, 0.0) for k in KEYS} | {"bi_model": M(t)["bi_model"]}
                  for g, t in WRONG.items()},
     "correct_physics_seed0": {k: M("uniform")[k] for k in ("rel_L2", "rel_L2_interior", "max_err", "Q_rel_err")}}

eps = []
for t in BASE:                                                   # veri yokken modelin RMS hatası (tüm alan)
    p = np.load(HERE / "runs" / t / "prediction.npz")
    eps.append(float(np.sqrt(np.mean((p["theta"] - p["theta_exact"]) ** 2))))
S["eps_model_no_data"] = {"values": eps, "gmean": float(np.exp(np.mean(np.log(eps))))}
b = S["count"]["0"]["rel_L2"]
w = {g: v["rel_L2"] for g, v in S["wrong_bi"].items()}
S["verdict"] = {
    "baseline_rel_L2_range": [b["min"], b["max"]],
    "count_gmean_ratio_vs_none": {g: v["rel_L2"]["gmean"] / b["gmean"] for g, v in S["count"].items()},
    "config_gmean_ratio_vs_none": {g: v["rel_L2"]["gmean"] / b["gmean"] for g, v in S["config"].items()},
    "all_correct_physics_runs_inside_or_above_baseline_range":
        bool(all(min(v["rel_L2"]["values"]) >= 0.8 * b["min"] for v in list(S["count"].values()) + list(S["config"].values()))),
    "model_error_at_sensors_over_noise_n20_s0": S["noise"]["0.01"]["data_rmse_vs_clean"] / 0.01,
    "wrong_bi_no_data_over_correct": w["veri yok"] / S["correct_physics_seed0"]["rel_L2"],
    "wrong_bi_best_data_reduction": w["veri yok"] / min(v for g, v in w.items() if g != "veri yok"),
    "wrong_bi_best_over_correct": min(v for g, v in w.items() if g != "veri yok") / S["correct_physics_seed0"]["rel_L2"],
}
(HERE / "data" / "summary_hybrid.json").write_text(json.dumps(S, indent=1, ensure_ascii=False))

# ------------------------------------------------------------------ Fig. 4
fig, axs = plt.subplots(2, 2, figsize=(183 * MM, 118 * MM))
rng = np.random.default_rng(1)


def band(ax, label=True):
    ax.axhspan(b["min"], b["max"], color=C["krom"], zorder=0)
    if label:
        ax.text(0.98, b["min"] * 1.04, "veri yok · 3 tohum aralığı", ha="right", va="bottom", fontsize=5.5, color=MUTED,
                transform=ax.get_yaxis_transform())


def strip(ax, groups, colors):
    for i, (g, st) in enumerate(groups.items()):
        v = np.array(st["rel_L2"]["values"])
        ax.scatter(i + rng.uniform(-0.08, 0.08, v.size), v, s=12, color=colors[i], zorder=3, linewidths=0)
        ax.plot([i - 0.22, i + 0.22], [st["rel_L2"]["gmean"]] * 2, color=INK, lw=0.9, zorder=4)
    ax.set_yscale("log")
    ax.set_xlim(-0.5, len(groups) - 0.5)
    ax.set_ylabel("bağıl L$_2$ hata")


# a — sensör sayısı
ax = axs[0, 0]
band(ax)
strip(ax, S["count"], [C["titanyum"]] + [C["plan"]] * 3)
ax.set_xticks(range(4), ["0", "5", "20", "80"])
ax.set_xlabel("sensör sayısı $N_d$  (σ = 0.01, düzgün, μ = 1)")
ax.set_title("sensör sayısı hatayı tohum aralığının dışına taşımıyor", fontsize=6, color=MUTED, pad=3)
panel_letter(ax, "a", dx=-0.17, dy=1.02)

# b — yerleşim ve veri ağırlığı
ax = axs[0, 1]
band(ax)
strip(ax, S["config"], [C["plan"], C["parca_mandalina"], C["lila"], C["derin"]])
ax.set_xticks(range(4), [g.replace(", ", "\n") for g in CONFIG], fontsize=6)
ax.set_title("$N_d$ = 20: yerleşim fark etmiyor, μ = 100 bozuyor", fontsize=6, color=MUTED, pad=3)
panel_letter(ax, "b", dx=-0.17, dy=1.02)

# c — gürültü: model ölçüme değil gerçeğe yakın
ax = axs[1, 0]
sig = list(NOISE)
xs = np.arange(len(sig))
nz = [S["noise"][str(s)] for s in sig]
ax.scatter(xs, [n["data_rmse_vs_noisy"] for n in nz], s=16, facecolor="white", edgecolor=C["plan"], lw=0.8,
           zorder=3, label="ölçüme göre RMSE")
ax.scatter(xs, [n["data_rmse_vs_clean"] for n in nz], s=16, color=C["plan"], zorder=3, linewidths=0,
           label="gerçeğe (FDM) göre RMSE")
ax.scatter(xs, [n["noise_rms"] if n["noise_rms"] > 0 else np.nan for n in nz], marker="_", s=90, color=C["titanyum"],
           lw=1.0, zorder=2, label="gürültü düzeyi")
ax.set_yscale("log")
ax.set_xticks(xs, ["σ = 0", "σ = 0.01\n(≈ 0.5 °C)", "σ = 0.05\n(≈ 2.5 °C)"], fontsize=6)
ax.set_xlim(-0.5, len(sig) - 0.5)
ax.set_ylabel("sensörlerde θ RMSE")
ax.legend(loc="upper left", fontsize=5.5, handletextpad=0.2)
for x, n in zip(xs, nz):
    ax.text(x + 0.12, n["data_rmse_vs_clean"], f"L$_2$ {n['rel_L2']:.1e}", fontsize=5.5, color=INK, va="center")
ax.set_title("ağ gürültüyü ezberlemiyor: fizik onu süzüyor (tohum 0)", fontsize=6, color=MUTED, pad=3)
panel_letter(ax, "c", dx=-0.17, dy=1.02)

# d — yanlış fizik: veri burada işe yarar
ax = axs[1, 1]
names = list(WRONG)
vals = [S["wrong_bi"][g.replace("\n", " ")]["rel_L2"] for g in names]
cols = [C["titanyum"]] + [C["lila"]] * 3
ax.bar(range(len(names)), vals, width=0.55, color=cols, zorder=3)
ax.axhline(S["correct_physics_seed0"]["rel_L2"], color=INK, lw=0.7, ls=(0, (3, 2)), zorder=4)
ax.text(len(names) - 0.55, S["correct_physics_seed0"]["rel_L2"] * 0.85, "doğru fizik, veri yok (tohum 0)",
        ha="right", va="top", fontsize=5.5, color=INK, zorder=5, bbox=dict(fc="white", ec="none", pad=0.6))
ax.set_ylim(4e-4, 0.25)
for i, g in enumerate(names):
    q = S["wrong_bi"][g.replace("\n", " ")]["Q_rel_err"]
    ax.text(i, vals[i] * 1.12, f"Q hatası %{q * 100:.0f}", ha="center", fontsize=5.5, color=INK)
ax.set_yscale("log")
ax.set_xticks(range(len(names)), names, fontsize=6)
ax.set_ylabel("bağıl L$_2$ hata")
ax.set_title("model Bi = 2 sanıyor (gerçek 4.9): veri hatayı en çok 2 kat düşürüyor", fontsize=6, color=MUTED, pad=3)
panel_letter(ax, "d", dx=-0.17, dy=1.02)

fig.tight_layout(pad=0.4, w_pad=1.4, h_pad=1.2)
save_figure(fig, HERE / "figures" / "fig04_hybrid")
plt.close(fig)

fmt = lambda st: f"{st['rel_L2']['gmean']:.2e} [{st['rel_L2']['min']:.1e}, {st['rel_L2']['max']:.1e}]"  # noqa: E731
print("sensör sayısı:", json.dumps({g: fmt(v) for g, v in S["count"].items()}, indent=1, ensure_ascii=False))
print("yapılandırma:", json.dumps({g: fmt(v) for g, v in S["config"].items()}, indent=1, ensure_ascii=False))
print("gürültü:", json.dumps({s: {k: f"{v[k]:.2e}" for k in ("rel_L2", "data_rmse_vs_noisy", "data_rmse_vs_clean", "noise_rms")}
                              for s, v in S["noise"].items()}, indent=1))
print("yanlış Bi:", json.dumps({g: {k: f"{v[k]:.2e}" for k in ("rel_L2", "Q_rel_err", "data_rmse_vs_clean")}
                                for g, v in S["wrong_bi"].items()}, indent=1, ensure_ascii=False))
print(json.dumps(S["verdict"], indent=1, ensure_ascii=False))
