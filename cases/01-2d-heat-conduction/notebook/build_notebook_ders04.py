"""
Ders 04 defterini üretir ve çalıştırır (çıktılar deftere gömülür).
    python notebook/build_notebook_ders04.py   ->  notebook/ders04_ters_problem.ipynb
Önce: python inverse_classical.py ; python inverse_runs.py ; python inverse_summary.py ; python lecture/ders04/make_slide_figures.py
"""

from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

HERE = Path(__file__).resolve().parent
OUT = HERE / "ders04_ters_problem.ipynb"

cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip("\n")))   # noqa: E731
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip("\n")))    # noqa: E731

md(r"""
# Ders 04 · Ters problem — Bi'yi iç sıcaklıklardan geri bulmak

**Kolay PINN · Türkişi Engineering** · Lisans + yüksek lisans · Adım 7

Ders 03'te kayıptaki Bi yanlışken ölçümlerin hatayı ancak ~2 kat düşürebildiğini gördük: yanlış Robin terimi ile veri
birbiriyle çekişiyordu. Bugün çekişmeyi kaldırıyoruz — Bi'yi ağ ağırlıklarıyla birlikte **öğreniyoruz**:

$$
\min_{\mathbf{w},\,s}\ \mathcal{L}_{\mathrm{PDE}}
+ \lambda\,\frac{1}{N_b}\sum_m\Big(\frac{\partial\hat\theta}{\partial\eta} - e^{s}\,\hat\theta\Big)^2
+ \mu\,\frac{1}{N_d}\sum_{i=1}^{N_d}\big(\hat\theta(\mathbf{x}_i) - \theta_i^{\mathrm{ö}}\big)^2,
\qquad \mathrm{Bi} = e^{s}
$$

**Öğrenme hedefleri**
1. Bi'yi pozitifliği garanti eden bir parametre olarak öğrenmek
2. Ölçümlerin Bi hakkındaki bilgisini deneyden önce hesaplamak: duyarlılık $\partial\theta/\partial\mathrm{Bi}$ ve Cramér–Rao sınırı
3. Köşe çelişkisinin Bi'yi neden aşağı çektiğini görmek
4. PINN'i aynı verilerle klasik bir yöntemle (FDM + en küçük kareler) karşılaştırmak

> Defterdeki eğitim kısaltılmıştır (~2 dk, CPU). Tam koşular (`runs/inv_*`, her biri ~8 dk) özetten yüklenir.
""")

code(r"""
import sys, json, time, logging, warnings, types
from pathlib import Path
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning)

CASE = Path.cwd().parent if Path.cwd().name == "notebook" else Path.cwd()
ROOT = CASE.parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(CASE))

import numpy as np
import torch
import matplotlib.pyplot as plt
from IPython.display import Image, display

from kolay_pinn.style import use_slide_style, C, INK, MUTED
from fdm_solver import BI_DEFAULT as Bi, solve_fdm
from pinn_forward import evaluate
from pinn_hybrid import sensors
import pinn_inverse

use_slide_style(); plt.rcParams["figure.dpi"] = 110
torch.set_default_dtype(torch.float64)
ASSETS = CASE / "lecture" / "ders04" / "assets"
def goster(ad, genislik=760):
    display(Image(filename=str(ASSETS / ad), width=genislik))
S = json.loads((CASE / "data" / "summary_inverse.json").read_text())
CL = json.loads((CASE / "data" / "inverse_classical.json").read_text())
print(f"torch {torch.__version__} · gerçek Bi = {Bi:.4f}")
""")

