![Kolay PINN · Case 01](figures/banner_case01.png)

# Case 01 — PINN for 2D Heat Conduction

Kare çelik plaka, üç kenarı 70 °C, alt kenarı 20 °C suyla konvektif soğutuluyor.
Hedef: aynı problemi önce klasik sayısal yöntemle (FDM) çözüp referans almak, sonra
adım adım PINN'e geçmek.

🎓 **Ders 01 (26 slayt, ~50 dk, konuşmacı notlu):** [`lecture/ders01_2d_isi_iletimi_referans.pptx`](lecture/ders01_2d_isi_iletimi_referans.pptx)
📄 **Rapor (Adım 1–3):** [`report/case01_adim1-3_fdm_referans.pdf`](report/case01_adim1-3_fdm_referans.pdf)

## Yol haritası

| # | Adım | Durum |
|---|------|-------|
| 1 | Problemi tanımla (L, k, h, Bi) | ✅ |
| 2 | Boyutsuzlaştır | ✅ |
| 3 | Referans FDM çözücü + analitik doğrulama | ✅ |
| 4 | Forward PINN (sadece fizik, veri yok) | ⏳ |
| 5 | Doğrulama: L2 hata, hata haritası, alt yüzey ısı akısı | ⏳ |
| 6 | Hibrit PINN: seyrek + gürültülü referans verisi | ⏳ |
| 7 | Ters problem: Bi'yi iç sıcaklıklardan geri bul | ⏳ |
| 8 | Parametrik vekil model: girdi (x, y, Bi) | ⏳ |
| 9 | Framework karşılaştırması (DeepXDE / PhysicsNeMo) | ⏳ |

---

## 1. Problem tanımı

| Büyüklük | Değer |
|---|---|
| Plaka boyu L | 0.1 m (kare) |
| Malzeme | çelik, k = 49 W/m·K |
| Duvar sıcaklığı T_w (üst, sol, sağ) | 70 °C |
| Akışkan | su, U∞ = 1 m/s, T∞ = 20 °C |
| Alt kenar | konvektif soğutma, h |

**h — düz levha üzerinde laminer akış korelasyonu.** Su özellikleri 20 °C'de
(Incropera Tablo A.6): ν = 1.004×10⁻⁶ m²/s, k_f = 0.598 W/m·K, Pr = 7.01.

```math
\begin{aligned}
\mathrm{Re}_L &= \frac{U L}{\nu} = \frac{1.0 \times 0.1}{1.004\times10^{-6}} \approx 99\,600 \quad (< 5\times10^5 \Rightarrow \text{laminer}) \\
\overline{\mathrm{Nu}}_L &= 0.664\,\mathrm{Re}_L^{1/2}\,\mathrm{Pr}^{1/3} = 0.664 \times 315.6 \times 1.913 \approx 401 \\
\bar h &= \frac{\overline{\mathrm{Nu}}_L\,k_f}{L} = \frac{401 \times 0.598}{0.1} \approx 2\,400\ \mathrm{W\,m^{-2}\,K^{-1}} \\
\mathrm{Bi} &= \frac{\bar h\,L}{k} = \frac{2398 \times 0.1}{49} \approx 4.9
\end{aligned}
```

Notlar:
- Senin verdiğin h = 2000 W/m²K ile Bi = 4.08. Fark %20 civarında; korelasyonun kendi
  belirsizliği (~±%15–20) ve film sıcaklığı seçimiyle aynı mertebede. Film sıcaklığında
  (~35 °C) özellik alınırsa h ≈ 2 600, Bi ≈ 5.3. Kodda varsayılan **Bi = 4.895**;
  `--Bi 4.08` ile değiştirilebilir.
- Korelasyon izotermal levha varsayar; alt yüzey burada 37–70 °C arasında değişiyor.
  Bu yüzden h sabit kabulü bir mühendislik yaklaşımıdır. İleride gerçek bir eşlenik
  (conjugate) CFD ile karşılaştırma ilginç bir yan adım olur.
- $\mathrm{Bi} \approx 5 \gg 0.1$: plaka içinde güçlü sıcaklık gradyanı var — PINN için iyi bir test.

## 2. Boyutsuzlaştırma

```math
\theta = \frac{T - T_\infty}{T_w - T_\infty}, \qquad \xi = \frac{x}{L}, \qquad \eta = \frac{y}{L}
```

Boyutsuz problem, $(\xi, \eta) \in [0,1]^2$:

```math
\begin{aligned}
&\frac{\partial^2\theta}{\partial\xi^2} + \frac{\partial^2\theta}{\partial\eta^2} = 0 && \text{(Laplace)} \\
&\theta = 1, \quad \xi = 0,\ \xi = 1,\ \eta = 1 && \text{(duvarlar, } 70\,^\circ\mathrm{C}\text{)} \\
&\frac{\partial\theta}{\partial\eta} = \mathrm{Bi}\,\theta, \quad \eta = 0 && \text{(Robin / konveksiyon)}
\end{aligned}
```

Robin koşulunun türetilmesi: alt yüzeyde dışarı (−y yönünde) çıkan iletim akısı, konveksiyonla taşınan
akıya eşit; $T - T_\infty = \Delta T\,\theta$ ve $y = L\eta$ yazınca $\Delta T$ sadeleşir:

