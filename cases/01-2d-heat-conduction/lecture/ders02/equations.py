"""
Ders 02 denklemleri — tek kaynak (LaTeX).
    python lecture/ders02/equations.py   ->  lecture/ders02/assets/eq/  (PNG + OMML, index.json)
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
from kolay_pinn.mathtex import render_set  # noqa: E402

INK, PLAN, CELIK = "0D161F", "15A5B4", "39659B"

EQ = {
    # sözlük
    "g_mlp": r"\mathcal{N}(\mathbf{x}) = W_4\,\sigma\big(W_3\,\sigma(\cdots\sigma(W_1\mathbf{x} + b_1)\cdots)\big) + b_4",
    "g_tanh": r"\sigma(z) = \tanh z",
    "g_ad": r"\frac{\partial \hat\theta}{\partial \xi},\ \frac{\partial^2 \hat\theta}{\partial \xi^2} \quad \text{(kesin, ağdan)}",
    "g_col": r"\{(\xi_k, \eta_k)\}_{k=1}^{N_r}",
    "g_hard": r"\hat\theta = g + d\,\mathcal{N}",
    "g_lbfgs": r"\mathbf{w}_{k+1} = \mathbf{w}_k - \alpha_k H_k \nabla\mathcal{L}",
    # 1 · ağ ve katı kısıt
    "residual": r"r(\xi,\eta) = \frac{\partial^2\hat\theta}{\partial\xi^2} + \frac{\partial^2\hat\theta}{\partial\eta^2} \;\to\; 0",
    "hard": r"\hat\theta(\xi,\eta) = 1 + \underbrace{\xi\,(1-\xi)\,(1-\eta)}_{d(\xi,\eta)}\;\mathcal{N}(\xi,\eta)",
    "hard_check": r"\xi = 0,\ \xi = 1,\ \eta = 1:\quad d = 0 \;\Rightarrow\; \hat\theta = 1",
    "relu_dd": r"\sigma(z) = \max(0, z) \;\Rightarrow\; \sigma''(z) = 0 \;\Rightarrow\; \nabla^2 \mathcal{N} \equiv 0",
    # 2 · kayıp ve eğitim
    "lap_ad": r"\nabla^2\hat\theta = \frac{\partial}{\partial\xi}\!\left(\frac{\partial\hat\theta}{\partial\xi}\right) + \frac{\partial}{\partial\eta}\!\left(\frac{\partial\hat\theta}{\partial\eta}\right)",
    "loss": r"\mathcal{L}(\mathbf{w}) = \frac{1}{N_r}\sum_{k=1}^{N_r} \big(\nabla^2\hat\theta(\mathbf{x}_k)\big)^2 + \frac{\lambda}{N_b}\sum_{m=1}^{N_b} \Big(\frac{\partial\hat\theta}{\partial\eta} - \mathrm{Bi}\,\hat\theta\Big)^2_{(\xi_m, 0)}",
    "loss_short": r"\mathcal{L} = \mathcal{L}_{\mathrm{PDE}} + \lambda\,\mathcal{L}_{\mathrm{Robin}}, \qquad \lambda = 1",
    "adam_lr": r"\alpha_t = 10^{-3} \cdot 0.1^{\,t / T_{\mathrm{Adam}}}",
    "conflict": r"\underbrace{\left.\frac{\partial\theta}{\partial\eta}\right|_{\xi=0} = 0}_{\text{yan duvar: } \theta \equiv 1} \qquad\text{ama}\qquad \underbrace{\frac{\partial\theta}{\partial\eta} = \mathrm{Bi}\,\theta = \mathrm{Bi}}_{\text{Robin, köşede}}",
    "nr": r"N_r = 4096",
    "nb": r"N_b = 256",
    "lam1": r"\lambda = 1",
    # 3 · doğrulama
    "relL2": r"\varepsilon_{L_2} = \frac{\|\hat\theta - \theta_{\mathrm{seri}}\|_2}{\|\theta_{\mathrm{seri}}\|_2}",
    "qprime": r"Q' = \bar h\,L\,(T_w - T_\infty)\int_0^1 \hat\theta(\xi, 0)\,d\xi",
    "corner": r"r = \sqrt{\xi^2 + \eta^2} \sim \text{log-düzgün}\,[10^{-3},\ 0.2]",
    # önizleme: Ders 03 hibrit
    "pv_hybrid": r"\mathcal{L} = \mathcal{L}_{\mathrm{PDE}} + \lambda\,\mathcal{L}_{\mathrm{Robin}} + \mu\,\frac{1}{N_d}\sum_{i=1}^{N_d} \big(\hat\theta(\mathbf{x}_i) - \theta_i^{\mathrm{ölçüm}}\big)^2",
}

SIZES = {"loss": 20, "pv_hybrid": 20, "g_mlp": 15, "g_ad": 15, "g_lbfgs": 16, "hard": 24, "residual": 22,
         "relu_dd": 18, "conflict": 19, "nr": 26, "nb": 26, "lam1": 26, "lap_ad": 20, "hard_check": 16, "corner": 16, "adam_lr": 18}
DECK = {k: {"tex": v, "size": SIZES.get(k, 18 if not k.startswith("g_") else 17)} for k, v in EQ.items()}

if __name__ == "__main__":
    idx = render_set(DECK, HERE / "assets" / "eq", color=INK)
    print(f"{len(idx)} denklem -> {HERE / 'assets' / 'eq'}")
    for k, v in idx.items():
        print(f"  {k:12s} {v['w']:.2f} x {v['h']:.2f} in")
