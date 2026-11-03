"""
Adım 6 deney planı: hibrit PINN (fizik + seyrek gürültülü ölçüm).
Koşuları sırayla çalıştırır; metrics.json'u olan koşuyu atlar (kaldığı yerden devam eder).

    python hybrid_runs.py           # hepsini koşar (2 CPU'da ~3 saat)
    python hybrid_runs.py --list    # planı gösterir

Veri yok (N_d = 0) karşılaştırması Ders 02'nin düzgün koşularıdır: uniform, uniform_s1, uniform_s2.
"""

import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

PLAN = {}
for s in (0, 1, 2):
    for n in (5, 20, 80):                                  # sensör sayısı (düzgün yerleşim, σ = 0.01)
        PLAN[f"hyb_n{n}_s{s}"] = f"--n-data {n} --noise 0.01 --where uniform --seed {s}"
    PLAN[f"hyb_mu100_s{s}"] = f"--n-data 20 --noise 0.01 --where uniform --mu 100 --seed {s}"   # veri ağırlığı
    for w in ("corner", "bottom"):                         # yerleşim (N_d = 20, σ = 0.01)
        PLAN[f"hyb_{w}_s{s}"] = f"--n-data 20 --noise 0.01 --where {w} --seed {s}"
for sig, name in ((0.0, "clean"), (0.05, "noisy05")):     # gürültü düzeyi (N_d = 20, tohum 0)
    PLAN[f"hyb_{name}"] = f"--n-data 20 --noise {sig} --where uniform --seed 0"

if __name__ == "__main__":
    if "--list" in sys.argv:
        for t, a in PLAN.items():
            print(f"{'✓' if (HERE / 'runs' / t / 'metrics.json').exists() else ' '} {t:16s} {a}")
        sys.exit()
    t_all = time.perf_counter()
    for tag, extra in PLAN.items():
        if (HERE / "runs" / tag / "metrics.json").exists():
            print(f"[atla] {tag}", flush=True)
            continue
        t0 = time.perf_counter()
        print(f"[başla] {tag}: {extra}", flush=True)
        log = HERE / f"runs_{tag}.log"
        with open(log, "w") as f:
            r = subprocess.run([sys.executable, str(HERE / "pinn_hybrid.py"), "--tag", tag, *extra.split()],
                               stdout=f, stderr=subprocess.STDOUT, cwd=HERE)
        status = "bitti" if r.returncode == 0 else f"HATA ({r.returncode}), bkz. {log.name}"
        print(f"[{status}] {tag}  {time.perf_counter() - t0:.0f} s", flush=True)
    print(f"toplam {(time.perf_counter() - t_all) / 60:.1f} dk", flush=True)
