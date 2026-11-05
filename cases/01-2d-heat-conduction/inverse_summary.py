"""
Adım 7 özeti: ters problem — Bi iç sıcaklıklardan ne kadar iyi geri bulunur?
Önce: python inverse_classical.py && python inverse_runs.py
Çıktı: figures/fig08_inverse.{pdf,svg,png}, data/summary_inverse.json
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
SEEDS = (0, 1, 2)
CL = json.loads((HERE / "data" / "inverse_classical.json").read_text())
BI = CL["Bi_true"]


def M(tag):
    p = HERE / "runs" / tag / "metrics.json"
    return json.loads(p.read_text()) if p.exists() else None


def H(tag):
    return np.load(HERE / "runs" / tag / "history.npz")


# grup -> (PINN koşuları, aynı sensörlerle klasik durum anahtarı)
GROUPS = {
    "temel\n20 düzgün": ([f"inv_base_s{s}" for s in SEEDS], "uniform_n20_s0.01"),
    "köşe dışlama\nyok": ([f"inv_noskip_s{s}" for s in SEEDS], "uniform_n20_s0.01"),
    "üst yarı": ([f"inv_top_s{s}" for s in SEEDS], "top_n20_s0.01"),
    "alt şerit": ([f"inv_bottom_s{s}" for s in SEEDS], "bottom_n20_s0.01"),
    "5 sensör": ([f"inv_n5_s{s}" for s in SEEDS], "uniform_n5_s0.01"),
    "80 sensör": ([f"inv_n80_s{s}" for s in SEEDS], "uniform_n80_s0.01"),
    "μ = 1": ([f"inv_mu1_s{s}" for s in SEEDS], "uniform_n20_s0.01"),
}
NOISE = {0.0: ("inv_clean", "uniform_n20_s0.0"), 0.01: ("inv_base_s0", "uniform_n20_s0.01"),
         0.05: ("inv_noisy05", "uniform_n20_s0.05")}
KEYS = ["Bi_hat", "Bi_rel_err", "rel_L2", "max_err", "Q_rel_err", "t_total_s", "data_rmse_vs_clean", "noise_rms"]


def rec(tag, ckey, seed):
    m = M(tag)
    if m is None:
        return None
    c = CL["cases"][ckey]
    return {k: m[k] for k in KEYS} | {"tag": tag, "fdm_ls_Bi": c["fdm_ls_Bi"][seed],
                                      "fdm_ls_rel_err": c["fdm_ls_rel_err"][seed],
                                      "crb_rel": c["crb_seeds"][seed] / BI}


S = {"Bi_true": BI, "groups": {}, "noise": {}, "start_bi10": None}
for g, (tags, ck) in GROUPS.items():
    runs = [r for s, t in zip(SEEDS, tags) if (r := rec(t, ck, s)) is not None]
    if not runs:
        continue
    e = np.array([r["Bi_rel_err"] for r in runs])
    S["groups"][g.replace("\n", " ")] = {
        "runs": runs, "classical_key": ck, "crb_rel": CL["cases"][ck]["crb_rel"],
        "pinn_rel_err_mean": float(e.mean()), "pinn_rel_err_rms": float(np.sqrt(np.mean(e ** 2))),
        "fdm_ls_rel_err_mean": float(np.mean([r["fdm_ls_rel_err"] for r in runs])),
        "pinn_minus_fdm_ls_mean": float(np.mean([r["Bi_hat"] - r["fdm_ls_Bi"] for r in runs])),
        "rel_L2_gmean": float(np.exp(np.mean(np.log([r["rel_L2"] for r in runs])))),
        "Q_rel_err_mean": float(np.mean([r["Q_rel_err"] for r in runs]))}
for sig, (t, ck) in NOISE.items():
    if (r := rec(t, ck, 0)) is not None:
        S["noise"][str(sig)] = r
if (m := M("inv_bi10")) is not None:
    S["start_bi10"] = {k: m[k] for k in KEYS} | {"bi0": m["bi0"], "same_as_bi0_1_seed0": M("inv_base_s0")["Bi_hat"]}

paired = [r for g in S["groups"].values() for r in g["runs"]]
ok = [r for g, v in S["groups"].items() if g.startswith(("temel", "üst", "alt", "5 ", "80 ")) for r in v["runs"]]
S["verdict"] = {
    "pinn_vs_fdm_ls_abs_diff_rel_median_skip": float(np.median([abs(r["Bi_hat"] - r["fdm_ls_Bi"]) / BI for r in ok])) if ok else None,
    "pinn_vs_fdm_ls_abs_diff_rel_max_skip": float(np.max([abs(r["Bi_hat"] - r["fdm_ls_Bi"]) / BI for r in ok])) if ok else None,
    "noskip_bias_mean": S["groups"].get("köşe dışlama yok", {}).get("pinn_minus_fdm_ls_mean"),
    "pinn_time_s_median": float(np.median([r["t_total_s"] for r in paired])),
    "fdm_ls_time_s_median": float(np.median(sum((CL["cases"][k]["fdm_ls_time_s"] for k in CL["cases"]), []))),
}
(HERE / "data" / "summary_inverse.json").write_text(json.dumps(S, indent=1, ensure_ascii=False))

# ------------------------------------------------------------------ Fig. 8
COL = {"temel 20 düzgün": C["plan"], "köşe dışlama yok": C["hata"], "üst yarı": C["parca_mandalina"],
       "alt şerit": C["lila"], "5 sensör": C["titanyum"], "80 sensör": C["celik_mavisi"], "μ = 1": C["gecti"]}
fig, axs = plt.subplots(2, 2, figsize=(183 * MM, 120 * MM))
rng = np.random.default_rng(3)

# a — PINN ile FDM + en küçük kareler aynı veriden aynı Bi'yi buluyor
ax = axs[0, 0]
lo, hi = 3.3, 5.6
ax.plot([lo, hi], [lo, hi], color=INK, lw=0.6, zorder=2)
ax.axhline(BI, color=MUTED, lw=0.5, ls="dotted", zorder=1)
ax.axvline(BI, color=MUTED, lw=0.5, ls="dotted", zorder=1)
for g, v in S["groups"].items():
    xs, ys = [r["fdm_ls_Bi"] for r in v["runs"]], [r["Bi_hat"] for r in v["runs"]]
    ax.scatter(xs, ys, s=14, color=COL[g], zorder=3, linewidths=0, label=g)
ax.set_xlim(lo, hi); ax.set_ylim(lo, hi); ax.set_aspect("equal")
ax.set_xlabel("klasik: FDM + en küçük kareler  $\\widehat{Bi}$")
ax.set_ylabel("PINN  $\\widehat{Bi}$")
ax.text(BI + 0.03, lo + 0.05, f"gerçek {BI:.2f}", fontsize=5.5, color=MUTED, rotation=90, va="bottom")
ax.legend(loc="upper left", fontsize=5.2, handletextpad=0.1, borderaxespad=0.3, labelspacing=0.25)
ax.set_title("aynı veri → aynı Bi; köşe dışlanmazsa PINN aşağı kayar", fontsize=6, color=MUTED, pad=3, loc="right")
panel_letter(ax, "a", dx=-0.3, dy=1.02)

# b — hata ve Cramér–Rao alt sınırı
ax = axs[0, 1]
names = list(S["groups"])
for i, g in enumerate(names):
    v = S["groups"][g]
    e = np.array([r["Bi_rel_err"] for r in v["runs"]]) * 100
    f = np.array([r["fdm_ls_rel_err"] for r in v["runs"]]) * 100
    ax.scatter(i - 0.12 + rng.uniform(-0.04, 0.04, e.size), e, s=13, color=COL[g], zorder=3, linewidths=0)
    ax.scatter(i + 0.12 + rng.uniform(-0.04, 0.04, f.size), f, s=13, facecolor="white", edgecolor=COL[g], lw=0.7, zorder=3)
    ax.plot([i - 0.32, i + 0.32], [100 * v["crb_rel"]] * 2, color=INK, lw=0.9, zorder=4)
ax.set_yscale("log")
ax.set_ylim(0.02, 60)
ax.set_xlim(-0.5, len(names) - 0.5)
ax.set_xticks(range(len(names)), [g.replace(" ", "\n", 1) if len(g) > 9 else g for g in names], fontsize=5.5)
ax.set_ylabel("|$\\widehat{Bi}$ − Bi| / Bi  (%)")
ax.scatter([], [], s=13, color=INK, linewidths=0, label="PINN")
ax.scatter([], [], s=13, facecolor="white", edgecolor=INK, lw=0.7, label="FDM + EKK")
ax.plot([], [], color=INK, lw=0.9, label="Cramér–Rao σ$_{Bi}$/Bi")
ax.legend(loc="upper right", fontsize=5.2, ncol=3, handletextpad=0.2, columnspacing=0.8, borderaxespad=0.3)
ax.set_title("σ = 0.01: hata ölçüm gürültüsünün izin verdiği düzeyde", fontsize=6, color=MUTED, pad=3)
panel_letter(ax, "b", dx=-0.17, dy=1.02)

# c — eğitim boyunca Bi
ax = axs[1, 0]
tr = [("inv_base_s0", C["plan"], "Bi₀ = 1, temel"), ("inv_bi10", C["celik_mavisi"], "Bi₀ = 10"),
      ("inv_noskip_s0", C["hata"], "köşe dışlama yok"), ("inv_top_s0", C["parca_mandalina"], "üst yarı")]
for t, col, lab in tr:
    if M(t) is None:
        continue
    h = H(t)
    ax.plot(h["it"], h["Bi"], color=col, lw=0.9, label=lab, zorder=3)
ax.axhline(BI, color=INK, lw=0.6, ls="dashed", zorder=2)
ax.axvline(6000, color=MUTED, lw=0.5, zorder=1)
ax.text(5900, 0.2, "Adam", ha="right", fontsize=5.5, color=MUTED)
ax.text(6100, 0.2, "L-BFGS", ha="left", fontsize=5.5, color=MUTED)
ax.text(200, BI * 1.06, f"gerçek Bi = {BI:.3f}", fontsize=5.5, color=INK)
ax.set_yscale("log")
ax.set_ylim(0.15, 14)
ax.set_xlabel("iterasyon")
ax.set_ylabel("$\\widehat{Bi}$ = e$^{s}$")
ax.legend(loc="upper right", fontsize=5.2, handletextpad=0.3, borderaxespad=0.3)
ax.set_title("Bi yavaş yükselir; son yaklaşmayı L-BFGS yapar", fontsize=6, color=MUTED, pad=3)
panel_letter(ax, "c", dx=-0.11, dy=1.02)

# d — gürültü düzeyi
ax = axs[1, 1]
sig = [s for s in NOISE if str(s) in S["noise"]]
xs = np.arange(len(sig))
for x, s in zip(xs, sig):
    r = S["noise"][str(s)]
    ax.scatter(x - 0.1, max(100 * r["Bi_rel_err"], 1e-3), s=18, color=C["plan"], zorder=3, linewidths=0)
    ax.scatter(x + 0.1, max(100 * r["fdm_ls_rel_err"], 1e-3), s=18, facecolor="white", edgecolor=C["plan"], lw=0.8, zorder=3)
    if r["crb_rel"] > 0:
        ax.plot([x - 0.3, x + 0.3], [100 * r["crb_rel"]] * 2, color=INK, lw=0.9, zorder=4)
    ax.text(x + 0.2, max(100 * r["Bi_rel_err"], 1e-3), f"Q %{100 * r['Q_rel_err']:.2f}", fontsize=5.5, color=INK, va="center")
ax.set_yscale("log")
ax.set_ylim(5e-3, 60)
ax.set_xlim(-0.5, len(sig) - 0.5)
ax.set_xticks(xs, [{0.0: "σ = 0", 0.01: "σ = 0.01\n(≈ 0.5 °C)", 0.05: "σ = 0.05\n(≈ 2.5 °C)"}[s] for s in sig], fontsize=6)
ax.set_ylabel("|$\\widehat{Bi}$ − Bi| / Bi  (%)")
ax.set_title("20 düzgün sensör, tohum 0: hata gürültüyle orantılı", fontsize=6, color=MUTED, pad=3)
panel_letter(ax, "d", dx=-0.17, dy=1.02)

fig.tight_layout(pad=0.4, w_pad=1.4, h_pad=1.2)
save_figure(fig, HERE / "figures" / "fig08_inverse")
plt.close(fig)

for g, v in S["groups"].items():
    print(f"{g:18s} PINN %{100 * v['pinn_rel_err_mean']:5.2f} · FDM-LS %{100 * v['fdm_ls_rel_err_mean']:5.2f} · "
          f"CRB %{100 * v['crb_rel']:5.2f} · PINN−LS {v['pinn_minus_fdm_ls_mean']:+.3f} · L2 {v['rel_L2_gmean']:.1e} · "
          f"Q %{100 * v['Q_rel_err_mean']:.2f}  ({len(v['runs'])} koşu)")
print(json.dumps(S["noise"], indent=1, ensure_ascii=False)[:1500])
print(json.dumps(S["verdict"], indent=1, ensure_ascii=False))
