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
    "g_param": r"\mathrm{Bi} = e^{s}, \quad s \in \mathbb{R}",
    "g_sens": r"S(\mathbf{x}) = \frac{\partial\theta}{\partial\,\mathrm{Bi}}",
    "g_crb": r"\sigma_{\mathrm{Bi}} \ge \frac{\sigma}{\sqrt{\sum_i S(\mathbf{x}_i)^2}}",
    "g_ls": r"\min_{\mathrm{Bi}} \sum_i \big(\theta_{\mathrm{FDM}}(\mathbf{x}_i;\mathrm{Bi}) - \theta_i^{\mathrm{ö}}\big)^2",
    "g_ident": r"S(\mathbf{x}) \approx 0 \;\Rightarrow\; \text{ölçüm Bi'yi görmez}",
    "g_corner": r"r_{\mathrm{Robin}}(0,0) = -\mathrm{Bi}",
    # 1 · Bi'yi parametre yap
    "inverse": r"\min_{\mathbf{w},\,s}\ \mathcal{L}_{\mathrm{PDE}} + \lambda\,\frac{1}{N_b}\sum_m\Big(\frac{\partial\hat\theta}{\partial\eta} - e^{s}\,\hat\theta\Big)^2 + \mu\,\frac{1}{N_d}\sum_{i=1}^{N_d}\big(\hat\theta(\mathbf{x}_i) - \theta_i^{\mathrm{ö}}\big)^2",
    "grad_s": r"\frac{\partial\mathcal{L}}{\partial s} = \mathrm{Bi}\,\frac{\partial\mathcal{L}}{\partial\,\mathrm{Bi}} \qquad \text{(göreli adım: } \Delta s \approx \Delta\mathrm{Bi}/\mathrm{Bi})",
    # 2 · bilgi
    "fisher": r"I(\mathrm{Bi}) = \frac{1}{\sigma^2}\sum_{i=1}^{N_d} S(\mathbf{x}_i)^2, \qquad \sigma_{\mathrm{Bi}} \ge I^{-1/2} = \frac{\sigma}{\sqrt{\sum_i S(\mathbf{x}_i)^2}}",
    "crb_scale": r"\frac{\sigma_{\mathrm{Bi}}}{\mathrm{Bi}} \approx \frac{\sigma}{\mathrm{Bi}\,\bar S\,\sqrt{N_d}}",
    # 3 · köşe
    "corner": r"\eta = 0,\ \xi \to 0: \quad \frac{\partial\hat\theta}{\partial\eta} \to 0,\ \ \hat\theta \to 1 \;\Rightarrow\; r_{\mathrm{Robin}} \to -\mathrm{Bi}, \quad \frac{\partial r^2}{\partial\,\mathrm{Bi}} = 2\,\mathrm{Bi}\,\hat\theta^2 > 0",
    # önizleme
    "pv_param": r"\hat\theta(\xi, \eta;\ \mathrm{Bi}) \;\;\text{— tek ağ, her Bi için çözüm}",
}

SIZES = {"inverse": 17, "grad_s": 18, "fisher": 20, "crb_scale": 22, "corner": 16, "pv_param": 22}
DECK = {k: {"tex": v, "size": SIZES.get(k, 16 if k.startswith("g_") else 18)} for k, v in EQ.items()}

if __name__ == "__main__":
    idx = render_set(DECK, HERE / "assets" / "eq", color=INK)
    print(f"{len(idx)} denklem -> {HERE / 'assets' / 'eq'}")
    for k, v in idx.items():
        print(f"  {k:12s} {v['w']:.2f} x {v['h']:.2f} in")
