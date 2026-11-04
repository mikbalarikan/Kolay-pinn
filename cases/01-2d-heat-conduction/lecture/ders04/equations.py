"""
Ders 04 denklemleri — tek kaynak (LaTeX).
    python lecture/ders04/equations.py   ->  lecture/ders04/assets/eq/  (PNG + OMML, index.json)
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
from kolay_pinn.mathtex import render_set  # noqa: E402

INK = "0D161F"

EQ = {
    # sözlük
    "g_beta": r"\mathrm{Bi} = e^{\beta}",
    "g_sens": r"S(\mathbf{x}) = \frac{\partial\theta}{\partial\mathrm{Bi}}",
    "g_crlb": r"\sigma_{\mathrm{Bi}} \geq \frac{\sigma}{\sqrt{\sum_i S_i^2}}",
    "g_floor": r"\mathcal{L}_{\mathrm{köşe}} \approx c\,\mathrm{Bi}^2",
    "g_skip": r"\delta = 0.02",
    "g_ls": r"\mathrm{Bi}^{*} = \arg\min_{\mathrm{Bi}} \sum_i \big(\theta(\mathbf{x}_i;\mathrm{Bi}) - \theta_i^{\mathrm{ö}}\big)^2",
    # 1 · Bi'yi öğrenilecek parametre yap
    "inverse": r"\min_{\mathbf{w},\,\beta}\ \mathcal{L}_{\mathrm{PDE}}(\mathbf{w}) + \lambda\,\mathcal{L}_{\mathrm{Robin}}(\mathbf{w}, e^{\beta}) + \mu\,\mathcal{L}_{\mathrm{veri}}(\mathbf{w})",
    "robin_bi": r"\mathcal{L}_{\mathrm{Robin}} = \frac{1}{N_b}\sum_{m}\Big(\frac{\partial\hat\theta}{\partial\eta} - e^{\beta}\,\hat\theta\Big)^2_{(\xi_m,\,0)}, \qquad \beta_0 = \ln 2",
    "h_from_bi": r"h = \frac{k\,\mathrm{Bi}}{L}, \qquad Q' = h\,L\,(T_w - T_\infty)\int_0^1\hat\theta(\xi, 0)\,d\xi",
    # 2 · klasik referans ve belirlenebilirlik
    "classical": r"\mathrm{Bi}^{*} = \arg\min_{\mathrm{Bi}}\ \sum_{i=1}^{N_d}\big(\theta_{\mathrm{seri}}(\mathbf{x}_i;\mathrm{Bi}) - \theta_i^{\mathrm{ö}}\big)^2",
    "crlb": r"I(\mathrm{Bi}) = \frac{1}{\sigma^2}\sum_{i=1}^{N_d} S(\mathbf{x}_i)^2 \quad\Longrightarrow\quad \sigma_{\mathrm{Bi}} \;\geq\; \frac{\sigma}{\sqrt{\sum_i S(\mathbf{x}_i)^2}}",
    # 3 · köşe yanlılığı
    "corner": r"\mathcal{L}_{\mathrm{Robin}}\big|_{\text{köşe}} \approx c\,\mathrm{Bi}^2, \qquad \mu\,\mathcal{L}_{\mathrm{veri}} \approx \mu\,m\,(\mathrm{Bi} - \mathrm{Bi}^{*})^2 + \mathrm{sabit}",
    "bias": r"\mathrm{Bi}_{\mathrm{PINN}} \approx \frac{\mu\,m}{c + \mu\,m}\,\mathrm{Bi}^{*}, \qquad m = \frac{1}{N_d}\sum_i S(\mathbf{x}_i)^2",
    # önizleme: Ders 05 parametrik vekil
    "pv_param": r"\hat\theta(\xi, \eta, \mathrm{Bi}) \approx \theta, \qquad \mathrm{Bi} \in [0.5,\ 20]",
}

SIZES = {"inverse": 21, "robin_bi": 19, "h_from_bi": 18, "classical": 20, "crlb": 19, "corner": 18, "bias": 22,
         "pv_param": 22}
DECK = {k: {"tex": v, "size": SIZES.get(k, 17 if k.startswith("g_") else 18)} for k, v in EQ.items()}

if __name__ == "__main__":
    idx = render_set(DECK, HERE / "assets" / "eq", color=INK)
    print(f"{len(idx)} denklem -> {HERE / 'assets' / 'eq'}")
    for k, v in idx.items():
        print(f"  {k:12s} {v['w']:.2f} x {v['h']:.2f} in")
