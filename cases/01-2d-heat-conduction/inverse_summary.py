"""
Adım 7 özeti: ters PINN — Bi ölçümlerden geri bulunabilir mi, hangi koşulda?
Önce: python inverse_classical.py ; python inverse_runs.py
Çıktı: figures/fig05_inverse.{pdf,svg,png}, data/summary_inverse.json

Köşe yanlılığı modeli. Köşe çelişkisi Robin kaybına Bi ile büyüyen bir taban ekler (Adım 5): L_köşe ≈ c Bi².
Veri terimi en iyi Bi* (klasik en küçük kareler, aynı veri) çevresinde μ·m·(Bi − Bi*)², m = ortalama S² sensörlerde.
Toplamın minimumu:
    Bi_PINN ≈ μ m Bi* / (c + μ m)
c, Adım 5'in üç tohumlu forward koşularından (son Robin kaybı / Bi²) alınır — ters koşulardan bağımsız bir öngörü.
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from kolay_pinn.style import C, INK, MM, MUTED, panel_letter, save_figure, use_style  # noqa: E402
from pinn_hybrid import sensors  # noqa: E402

use_style()
M = lambda tag: json.loads((HERE / "runs" / tag / "metrics.json").read_text())  # noqa: E731
H = lambda tag: np.load(HERE / "runs" / tag / "history.npz")  # noqa: E731
CL = json.loads((HERE / "data" / "inverse_classical.json").read_text())
BI = CL["Bi_true"]
SEEDS = (0, 1, 2)
KEYS = ["Bi_est", "Bi_rel_err", "rel_L2", "rel_L2_interior", "Q_rel_err_est", "final_loss", "final_robin", "final_data",
        "data_rmse_vs_noisy", "data_rmse_vs_clean", "t_total_s"]

# --- köşe tabanı sabiti c (Adım 5, veri yok, δ = 0 ve δ = 0.02)
c_corner = float(np.mean([M(t)["final_robin"] / M(t)["Bi"] ** 2 for t in ("uniform", "uniform_s1", "uniform_s2")]))
c_skip = float(np.mean([M(t)["final_robin"] / M(t)["Bi"] ** 2 for t in ("skip", "skip_s1", "skip_s2")]))
cl0 = CL["configs"]["n20_uniform"]["seeds"]["s0"]
m0 = cl0["sum_S2"] / 20                                          # ortalama S², N_d = 20, tohum 0
predict = lambda mu, c: mu * m0 * cl0["Bi_est"] / (c + mu * m0)  # noqa: E731

MU = [1, 10, 100, 1000]
MU_RUNS = {mu: f"inv_mu{mu}" for mu in MU}
MU_SKIP = {1: "inv_skip_mu1", 100: "inv_n20_s0", 1000: "inv_skip_mu1000"}
GROUPS = {                                                       # önerilen ayar (δ = 0.02, μ = 100)
    "5 düzgün": ("n5_uniform", [f"inv_n5_s{s}" for s in SEEDS]),
    "20 düzgün": ("n20_uniform", [f"inv_n20_s{s}" for s in SEEDS]),
    "80 düzgün": ("n80_uniform", [f"inv_n80_s{s}" for s in SEEDS]),
    "20 üst yarı": ("n20_top", [f"inv_top_s{s}" for s in SEEDS]),
    "20 alt şerit": ("n20_bottom", [f"inv_bottom_s{s}" for s in SEEDS]),
}
EXTRA = {"σ = 0": "inv_clean", "σ = 0.05": "inv_noisy05", "Bi₀ = 0.5": "inv_init0.5", "Bi₀ = 8": "inv_init8",
         "ısınma, μ = 1": "inv_skip_mu1_warm"}


def row(tag):
    return {k: M(tag).get(k) for k in KEYS}


S = {"Bi_true": BI, "c_corner": c_corner, "c_skip": c_skip, "m_n20_s0": m0, "Bi_classical_n20_s0": cl0["Bi_est"],
     "mu_scan": {str(mu): row(t) | {"Bi_pred": predict(mu, c_corner)} for mu, t in MU_RUNS.items()},
     "mu_scan_skip": {str(mu): row(t) | {"Bi_pred": predict(mu, c_skip)} for mu, t in MU_SKIP.items()},
     "groups": {}, "extra": {g: row(t) for g, t in EXTRA.items()}}
S["extra"]["σ = 0"]["Bi_classical"] = CL["noise_scan"]["0.0"]["Bi_est"]
S["extra"]["σ = 0.05"]["Bi_classical"] = CL["noise_scan"]["0.05"]["Bi_est"]
S["extra"]["σ = 0.05"]["crlb_sigma_Bi"] = CL["noise_scan"]["0.05"]["crlb_sigma_Bi"]
for g, (cfg, tags) in GROUPS.items():
    cs = CL["configs"][cfg]["seeds"]
    runs = [row(t) | {"Bi_classical": cs[f"s{s}"]["Bi_est"], "crlb": cs[f"s{s}"]["crlb_sigma_Bi"]}
            for s, t in zip(SEEDS, tags)]
    gap = np.array([r["Bi_est"] - r["Bi_classical"] for r in runs])
    err = np.array([r["Bi_est"] - BI for r in runs])
    S["groups"][g] = {"runs": runs, "mean_abs_rel_err": float(np.mean(np.abs(err)) / BI),
                      "mean_abs_gap_to_classical": float(np.mean(np.abs(gap))),
                      "mean_crlb": float(np.mean([r["crlb"] for r in runs])),
                      "gap_over_crlb": float(np.mean(np.abs(gap)) / np.mean([r["crlb"] for r in runs])),
                      "rel_L2_gmean": float(np.exp(np.mean(np.log([r["rel_L2"] for r in runs]))))}
rec = S["groups"]["20 düzgün"]
S["verdict"] = {
    "naive_mu1_Bi": S["mu_scan"]["1"]["Bi_est"],
    "mu100_noskip_Bi": S["mu_scan"]["100"]["Bi_est"], "mu100_noskip_pred": S["mu_scan"]["100"]["Bi_pred"],
    "recommended_n20_mean_abs_rel_err": rec["mean_abs_rel_err"],
    "recommended_gap_over_crlb": {g: v["gap_over_crlb"] for g, v in S["groups"].items()},
    "top_vs_bottom_crlb_ratio": S["groups"]["20 üst yarı"]["mean_crlb"] / S["groups"]["20 alt şerit"]["mean_crlb"],
    "init_spread": abs(S["extra"]["Bi₀ = 0.5"]["Bi_est"] - S["extra"]["Bi₀ = 8"]["Bi_est"]),
    "wrong_physics_step6_rel_L2": 0.0918, "recommended_rel_L2_gmean": rec["rel_L2_gmean"],
}
(HERE / "data" / "summary_inverse.json").write_text(json.dumps(S, indent=1, ensure_ascii=False))

# ------------------------------------------------------------------ Fig. 5
fig, axs = plt.subplots(2, 2, figsize=(183 * MM, 122 * MM))


def truth(ax, label=True):
    ax.axhline(BI, color=INK, lw=0.7, ls=(0, (3, 2)), zorder=2)
    if label:
        ax.text(0.99, BI * 1.04, "gerçek Bi = 4.895", ha="right", va="bottom", fontsize=5.5, color=INK,
                transform=ax.get_yaxis_transform())


# a — Bi'nin eğitim boyunca yolu
ax = axs[0, 0]
TRAJ = [("inv_mu1", "δ = 0, μ = 1", C["titanyum"], "-"), ("inv_mu100", "δ = 0, μ = 100", C["parca_mandalina"], "-"),
        ("inv_n20_s0", "δ = 0.02, μ = 100", C["plan"], "-"), ("inv_init0.5", "δ = 0.02, μ = 100, Bi₀ = 0.5", C["plan"], ":"),
        ("inv_init8", "δ = 0.02, μ = 100, Bi₀ = 8", C["plan"], "--")]
for tag, lab, col, ls in TRAJ:
    h = H(tag)
    ax.plot(h["it"] + 1, h["Bi"], color=col, ls=ls, lw=1.0, label=lab)
ax.axvline(6000, color=MUTED, lw=0.5)
ax.text(6150, 0.06, "L-BFGS", fontsize=5.5, color=MUTED)
truth(ax, label=False)
ax.set_yscale("log")
ax.set_ylim(0.04, 12)
ax.set_xlim(0, None)
ax.set_xlabel("iterasyon")
ax.set_ylabel("öğrenilen Bi")
ax.legend(loc="lower left", fontsize=5.5, handlelength=2.2)
ax.set_title("saf ayarda Bi çöker; δ = 0.02 ve μ = 100 ile her başlangıç aynı değere gider", fontsize=6, color=MUTED, pad=3)
panel_letter(ax, "a", dx=-0.17, dy=1.02)

# b — μ taraması ve köşe yanlılığı öngörüsü
ax = axs[0, 1]
mus = np.geomspace(0.7, 1500, 200)
ax.plot(mus, predict(mus, c_corner), color=C["parca_mandalina"], lw=0.8, alpha=0.6,
        label="öngörü, δ = 0:  μm Bi*/(c + μm)")
ax.scatter(MU, [S["mu_scan"][str(m)]["Bi_est"] for m in MU], s=18, color=C["parca_mandalina"], zorder=3,
           linewidths=0, label="PINN, δ = 0")
ms = list(MU_SKIP)
ax.scatter(ms, [S["mu_scan_skip"][str(m)]["Bi_est"] for m in ms], s=18, color=C["plan"], zorder=3, linewidths=0,
           label="PINN, δ = 0.02")
lo, hi = cl0["Bi_est"] - cl0["crlb_sigma_Bi"], cl0["Bi_est"] + cl0["crlb_sigma_Bi"]
ax.axhspan(lo, hi, color=C["krom"], zorder=0)
ax.text(0.99, hi * 1.03, "klasik Bi* ± σ$_{CR}$ (aynı veri)", ha="right", va="bottom", fontsize=5.5, color=MUTED,
        transform=ax.get_yaxis_transform())
truth(ax, label=False)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_ylim(0.04, 12)
ax.set_xlabel("veri ağırlığı μ  (N$_d$ = 20, σ = 0.01, tohum 0)")
ax.set_ylabel("öğrenilen Bi")
ax.legend(loc="lower right", fontsize=5.5)
ax.set_title("köşe tabanı Bi'yi aşağı çeker; yanlılık önceden hesaplanabilir", fontsize=6, color=MUTED, pad=3)
panel_letter(ax, "b", dx=-0.17, dy=1.02)

# c — duyarlılık haritası ∂θ/∂Bi ve sensör yerleşimleri
ax = axs[1, 0]
sd = np.load(HERE / "data" / "sensitivity_Bi.npz")
im = ax.imshow(-sd["S"], origin="lower", extent=(0, 1, 0, 1), cmap="Blues", vmin=0)
cs = ax.contour(sd["x"], sd["x"], -sd["S"], levels=[0.002, 0.01, 0.03], colors=INK, linewidths=0.4)
ax.clabel(cs, fontsize=5, fmt="%.3f")
for where, col, mk, lab in (("top", C["lila"], "^", "üst yarı"), ("bottom", C["parca_mandalina"], "s", "alt şerit"),
                            ("uniform", "white", "o", "düzgün")):
    X, _, _ = sensors(20, where, 0.01, 0)
    ax.scatter(X[:, 0], X[:, 1], s=9, marker=mk, facecolor=col, edgecolor=INK, lw=0.4, zorder=3, label=lab)
ax.set_xlabel("ξ"); ax.set_ylabel("η")
ax.set_aspect("equal")
cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
cb.set_label("−∂θ/∂Bi", fontsize=6)
ax.legend(loc="upper center", fontsize=5.5, ncol=3, bbox_to_anchor=(0.5, -0.17), handletextpad=0.1)
ax.set_title("Bi'nin izi soğutulan yüzeyde; üst yarı neredeyse kör", fontsize=6, color=MUTED, pad=3)
panel_letter(ax, "c", dx=-0.25, dy=1.02)

# d — PINN ve klasik, aynı veriyle (δ = 0.02, μ = 100)
ax = axs[1, 1]
names = list(GROUPS)
for i, g in enumerate(names):
    for k, r in enumerate(S["groups"][g]["runs"]):
        x = i + (k - 1) * 0.16
        ax.errorbar(x + 0.04, r["Bi_classical"], yerr=r["crlb"], fmt="o", ms=3, mfc="white", mec=C["titanyum"],
                    ecolor=C["titanyum"], elinewidth=0.6, capsize=1.2, zorder=3,
                    label="klasik ± σ$_{CR}$" if i == 0 and k == 0 else None)
        ax.scatter(x - 0.04, r["Bi_est"], s=12, color=C["plan"], zorder=4, linewidths=0,
                   label="PINN" if i == 0 and k == 0 else None)
truth(ax)
ax.set_xticks(range(len(names)), [g.replace(" ", "\n", 1) for g in names], fontsize=6)
ax.set_xlim(-0.5, len(names) - 0.5)
ax.set_ylabel("öğrenilen Bi")
ax.set_xlabel("sensör sayısı ve yerleşim (σ = 0.01; her nokta bir tohum)")
ax.legend(loc="lower left", fontsize=5.5)
ax.set_title("δ = 0.02, μ = 100: PINN klasik tahminin gürültü sınırı içinde", fontsize=6, color=MUTED, pad=3)
panel_letter(ax, "d", dx=-0.17, dy=1.02)

fig.tight_layout(pad=0.4, w_pad=1.4, h_pad=1.4)
save_figure(fig, HERE / "figures" / "fig05_inverse")
plt.close(fig)

print(f"c (δ = 0) = {c_corner:.2e}, c (δ = 0.02) = {c_skip:.2e}, m = {m0:.2e}, Bi* = {cl0['Bi_est']:.4f}")
for k in ("mu_scan", "mu_scan_skip"):
    print(k, {mu: f"{v['Bi_est']:.3f} (öngörü {v['Bi_pred']:.3f})" for mu, v in S[k].items()})
for g, v in S["groups"].items():
    print(f"{g:14s}", " ".join(f"{r['Bi_est']:.3f}/{r['Bi_classical']:.3f}±{r['crlb']:.3f}" for r in v["runs"]),
          f"| L2 {v['rel_L2_gmean']:.1e} | fark/σCR {v['gap_over_crlb']:.2f}")
print("ek:", {g: f"{v['Bi_est']:.3f}" for g, v in S["extra"].items()})
print(json.dumps(S["verdict"], indent=1, ensure_ascii=False))