```math
k\,\frac{\partial T}{\partial y} = h\,(T - T_\infty)
\quad\Longrightarrow\quad
\frac{\partial\theta}{\partial\eta} = \frac{hL}{k}\,\theta = \mathrm{Bi}\,\theta
```

Tek fiziksel parametre Bi. Geometri ve sıcaklıklar ölçekten düştü — PINN'i boyutsuz
formda eğitmenin ana sebebi bu (girdi ve çıktılar O(1)).

Sıcaklık: $T = 20 + 50\,\theta$ [°C]. Alt yüzeyden çıkan ısı (birim derinlik başına):

```math
Q' = \bar h\,L\,(T_w - T_\infty) \int_0^1 \theta(\xi, 0)\,d\xi
```

## 3. Referans FDM çözücü

`fdm_solver.py`: düzgün N×N düğüm ağı, 2. mertebe merkezi farklar, Robin koşulu için
alt kenarda hayalet düğüm:

```math
\begin{aligned}
&\theta_{i+1,j} + \theta_{i-1,j} + \theta_{i,j+1} + \theta_{i,j-1} - 4\,\theta_{i,j} = 0 && \text{(iç düğüm)} \\
&\theta_{i,-1} = \theta_{i,1} - 2\Delta\,\mathrm{Bi}\,\theta_{i,0} && \text{(hayalet düğüm)} \\
&\theta_{i-1,0} + \theta_{i+1,0} + 2\,\theta_{i,1} - (4 + 2\Delta\,\mathrm{Bi})\,\theta_{i,0} = 0 && \text{(alt kenar)}
\end{aligned}
```

Alt köşeler yan duvarlara ait ($\theta = 1$). Doğrusal sistem seyrek doğrudan çözücüyle çözülür.

**Analitik doğrulama.** Değişkenlere ayırma ile:

```math
\theta(\xi,\eta) = 1 - \sum_{n\ \text{tek}} A_n \sin(n\pi\xi)\,\sinh\big(n\pi(1-\eta)\big),
\qquad
A_n = \frac{4\,\mathrm{Bi}/(n\pi)}{n\pi\cosh(n\pi) + \mathrm{Bi}\,\sinh(n\pi)}
```

### Sonuçlar (Bi = 4.895, N = 101)

| Büyüklük | Değer |
|---|---|
| Alt yüzey orta noktası θ(0.5, 0) | 0.331 → **36.5 °C** |
| Plakadaki min. sıcaklık | 36.5 °C |
| ∫ θ(ξ,0) dξ | 0.462 |
| Alt yüzeyden ısı çıkışı Q' | **≈ 5 540 W/m** (derinlik başına) |

Ağ yakınsaması (analitiğe göre):

| N | bağıl L2 | max \|hata\| |
|---|---|---|
| 26 | 1.2e-3 | 1.6e-2 |
| 51 | 3.7e-4 | 9.0e-3 |
| 101 | 1.1e-4 | 4.8e-3 |
| 201 | 3.0e-5 | 2.5e-3 |

L2 hatası ~2. mertebe yakınsıyor, maksimum hata ise yalnızca ~1. mertebe. Sebep alt
köşelerdeki tekillik: yan duvar θ = 1 isterken alt kenar soğuyor, köşede ∂θ/∂ξ
sonsuza gider. **PINN hatası da büyük olasılıkla tam burada toplanacak** — 5. adımda
sadece toplam kayba değil, hata haritasına bakacağız.

![Fig. 1](figures/fig01_fdm_reference.png)

**Fig. 1 | İkinci mertebe FDM seri çözümü yeniden üretiyor; hata alt köşelerdeki tekillikte toplanıyor.**
**a**, N = 101 ağında sıcaklık alanı, izotermler °C. **b**, soğutulan yüzeyin sıcaklığı: FDM (çizgi) ve 4000
terimli seri çözüm (her 5. düğüm). **c**, mutlak hatanın log₁₀ haritası; açık bant hatanın işaret değiştirdiği
yer. **d**, N = 26–201 için bağıl L₂ ve maksimum hata; p en küçük kareler eğimi (L₂: 1.77, maks.: 0.88).
Vektör sürümler: [`fig01_fdm_reference.pdf`](figures/fig01_fdm_reference.pdf) · [`.svg`](figures/fig01_fdm_reference.svg)

### Çalıştırma

```bash
pip install -r requirements.txt
python fdm_solver.py            # çözer, data/fdm_N101.{npz,csv} yazar
python fdm_solver.py --Bi 4.08  # h = 2000 W/m²K durumu
python plot_reference.py        # figures/fig01_fdm_reference.{pdf,svg,png} + data/summary.json
python make_report.py           # report/case01_adim1-3_fdm_referans.pdf
python lecture/equations.py && python lecture/make_slide_figures.py && node lecture/build_lecture.js   # ders destesi (önce kökte: npm install; ayrıca pdflatex + pandoc)
```

`data/fdm_N101.npz` alanları: `x, y, theta, theta_exact, Bi, L, k, T_wall, T_inf`.
PINN adımlarında referans ve (6–7. adımlarda) seyrek "ölçüm" verisi buradan çekilecek.
