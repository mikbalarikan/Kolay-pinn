"""
Adım 7 deney planı: ters problem (Bi öğrenilir). Sırayla koşar; metrics.json'u olan koşuyu atlar.

    python inverse_runs.py           # hepsini koşar (2 CPU'da ~3.5 saat)
    python inverse_runs.py --list    # planı gösterir

Temel ayar: Bi₀ = 1, 20 sensör (düzgün), σ = 0.01, μ = 100, köşe Robin dışlama δ = 0.02.
"""

import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = "--bi0 1 --n-data 20 --noise 0.01 --where uniform --mu 100 --skip 0.02"
PLAN = {}
for s in (0, 1, 2):
    PLAN[f"inv_base_s{s}"] = f"{BASE} --seed {s}"
for s in (0, 1, 2):                                                   # köşe çelişkisi Bi'yi aşağı çeker mi?
    PLAN[f"inv_noskip_s{s}"] = f"{BASE.replace('--skip 0.02', '--skip 0')} --seed {s}"
for w in ("top", "bottom"):                                           # tanımlanabilirlik: yerleşim
    for s in (0, 1, 2):
        PLAN[f"inv_{w}_s{s}"] = f"{BASE.replace('--where uniform', '--where ' + w)} --seed {s}"
for n in (80, 5):                                                     # sensör sayısı
    for s in (0, 1, 2):
        PLAN[f"inv_n{n}_s{s}"] = f"{BASE.replace('--n-data 20', f'--n-data {n}')} --seed {s}"
for s in (0, 1, 2):                                                   # veri ağırlığı
    PLAN[f"inv_mu1_s{s}"] = f"{BASE.replace('--mu 100', '--mu 1')} --seed {s}"
PLAN["inv_clean"] = f"{BASE.replace('--noise 0.01', '--noise 0')} --seed 0"
PLAN["inv_noisy05"] = f"{BASE.replace('--noise 0.01', '--noise 0.05')} --seed 0"
PLAN["inv_bi10"] = f"{BASE.replace('--bi0 1', '--bi0 10')} --seed 0"   # yukarıdan başlangıç

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
            r = subprocess.run([sys.executable, str(HERE / "pinn_inverse.py"), "--tag", tag, *extra.split()],
                               stdout=f, stderr=subprocess.STDOUT, cwd=HERE)
        print(f"[{'bitti' if r.returncode == 0 else f'HATA ({r.returncode})'}] {tag}  {time.perf_counter() - t0:.0f} s", flush=True)
    print(f"toplam {(time.perf_counter() - t_all) / 60:.1f} dk", flush=True)