# =====================================================================================
md(r"""
---
## 1 · Bi'yi parametre yap

### 1.1 Neden $\mathrm{Bi} = e^{s}$?

- Bi negatif olamaz; $e^{s}$ her $s$ için pozitif.
- $\partial\mathcal{L}/\partial s = \mathrm{Bi}\,\partial\mathcal{L}/\partial\mathrm{Bi}$: adım **göreli** olur. Bi = 1'de de 10'da da benzer yüzdelik adımlar.

`pinn_inverse.train` içinde tek değişiklik bu:

```python
s = torch.nn.Parameter(torch.tensor(math.log(args.bi0)))      # Bi = exp(s)
r_pde, r_rob = residuals(model, X_int, X_bot, s.exp())
opt = torch.optim.Adam([{"params": model.parameters()}, {"params": [s], "lr": 1e-2}], lr=1e-3)
```

$s$'nin öğrenme oranı ağınkinden 10 kat büyük: ağın binlerce ağırlığı varken $s$ tek bir sayı ve hızlı hareket etmesi gerekiyor.

### 1.2 Kısa bir eğitim

20 düzgün sensör, $\sigma = 0.01$ (0.5 °C), Bi₀ = 1:
""")
code(r"""
X_d, y_d, temiz = sensors(20, "uniform", 0.01, seed=0)
args = types.SimpleNamespace(seed=0, width=50, depth=4, bi0=1.0, n_int=4096, n_bot=256, skip=0.02,
                             lam=1.0, mu=100.0, lr=1e-3, lr_bi=1e-2, adam=1500, lbfgs=400, Bi=Bi)
t0 = time.perf_counter()
model, Bi_hat, hist, info = pinn_inverse.train(args, X_d, y_d)
m = evaluate(model, Bi)[0]
print(f"\nkısa eğitim: Bi = {Bi_hat:.3f} (gerçek {Bi:.3f}, hata %{100 * abs(Bi_hat - Bi) / Bi:.1f}) · "
      f"bağıl L2 {m['rel_L2']:.1e} · {time.perf_counter() - t0:.0f} s")
""")
code(r"""
fig, ax = plt.subplots(figsize=(7, 3.6))
ax.plot(hist["it"], hist["Bi"], color=C["plan"], lw=2)
ax.axhline(Bi, color=INK, ls="dashed"); ax.axvline(args.adam, color=MUTED, lw=0.8)
ax.set(xlabel="iterasyon", ylabel="Bi tahmini", title="kısa eğitim: Adam 1500 + L-BFGS 400")
plt.show()
""")
md(r"""
Kısa eğitimde Bi henüz gerçek değere oturmayabilir: Adam'da Bi yavaş yükselir, son yaklaşmayı L-BFGS yapar.
Tam koşular (Adam 6000 + L-BFGS 2000):
""")
code(r"""goster("02_trajectory.png", 700)""")
code(r"""
for g, v in S["groups"].items():
    print(f"{g:18s} Bi = {[round(r['Bi_hat'], 3) for r in v['runs']]}")
if S["start_bi10"]:
    print(f"\nBi₀ = 10'dan: {S['start_bi10']['Bi_hat']:.3f}  (aynı tohum, Bi₀ = 1: {S['start_bi10']['same_as_bi0_1_seed0']:.3f})")
""")

# =====================================================================================
md(r"""
---
## 2 · Ne kadar bilgi var?

### 2.1 Duyarlılık

Bi'yi biraz değiştirince her noktadaki sıcaklık ne kadar değişir? FDM'i iki kez çözüp merkezi farkla:

$$S(\mathbf{x}) = \frac{\partial\theta}{\partial\,\mathrm{Bi}} \approx \frac{\theta(\mathbf{x};\mathrm{Bi}+h) - \theta(\mathbf{x};\mathrm{Bi}-h)}{2h}$$
""")
code(r"""
N = 101
h = 1e-3 * Bi
x, _, _ = solve_fdm(N, Bi)
Sm = (solve_fdm(N, Bi + h)[2] - solve_fdm(N, Bi - h)[2]) / (2 * h)
print(f"max |S| = {np.abs(Sm).max():.4f} (alt yüzey ortası) · merkez {abs(Sm[N // 2, N // 2]):.4f} · "
      f"üst yarı max {np.abs(Sm[N // 2:]).max():.4f}")
""")
code(r"""goster("01_sensitivity.png", 900)""")
md(r"""
Bi yalnız soğutulan yüzeyin yakınını değiştiriyor; Dirichlet duvarlarına yakın noktalar duvar sıcaklığına kilitli.

### 2.2 Cramér–Rao alt sınırı *(yüksek lisans)*

Gauss gürültüsünde Fisher bilgisi ve ondan gelen alt sınır:

$$I(\mathrm{Bi}) = \frac{1}{\sigma^2}\sum_{i=1}^{N_d} S(\mathbf{x}_i)^2, \qquad
\sigma_{\mathrm{Bi}} \ge I^{-1/2} = \frac{\sigma}{\sqrt{\sum_i S(\mathbf{x}_i)^2}}$$

Hiçbir yansız tahminci bu sensörlerle bu gürültüde daha iyisini yapamaz. Deney yapmadan hesaplanır:
""")
code(r"""
from inverse_classical import crb, fit_fdm
for w in ("uniform", "bottom", "top"):
    for n in (5, 20, 80):
        X, _, _ = sensors(n, w, 0.01, seed=0)
        print(f"{w:8s} N_d = {n:2d}:  CRB σ_Bi/Bi = %{100 * crb(X, 0.01) / Bi:5.2f}")
""")
md(r"""
Kural: sensör sayısını 4 katına çıkarmak belirsizliği yarıya indirir; sensörü duyarlılığı yüksek yere koymak da aynı
işi yapar.

### 2.3 Klasik taban: FDM + en küçük kareler

Aynı sensörlerle FDM'i bir en küçük kareler döngüsüne koyuyoruz ($\log\mathrm{Bi}$ üzerinde, `scipy.optimize.least_squares`):
""")
code(r"""
bi_ls, t_ls, n_ev = fit_fdm(X_d, y_d)
print(f"FDM + EKK: Bi = {bi_ls:.4f} · {n_ev} FDM çözümü · {t_ls:.2f} s")
print(f"PINN (tam koşu, aynı sensörler): Bi = {S['groups']['temel 20 düzgün']['runs'][0]['Bi_hat']:.4f}")
""")
code(r"""goster("03_error_crb.png", 900)""")
code(r"""
print(f"{'grup':18s} {'PINN':>7s} {'FDM-EKK':>8s} {'CRB':>6s}   (ortalama |Bi − gerçek| / Bi)")
for g, v in S["groups"].items():
    print(f"{g:18s} %{100 * v['pinn_rel_err_mean']:5.2f}  %{100 * v['fdm_ls_rel_err_mean']:5.2f}  %{100 * v['crb_rel']:4.1f}")
""")
code(r"""goster("04_parity.png", 480)""")
md(r"""
**Okuma.** Köşe dışlamalı koşularda PINN ile klasik yöntem aynı veriden neredeyse aynı Bi'yi buluyor; ikisi de
Cramér–Rao sınırı mertebesinde. Hata yöntemden değil, ölçüm gürültüsünden geliyor.
""")

