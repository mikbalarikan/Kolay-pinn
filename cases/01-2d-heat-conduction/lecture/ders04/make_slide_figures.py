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

from kolay_pinn.style import C, INK, MUTED, use_slide_style  # noqa: E402
from pinn_hybrid import sensors  # noqa: E402

use_slide_style()
OUT = HERE / "assets"
OUT.mkdir(exist_ok=True)
DPI = 220
S = json.loads((CASE / "data" / "summary_inverse.json").read_text())
CL = json.loads((CASE / "data" / "inverse_classical.json").read_text())
H = lambda tag: np.load(CASE / "runs" / tag / "history.npz")  # noqa: E731
RUN = lambda tag, f: np.load(CASE / "runs" / tag / f)  # noqa: E731
BI = S["Bi_true"]
T = lambda th: 20 + 50 * th  # noqa: E731


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=DPI)
    plt.close(fig)


def truth(ax, text=True):
    ax.axhline(BI, color=INK, lw=1.4, ls=(0, (4, 3)), zorder=2)
    if text:
        ax.text(0.99, BI * 1.06, "gerçek Bi = 4.895", ha="right", va="bottom", fontsize=12, color=INK,
                transform=ax.get_yaxis_transform())


for f in ("ti_light.png", "ti_dark.png", "maskot_normal.png", "maskot_mutlu.png"):
    shutil.copy(CASE / "lecture" / "assets" / f, OUT / f)

# 1 — tuzak: Bi'nin eğitim boyunca yolu ------------------------------------------------
fig, axs = plt.subplots(1, 2, figsize=(12.4, 4.4))
ax = axs[0]
for tag, lab, col in (("inv_mu1", "δ = 0, μ = 1", C["titanyum"]), ("inv_skip_mu1", "δ = 0.02, μ = 1", C["lila"]),
                      ("inv_mu100", "δ = 0, μ = 100", C["parca_mandalina"]), ("inv_n20_s0", "δ = 0.02, μ = 100", C["plan"])):
    h = H(tag)
    ax.plot(h["it"] + 1, h["Bi"], color=col, lw=2.2, label=lab)
ax.axvline(6000, color=MUTED, lw=1)
ax.text(6150, 0.06, "L-BFGS", fontsize=12, color=MUTED)
truth(ax)
ax.set_yscale("log"); ax.set_ylim(0.04, 10); ax.set_xlim(0, None)
ax.set_xlabel("iterasyon"); ax.set_ylabel("öğrenilen Bi")
ax.legend(loc="lower left", fontsize=12)
ax.set_title("Bi₀ = 2'den başlayan dört ayar", fontsize=14, color=MUTED)
ax = axs[1]
h = H("inv_mu1")
for k, lab, col in (("rob", "Robin", C["parca_mandalina"]), ("data", "veri (μ = 1)", C["lila"]), ("pde", "PDE", C["titanyum"])):
    ax.plot(h["it"] + 1, h[k], color=col, lw=2, label=lab)
ax.axhline(1e-4, color=INK, lw=1, ls=":")
ax.text(200, 1.2e-4, "σ² = 10⁻⁴", fontsize=12, color=INK)
ax.set_yscale("log"); ax.set_xlim(0, None)
ax.set_xlabel("iterasyon"); ax.set_ylabel("kayıp terimi")
ax.legend(loc="upper right", fontsize=12)
ax.set_title("δ = 0, μ = 1: Robin'i düşürmenin en ucuz yolu Bi → 0", fontsize=14, color=MUTED)
fig.tight_layout()
save(fig, "01_trap")

# 2 — köşe yanlılığı: μ taraması ve öngörü ------------------------------------------------
fig, ax = plt.subplots(figsize=(8.2, 4.6))
c, cs, m0, bstar = S["c_corner"], S["c_skip"], S["m_n20_s0"], S["Bi_classical_n20_s0"]
mus = np.geomspace(0.7, 1500, 200)
ax.plot(mus, mus * m0 * bstar / (c + mus * m0), color=C["parca_mandalina"], lw=2, alpha=0.6, label="öngörü (δ = 0)")
mu_k = [int(k) for k in S["mu_scan"]]
ax.scatter(mu_k, [S["mu_scan"][str(k)]["Bi_est"] for k in mu_k], s=90, color=C["parca_mandalina"], zorder=3,
           linewidths=0, label="PINN, δ = 0")
mu_s = [int(k) for k in S["mu_scan_skip"]]
ax.scatter(mu_s, [S["mu_scan_skip"][str(k)]["Bi_est"] for k in mu_s], s=90, color=C["plan"], zorder=3, linewidths=0,
           label="PINN, δ = 0.02")
cl0 = CL["configs"]["n20_uniform"]["seeds"]["s0"]
ax.axhspan(cl0["Bi_est"] - cl0["crlb_sigma_Bi"], cl0["Bi_est"] + cl0["crlb_sigma_Bi"], color=C["krom"], zorder=0)
truth(ax)
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylim(0.04, 10)
ax.set_xlabel("veri ağırlığı μ"); ax.set_ylabel("öğrenilen Bi")
ax.legend(loc="lower right", fontsize=12)
fig.tight_layout()
save(fig, "02_corner_bias")

