"""
Adım 7 — klasik referans: aynı ters problemi seri çözüm + en küçük karelerle çözmek.

İleri model θ(x; Bi) burada analitik seri çözümdür (README, Adım 3). Ölçümler FDM (N = 201) düğümlerinden gelir,
yani veriyi üreten model ile tersine çevirmede kullanılan model farklıdır ("ters suç" yapılmaz).

    Bi* = argmin_Bi  Σ_i (θ(x_i; Bi) − θ_i^ölçüm)²                  (tek değişkenli, sınırlı arama, ln Bi'de)

Belirlenebilirlik. Duyarlılık S(x) = ∂θ/∂Bi, sensör konumlarında Fisher bilgisini verir:
    I(Bi) = Σ_i S(x_i)² / σ²      →      σ_Bi ≥ σ / sqrt(Σ_i S(x_i)²)      (Cramér–Rao alt sınırı)
Monte Carlo: aynı sensör konumları, 400 bağımsız gürültü gerçeklemesi → Bi* dağılımı.

Çalıştırma:
    python inverse_classical.py         # data/inverse_classical.json (+ duyarlılık haritası .npz)
"""

import json
import time
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar

from fdm_solver import BI_DEFAULT
from pinn_hybrid import sensors

HERE = Path(__file__).resolve().parent


def theta_series(X, Bi, n_terms=1500):
    """Seri çözüm dağınık noktalarda: X (n, 2) = (ξ, η)."""
    xi, eta = X[:, 0:1], X[:, 1:2]
    a = np.pi * np.arange(1, 2 * n_terms, 2)[None, :]
    ratio = np.exp(-a * eta) * (1 - np.exp(-2 * a * (1 - eta))) / (1 + np.exp(-2 * a))
    return 1.0 - ((4 * Bi / a) / (a + Bi * np.tanh(a)) * np.sin(a * xi) * ratio).sum(1)


def sensitivity(X, Bi=BI_DEFAULT, d=1e-4):
    """S = ∂θ/∂Bi, merkezi fark."""
    return (theta_series(X, Bi * (1 + d)) - theta_series(X, Bi * (1 - d))) / (2 * Bi * d)


def fit_bi(X, y):
    f = lambda b: np.sum((theta_series(X, np.exp(b)) - y) ** 2)   # noqa: E731
    r = minimize_scalar(f, bounds=(np.log(1e-2), np.log(1e3)), method="bounded", options={"xatol": 1e-9})
    return float(np.exp(r.x)), float(r.fun)


def crlb(X, sigma, Bi=BI_DEFAULT):
    S = sensitivity(X, Bi)
    return float(sigma / np.sqrt(np.sum(S ** 2)))


# PINN koşularıyla aynı sensör kümeleri (n, yerleşim, σ, tohum)
CONFIGS = {f"n{n}_{w}": (n, w) for n in (5, 20, 80) for w in ("uniform",)}
CONFIGS.update({"n20_top": (20, "top"), "n20_bottom": (20, "bottom"), "n20_corner": (20, "corner")})

if __name__ == "__main__":
    t0 = time.perf_counter()
    rng = np.random.default_rng(7)
    out = {"Bi_true": BI_DEFAULT, "sigma": 0.01, "configs": {}}
    for name, (n, where) in CONFIGS.items():
        rows = {}
        for s in (0, 1, 2):
            X, y, clean = sensors(n, where, 0.01, s)
            bi, _ = fit_bi(X, y)
            bi_clean, _ = fit_bi(X, clean)
            # Monte Carlo: aynı konumlar, yeni gürültü
            mc = np.array([fit_bi(X, clean + rng.normal(0, 0.01, n))[0] for _ in range(400 if s == 0 else 100)])
            rows[f"s{s}"] = {"Bi_est": bi, "Bi_est_clean": bi_clean, "crlb_sigma_Bi": crlb(X, 0.01),
                             "sum_S2": float(np.sum(sensitivity(X) ** 2)),
                             "mc_mean": float(mc.mean()), "mc_std": float(mc.std(ddof=1)),
                             "mc_p05": float(np.percentile(mc, 5)), "mc_p95": float(np.percentile(mc, 95))}
            print(f"{name:12s} s{s}: Bi* = {bi:.4f}  (gürültüsüz {bi_clean:.4f})  CRLB σ = {rows[f's{s}']['crlb_sigma_Bi']:.3f}"
                  f"  MC σ = {mc.std(ddof=1):.3f}", flush=True)
        out["configs"][name] = {"n": n, "where": where, "seeds": rows}
    # gürültü düzeyi (N_d = 20, düzgün, tohum 0)
    X, _, clean = sensors(20, "uniform", 0.0, 0)
    out["noise_scan"] = {}
    for sig in (0.0, 0.01, 0.05):
        _, y, _ = sensors(20, "uniform", sig, 0)
        out["noise_scan"][str(sig)] = {"Bi_est": fit_bi(X, y)[0], "crlb_sigma_Bi": crlb(X, sig) if sig else 0.0}

    # duyarlılık haritası (figür için): S(ξ, η) 101 × 101
    x = np.linspace(0, 1, 101)
    XX, YY = np.meshgrid(x, x)
    P = np.column_stack([XX.ravel(), YY.ravel()])
    S = sensitivity(P).reshape(101, 101)
    np.savez_compressed(HERE / "data" / "sensitivity_Bi.npz", x=x, S=S)
    # profil: ∂θ/∂Bi eğrisi ve θ(Bi) alt orta nokta — "Bi büyüdükçe bilgi azalır"
    bis = np.geomspace(0.1, 100, 61)
    pm = np.array([[0.5, 0.05]])
    out["bi_curve"] = {"Bi": bis.tolist(), "theta_mid": [float(theta_series(pm, b)[0]) for b in bis],
                       "S_mid": [float(sensitivity(pm, b)[0]) for b in bis]}
    out["S_max"] = float(np.abs(S).max())
    out["t_s"] = round(time.perf_counter() - t0, 1)
    (HERE / "data" / "inverse_classical.json").write_text(json.dumps(out, indent=1))
    print(f"süre {out['t_s']} s")
