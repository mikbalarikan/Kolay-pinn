"""
Adım 7 deney planı: ters PINN (Bi öğrenilir). Koşuları iki paralel işte çalıştırır (her biri 2 iş parçacığı);
metrics.json'u olan koşuyu atlar (kaldığı yerden devam eder).

    python inverse_runs.py           # hepsini koşar (4 CPU'da ~2 saat)
    python inverse_runs.py --list    # planı gösterir

Ortak: σ = 0.01, Bi₀ = 2, Adam 6000 → L-BFGS 2000. Önerilen ayar: köşe dışlama δ = 0.02 ve μ = 100.
"""

import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
REC = "--skip 0.02 --mu 100"                                     # önerilen ayar

PLAN = {}
for mu in (1, 10, 100, 1000):                                    # veri ağırlığı, köşe dışlama YOK → köşe yanlılığı
    PLAN[f"inv_mu{mu}"] = f"--n-data 20 --mu {mu} --seed 0"
for mu in (1, 1000):                                             # veri ağırlığı, köşe dışlama VAR (μ = 100: inv_n20_s0)
    PLAN[f"inv_skip_mu{mu}"] = f"--n-data 20 --skip 0.02 --mu {mu} --seed 0"
PLAN["inv_skip_mu1_warm"] = "--n-data 20 --skip 0.02 --mu 1 --warmup 2000 --seed 0"   # ısınma + en küçük kareler Bi
for s in (0, 1, 2):
    for n in (5, 20, 80):                                        # sensör sayısı
        PLAN[f"inv_n{n}_s{s}"] = f"--n-data {n} {REC} --seed {s}"
    for w in ("top", "bottom"):                                  # yerleşim
        PLAN[f"inv_{w}_s{s}"] = f"--n-data 20 --where {w} {REC} --seed {s}"
for sig, name in ((0.0, "clean"), (0.05, "noisy05")):            # gürültü (tohum 0)
    PLAN[f"inv_{name}"] = f"--n-data 20 --noise {sig} {REC} --seed 0"
for b0 in (0.5, 8):                                              # başlangıç tahmini (tohum 0)
    PLAN[f"inv_init{b0:g}"] = f"--n-data 20 --bi0 {b0} {REC} --seed 0"


def run(item):
    tag, extra = item
    t0 = time.perf_counter()
    print(f"[başla] {tag}: {extra}", flush=True)
    with open(HERE / f"runs_{tag}.log", "w") as f:
        r = subprocess.run([sys.executable, str(HERE / "pinn_inverse.py"), "--tag", tag, *extra.split()],
                           stdout=f, stderr=subprocess.STDOUT, cwd=HERE, env=os.environ | {"OMP_NUM_THREADS": "2"})
    status = "bitti" if r.returncode == 0 else f"HATA ({r.returncode}), bkz. runs_{tag}.log"
    print(f"[{status}] {tag}  {time.perf_counter() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    todo = {t: a for t, a in PLAN.items() if not (HERE / "runs" / t / "metrics.json").exists()}
    if "--list" in sys.argv:
        for t, a in PLAN.items():
            print(f"{' ' if t in todo else '✓'} {t:16s} {a}")
        sys.exit()
    t_all = time.perf_counter()
    with ThreadPoolExecutor(2) as ex:
        list(ex.map(run, todo.items()))
    print(f"toplam {(time.perf_counter() - t_all) / 60:.1f} dk", flush=True)
