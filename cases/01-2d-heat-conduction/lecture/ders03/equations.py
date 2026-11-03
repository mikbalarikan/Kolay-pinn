"""
Ders 03 denklemleri — tek kaynak (LaTeX).
    python lecture/ders03/equations.py   ->  lecture/ders03/assets/eq/  (PNG + OMML, index.json)
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
from kolay_pinn.mathtex import render_set  # noqa: E402

INK = "0D161F"

EQ = {
    # sözlük
    "g_data": r"\mathcal{L}_{\mathrm{veri}} = \frac{1}{N_d}\sum_{i=1}^{N_d}\big(\hat\theta(\mathbf{x}_i) - \theta_i^{\mathrm{ö}}\big)^2",
    "g_mu": r"\mu\,\mathcal{L}_{\mathrm{veri}}",
    "g_noise": r"\varepsilon_i \sim \mathcal{N}(0, \sigma^2)",
    "g_model": r"\varepsilon_{\mathrm{model}} = \mathrm{RMS}\big(\hat\theta - \theta\big)",
    "g_wrong": r"\mathrm{Bi}_{\mathrm{model}} \neq \mathrm{Bi}",
    "g_filter": r"\mathrm{RMS}(\hat\theta - \theta^{\mathrm{ö}}) \approx \sigma",
    # 1 · veriyi kayba ekle
    "hybrid": r"\mathcal{L} = \underbrace{\mathcal{L}_{\mathrm{PDE}} + \lambda\,\mathcal{L}_{\mathrm{Robin}}}_{\text{fizik}} \;+\; \mu\,\underbrace{\frac{1}{N_d}\sum_{i=1}^{N_d}\big(\hat\theta(\mathbf{x}_i) - \theta_i^{\mathrm{ö}}\big)^2}_{\text{veri}}",
    "meas": r"\theta_i^{\mathrm{ö}} = \theta_{\mathrm{FDM}}(\mathbf{x}_i) + \varepsilon_i, \qquad \varepsilon_i \sim \mathcal{N}(0, \sigma^2)",
    "sigma_C": r"\sigma = 0.01 \;\Longleftrightarrow\; \sigma_T = \sigma\,(T_w - T_\infty) = 0.5\ ^\circ\mathrm{C}",
    "scale": r"\mathcal{L}_{\mathrm{veri}} \approx \sigma^2 = 10^{-4} \quad\ll\quad \mathcal{L}_{\mathrm{Robin}} \approx 0.08",
    # 2 · doğru fizik
    "criterion": r"\frac{\sigma}{\sqrt{N_d}} \;<\; \varepsilon_{\mathrm{model}} \quad\Rightarrow\quad \text{veri bilgi taşır}",
    # 3 · yanlış fizik
    "wrong": r"\mathcal{L}_{\mathrm{Robin}} = \frac{1}{N_b}\sum_{m}\Big(\frac{\partial\hat\theta}{\partial\eta} - \underbrace{2}_{\mathrm{Bi}_{\mathrm{model}}}\,\hat\theta\Big)^2, \qquad \text{ölçümler: } \mathrm{Bi} = 4.895",
    # önizleme: Ders 04 ters problem
    "pv_inverse": r"\min_{\mathbf{w},\,\mathrm{Bi}}\ \mathcal{L}_{\mathrm{PDE}} + \lambda\,\mathcal{L}_{\mathrm{Robin}}(\mathrm{Bi}) + \mu\,\mathcal{L}_{\mathrm{veri}}",
}

SIZES = {"hybrid": 20, "meas": 20, "sigma_C": 18, "scale": 19, "criterion": 22, "wrong": 17, "pv_inverse": 22}
DECK = {k: {"tex": v, "size": SIZES.get(k, 17 if k.startswith("g_") else 18)} for k, v in EQ.items()}

if __name__ == "__main__":
    idx = render_set(DECK, HERE / "assets" / "eq", color=INK)
    print(f"{len(idx)} denklem -> {HERE / 'assets' / 'eq'}")
    for k, v in idx.items():
        print(f"  {k:12s} {v['w']:.2f} x {v['h']:.2f} in")
