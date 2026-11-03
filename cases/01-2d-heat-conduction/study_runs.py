"""
Ders 02 sağlamlık çalışması: tohum değişkenliği + kapasite + eğitim süresi.
Koşuları sırayla çalıştırır; metrics.json'u olan koşuyu atlar (kaldığı yerden devam eder).

    python study_runs.py            # hepsini koşar (2 CPU'da ~1.5–2 saat)
    python study_runs.py --list     # planı gösterir

Tohum hem ağ başlatmayı hem kolokasyon noktalarını (Sobol karıştırma) değiştirir.
"""

import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

# tag: ek argümanlar   (seed 0 koşuları zaten var: uniform, corner, skip)
PLAN = {
    # tohum değişkenliği — üç kolokasyon stratejisi × 2 ek tohum
    "uniform_s1": "--seed 1",
    "uniform_s2": "--seed 2",
    "skip_s1": "--skip 0.02 --seed 1",
    "skip_s2": "--skip 0.02 --seed 2",
    "corner_s1": "--corner --seed 1",
    "corner_s2": "--corner --seed 2",
    # kapasite ve eğitim süresi — temel ayara göre tek değişiklik
    "long": "--lbfgs 6000",
    "wide4x100": "--width 100",
    "deep8x50": "--depth 8",
}

if __name__ == "__main__":
    if "--list" in sys.argv:
        for t, a in PLAN.items():
            done = (HERE / "runs" / t / "metrics.json").exists()
            print(f"{'✓' if done else ' '} {t:12s} {a}")
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
            r = subprocess.run([sys.executable, str(HERE / "pinn_forward.py"), "--tag", tag, *extra.split()],
                               stdout=f, stderr=subprocess.STDOUT, cwd=HERE)
        status = "bitti" if r.returncode == 0 else f"HATA ({r.returncode}), bkz. {log.name}"
        print(f"[{status}] {tag}  {time.perf_counter() - t0:.0f} s", flush=True)
    print(f"toplam {(time.perf_counter() - t_all) / 60:.1f} dk", flush=True)
