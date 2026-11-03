"""
Ders 01 denklemleri — tek kaynak (LaTeX).
Deste:  python lecture/equations.py           -> lecture/assets/eq/  (PNG + OMML, index.json)
Rapor:  make_report.py aynı sözlüğü küçük boyutta (11 pt) dizer.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from kolay_pinn.mathtex import render_set  # noqa: E402

INK, PLAN, CELIK, WHITE = "0D161F", "15A5B4", "39659B", "FFFFFF"

# --- kavram sözlüğü ---------------------------------------------------------------
GLOSSARY = {
    "g_laplace": r"\nabla^2 T = \frac{\partial^2 T}{\partial x^2} + \frac{\partial^2 T}{\partial y^2} = 0",
    "g_dirichlet": r"T = T_w \quad \text{(sınırda)}",
    "g_robin": r"-k\,\frac{\partial T}{\partial n} = h\,\left(T - T_\infty\right)",
    "g_biot": r"\mathrm{Bi} = \frac{h\,L}{k}",
    "g_fd": r"\frac{\partial^2 T}{\partial x^2} \approx \frac{T_{i+1} - 2T_i + T_{i-1}}{\Delta x^2}",
    "g_nondim": r"\theta = \frac{T - T_\infty}{T_w - T_\infty}",
}

# --- 1 · problem ---------------------------------------------------------------------
PROBLEM = {
    "re": r"\mathrm{Re}_L = \frac{U L}{\nu}",
    "nu": r"\overline{\mathrm{Nu}}_L = 0.664\,\mathrm{Re}_L^{1/2}\,\mathrm{Pr}^{1/3}",
    "h": r"\bar h = \frac{\overline{\mathrm{Nu}}_L\, k_f}{L}",
    "bi_num": r"\mathrm{Bi} = \frac{\bar h\,L}{k} = \frac{2398 \times 0.1}{49} \approx 4.89",
}

# --- 2 · boyutsuzlaştırma ------------------------------------------------------------
NONDIM = {
    "scales": r"\begin{aligned} \theta &= \frac{T - T_\infty}{T_w - T_\infty} \\[4pt] \xi &= \frac{x}{L}, \qquad \eta = \frac{y}{L} \\[4pt] T &= 20 + 50\,\theta \quad [^\circ\mathrm{C}] \end{aligned}",
    "nd_problem": r"\begin{aligned} &\frac{\partial^2\theta}{\partial\xi^2} + \frac{\partial^2\theta}{\partial\eta^2} = 0, && (\xi,\eta) \in [0,1]^2 \\[4pt] &\theta = 1, && \xi = 0,\ \xi = 1,\ \eta = 1 \\[4pt] &\frac{\partial\theta}{\partial\eta} = \mathrm{Bi}\,\theta, && \eta = 0 \end{aligned}",
    "rob1": r"k\,\frac{\partial T}{\partial y} = h\,\left(T - T_\infty\right)",
    "rob2": r"\frac{k\,\Delta T}{L}\,\frac{\partial \theta}{\partial \eta} = h\,\Delta T\,\theta",
    "rob3": r"\frac{\partial \theta}{\partial \eta} = \frac{h L}{k}\,\theta = \mathrm{Bi}\,\theta",
    "rob2_sub": r"T - T_\infty = \Delta T\,\theta, \qquad y = L\,\eta",
    "loss_w": r"\mathcal{L} = \mathcal{L}_{\mathrm{PDE}} + \lambda\,\mathcal{L}_{\mathrm{Robin}}, \qquad \lambda \approx 1",
    "domain": r"\xi,\ \eta \in [0, 1]",
}

# --- 3 · FDM ve analitik -------------------------------------------------------------
FDM = {
    "st_in": r"\theta_{i+1,j} + \theta_{i-1,j} + \theta_{i,j+1} + \theta_{i,j-1} - 4\,\theta_{i,j} = 0",
    "st_ghost": r"\theta_{i,-1} = \theta_{i,1} - 2\Delta\,\mathrm{Bi}\,\theta_{i,0}",
    "st_bot": r"\theta_{i-1,0} + \theta_{i+1,0} + 2\,\theta_{i,1} - \left(4 + 2\Delta\,\mathrm{Bi}\right)\theta_{i,0} = 0",
    "series": r"\theta(\xi,\eta) = 1 - \sum_{n\ \mathrm{tek}} A_n\,\sin(n\pi\xi)\,\sinh\!\big(n\pi(1-\eta)\big)",
    "an": r"A_n = \frac{4\,\mathrm{Bi}/(n\pi)}{n\pi\cosh(n\pi) + \mathrm{Bi}\,\sinh(n\pi)}",
    "phi": r"\theta = 1 - \varphi",
    "an_rob": r"\left.\frac{\partial\theta}{\partial\eta}\right|_{\eta=0} = \mathrm{Bi}\,\theta \;\Rightarrow\; A_n",
    "ratio": r"\frac{\sinh\!\big(n\pi(1-\eta)\big)}{\cosh(n\pi)} = e^{-n\pi\eta}\,\frac{1 - e^{-2n\pi(1-\eta)}}{1 + e^{-2n\pi}}",
    "qprime": r"Q' = \bar h\,L\,(T_w - T_\infty)\int_0^1 \theta(\xi, 0)\,d\xi",
    "order": r"\|e\| \propto \Delta^{p}",
}

# --- Ders 02 önizleme ----------------------------------------------------------------
PREVIEW = {
    "pv_in": r"(\xi,\ \eta)",
    "pv_hard": r"\hat\theta = 1 + \xi(1-\xi)(1-\eta)\,\mathcal{N}(\xi,\eta)",
    "pv_loss": r"\mathcal{L} = \big\|\nabla^2\hat\theta\big\|^2 + \Big\|\frac{\partial\hat\theta}{\partial\eta} - \mathrm{Bi}\,\hat\theta\Big\|^2_{\eta=0}",
}

# per-group sizes (pt) for the deck
DECK = {}
for group, size in [(GLOSSARY, 17), (PROBLEM, 20), (NONDIM, 22), (FDM, 20), (PREVIEW, 20)]:
    for k, v in group.items():
        spec = {"tex": v} if isinstance(v, str) else dict(v)
        spec.setdefault("size", size)
        DECK[k] = spec
for k in ("rob2_sub", "qprime", "an_rob", "domain"):
    DECK[k]["size"] = 16
DECK["series"]["size"] = 24
DECK["an"]["size"] = 24
DECK["ratio"]["size"] = 18
# big coloured stat values
DECK.update({
    "v_th1": {"tex": r"\theta = 1", "size": 36, "color": CELIK},
    "v_th0": {"tex": r"\theta = 0", "size": 36, "color": CELIK},
    "v_thm": {"tex": r"\theta(0.5,\,0) = 0.33", "size": 36, "color": PLAN},
})

ALL_TEX = {k: v["tex"] for k, v in DECK.items()}

if __name__ == "__main__":
    idx = render_set(DECK, HERE / "assets" / "eq", color=INK)
    print(f"{len(idx)} denklem -> {HERE / 'assets' / 'eq'}")