# 3 — duyarlılık haritası + yerleşime göre Cramér–Rao sınırı -------------------------------
fig, axs = plt.subplots(1, 2, figsize=(12.4, 4.8), gridspec_kw={"width_ratios": [1.05, 1]})
ax = axs[0]
sd = np.load(CASE / "data" / "sensitivity_Bi.npz")
im = ax.imshow(-sd["S"], origin="lower", extent=(0, 1, 0, 1), cmap="Blues", vmin=0)
cn = ax.contour(sd["x"], sd["x"], -sd["S"], levels=[0.002, 0.01, 0.03], colors=INK, linewidths=1)
ax.clabel(cn, fontsize=11, fmt="%.3f")
for where, col, mk in (("top", C["lila"], "^"), ("bottom", C["parca_mandalina"], "s"), ("uniform", "white", "o")):
    X, _, _ = sensors(20, where, 0.01, 0)
    ax.scatter(X[:, 0], X[:, 1], s=40, marker=mk, facecolor=col, edgecolor=INK, lw=0.8, zorder=3)
ax.set_xlabel("ξ"); ax.set_ylabel("η"); ax.set_aspect("equal")
fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03).set_label("−∂θ/∂Bi")
ax = axs[1]
cfgs = [("n5_uniform", "5\ndüzgün", C["plan"]), ("n20_uniform", "20\ndüzgün", C["plan"]), ("n80_uniform", "80\ndüzgün", C["plan"]),
        ("n20_top", "20\nüst yarı", C["lila"]), ("n20_bottom", "20\nalt şerit", C["parca_mandalina"]),
        ("n20_corner", "20\nköşe", C["celik_mavisi"])]
v = [np.mean([CL["configs"][k]["seeds"][f"s{s}"]["crlb_sigma_Bi"] for s in (0, 1, 2)]) / BI * 100 for k, _, _ in cfgs]
ax.bar(range(len(cfgs)), v, color=[c for _, _, c in cfgs], width=0.6)
for i, val in enumerate(v):
    ax.text(i, val * 1.08, f"%{val:.1f}", ha="center", fontsize=12)
ax.set_yscale("log")
ax.set_xticks(range(len(cfgs)), [n for _, n, _ in cfgs], fontsize=12)
ax.set_ylabel("σ$_{CR}$ / Bi  (σ = 0.5 °C)")
ax.set_title("Cramér–Rao sınırı, 3 sensör kümesi ortalaması", fontsize=14, color=MUTED)
fig.tight_layout()
save(fig, "03_sensitivity")

# 4 — PINN ve klasik, aynı veriyle -------------------------------------------------------
fig, ax = plt.subplots(figsize=(12.4, 4.6))
names = list(S["groups"])
for i, g in enumerate(names):
    for k, r in enumerate(S["groups"][g]["runs"]):
        x = i + (k - 1) * 0.18
        ax.errorbar(x + 0.05, r["Bi_classical"], yerr=r["crlb"], fmt="o", ms=8, mfc="white", mec=C["titanyum"],
                    ecolor=C["titanyum"], elinewidth=1.4, capsize=3, zorder=3,
                    label="klasik (seri + en küçük kareler) ± σ$_{CR}$" if i == 0 and k == 0 else None)
        ax.scatter(x - 0.05, r["Bi_est"], s=70, color=C["plan"], zorder=4, linewidths=0,
                   label="PINN (δ = 0.02, μ = 100)" if i == 0 and k == 0 else None)
truth(ax)
ax.set_xticks(range(len(names)), names, fontsize=13)
ax.set_xlim(-0.5, len(names) - 0.5)
ax.set_ylabel("öğrenilen Bi")
ax.legend(loc="lower left", fontsize=12)
fig.tight_layout()
save(fig, "04_pinn_vs_classical")

# 5 — Ders 03'ün yanlış fiziği düzeldi: alt yüzey sıcaklığı ------------------------------
fig, ax = plt.subplots(figsize=(8.2, 4.4))
p = RUN("inv_n20_s0", "prediction.npz")
x = p["x"]
ax.plot(x, T(p["theta_exact"][0]), color=INK, lw=3.2, label="gerçek (seri, Bi = 4.895)")
pw = RUN("wrongbi_n20_mu100", "prediction.npz")
ax.plot(x, T(pw["theta"][0]), color=C["lila"], lw=2, ls="--", label="Ders 03: Bi = 2 sabit, 20 sensör, μ = 100")
ax.plot(x, T(p["theta"][0]), color=C["plan"], lw=2, label=f"Ders 04: Bi öğrenildi → {S['groups']['20 düzgün']['runs'][0]['Bi_est']:.2f}")
ax.set_xlabel("ξ  (alt yüzey, η = 0)"); ax.set_ylabel("T [°C]")
ax.set_xlim(0, 1)
ax.legend(loc="upper center", fontsize=12)
fig.tight_layout()
save(fig, "05_bottom_fixed")
print("slayt görselleri ->", OUT)