# =====================================================================================
md(r"""
---
## 3 · Tuzaklar ve maliyet

### 3.1 Köşe yanlılığı

Alt köşede yan duvar $\theta = 1$ ve eğimi sıfır dayatıyor; Robin koşulu eğimin $\mathrm{Bi}\,\theta$ olmasını istiyor:

$$\eta = 0,\ \xi \to 0:\quad \frac{\partial\hat\theta}{\partial\eta} \to 0,\ \ \hat\theta \to 1
\;\Rightarrow\; r_{\mathrm{Robin}} \to -\mathrm{Bi},\qquad \frac{\partial r^2}{\partial\,\mathrm{Bi}} = 2\,\mathrm{Bi}\,\hat\theta^2 > 0$$

Kaybı azaltmanın kolay yolu Bi'yi küçültmek. Köşeden $\delta = 0.02$ içindeki Robin noktalarını dışlıyoruz:
""")
code(r"""
a, b = S["groups"]["temel 20 düzgün"]["runs"], S["groups"]["köşe dışlama yok"]["runs"]
for k, (ra, rb) in enumerate(zip(a, b)):
    print(f"tohum {k}: FDM-EKK {ra['fdm_ls_Bi']:.3f} · PINN δ=0.02 {ra['Bi_hat']:.3f} · PINN δ=0 {rb['Bi_hat']:.3f}")
""")
code(r"""goster("05_corner.png", 560)""")

md(r"""
### 3.2 Gürültü ve maliyet
""")
code(r"""goster("06_noise.png", 560)""")
code(r"""
V = S["verdict"]
print(f"PINN ters koşu: ~{V['pinn_time_s_median']:.0f} s · FDM + EKK: ~{V['fdm_ls_time_s_median']:.1f} s "
      f"-> {V['pinn_time_s_median'] / V['fdm_ls_time_s_median']:.0f} kat")
""")
md(r"""
Bu problemde klasik yöntem aynı doğruluğu yüzlerce kat hızlı veriyor. PINN'in ters problemde anlamlı olduğu yerler:
çözücü pahalı ve türevlenemez olduğunda (her adım bir CFD koşusu), bilinmeyen bir **alan** olduğunda ($h(\xi)$),
ve aynı ağ her Bi için çözüm verdiğinde — parametrik PINN, Ders 05.

## Özet

- $\mathrm{Bi} = e^{s}$ ile Bi'yi ağırlıklarla birlikte öğrenmek tek satır; Bi₀ = 1 ve 10'dan aynı değere yakınsar.
- Ne kadar doğru bulabileceğinizi önce hesaplayın: duyarlılık haritası ve Cramér–Rao sınırı yerleşimi belirler.
- PINN'in Bi hatası gürültü sınırında ve aynı veriyle klasik yöntemle örtüşüyor.
- Köşe tekilliği ters problemde yanlılık olur: köşe Robin noktalarını dışlayın.

## Alıştırmalar

**Lisans:** (1) 10 sensörü alt şeride koyun: önce CRB'yi hesaplayın, sonra PINN ile deneyin ·
(2) Bi₀ = 0.2 ve 25'ten başlatın · (3) $\delta = 0, 0.02, 0.05, 0.1$ taraması.

**Yüksek lisans:** (1) 20 tohumla PINN Bi dağılımının standart sapmasını CRB ile karşılaştırın ·
(2) $h(\xi) = \mathrm{Bi}\,(1 + a\,\xi(1-\xi))$ yapın, $a$'yı da öğrenin · (3) sensör konumlarına ±1 mm hata ekleyin.
""")
code(r"""
# Alıştırma alanı — Lisans 1: 10 sensör alt şeritte
X_b, y_b, _ = sensors(10, "bottom", 0.01, seed=0)
print(f"CRB σ_Bi/Bi = %{100 * crb(X_b, 0.01) / Bi:.2f} · FDM-EKK Bi = {fit_fdm(X_b, y_b)[0]:.3f}")
# model_b, Bi_b, _, _ = pinn_inverse.train(args, X_b, y_b)   # açıp çalıştırın (~2 dk)
""")

nb = nbf.v4.new_notebook()
nb["cells"] = cells
nb["metadata"] = {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                  "language_info": {"name": "python"}}
NotebookClient(nb, timeout=2400, kernel_name="python3", resources={"metadata": {"path": str(HERE)}}).execute()
nbf.write(nb, OUT)
print(OUT, f"{OUT.stat().st_size / 1e6:.1f} MB")
