"""
Adım 7 klasik taban: (1) duyarlılık ∂θ/∂Bi ve Cramér–Rao alt sınırı, (2) FDM + en küçük kareler ile Bi kestirimi.
PINN koşularıyla aynı sensörler (pinn_hybrid.sensors, aynı tohumlar).
Çıktı: data/inverse_classical.json
"""

import json
import time
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

from fdm_solver import BI_DEFAULT, solve_fdm
from pinn_hybrid import sensors

HERE = Path(__file__).resolve().parent
N, BI = 201, BI_DEFAULT
x, _, th0 = solve_fdm(N, BI)
h = 1e-3 * BI
S = (solve_fdm(N, BI + h)[2] - solve_fdm(N, BI - h)[2]) / (2 * h)       # ∂θ/∂Bi, (η, ξ) dizini
idx = {round(v, 6): i for i, v in enumerate(x)}


def node(X):
    return np.array([idx[round(a, 6)] for a in X[:, 1]]), np.array([idx[round(a, 6)] for a in X[:, 0]])


def crb(X, sigma):
    j, i = node(X)
    return float(sigma / np.sqrt(np.sum(S[j, i] ** 2)))                 # σ_Bi alt sınırı


def fit_fdm(X, y, bi0=1.0, Nfit=101):
    """FDM (Nfit) çözümünü sensörlere doğrusal enterpolasyonla taşı; log Bi üzerinde en küçük kareler."""
    from scipy.interpolate import RegularGridInterpolator
    n_eval = [0]

    def res(p):
        n_eval[0] += 1
        xf, _, th = solve_fdm(Nfit, float(np.exp(p[0])))
        return RegularGridInterpolator((xf, xf), th)(np.column_stack([X[:, 1], X[:, 0]])) - y

    t0 = time.perf_counter()
    r = least_squares(res, [np.log(bi0)], x_scale=1.0, xtol=1e-10)
    return float(np.exp(r.x[0])), time.perf_counter() - t0, n_eval[0]


out = {"Bi_true": BI, "sensitivity": {"max": float(np.abs(S).max()), "bottom_mid": float(S[0, N // 2]),
                                      "center": float(S[N // 2, N // 2]), "top_half_max": float(np.abs(S[N // 2:]).max())},
       "cases": {}}
np.save(HERE / "data" / "sensitivity_dtheta_dBi.npy", S)
cases = [(n, w, sig) for w in ("uniform", "bottom", "top", "corner") for n in (5, 20, 80) for sig in (0.01,)] + \
        [(20, "uniform", 0.0), (20, "uniform", 0.05)]
for n, w, sig in cases:
    key = f"{w}_n{n}_s{sig}"
    rec = {"crb_seeds": [], "fdm_ls_Bi": [], "fdm_ls_time_s": []}
    for seed in (0, 1, 2):
        X, y, _ = sensors(n, w, sig, seed, BI)
        rec["crb_seeds"].append(crb(X, max(sig, 1e-12)) if sig > 0 else 0.0)
        bi, t, ne = fit_fdm(X, y)
        rec["fdm_ls_Bi"].append(bi); rec["fdm_ls_time_s"].append(t)
    b = np.array(rec["fdm_ls_Bi"])
    rec["crb_rel"] = float(np.mean(rec["crb_seeds"]) / BI)
    rec["fdm_ls_rel_err"] = (np.abs(b - BI) / BI).tolist()
    out["cases"][key] = rec
    print(f"{key:22s} CRB σ_Bi/Bi = %{100 * rec['crb_rel']:6.2f} · FDM-LS Bi = {np.round(b, 3)} "
          f"(hata %{100 * np.mean(rec['fdm_ls_rel_err']):.2f}) · {np.mean(rec['fdm_ls_time_s']):.2f} s")
(HERE / "data" / "inverse_classical.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out["sensitivity"], indent=1))
