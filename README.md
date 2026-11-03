![Kolay PINN · Türkişi Engineering](brand/banner_kolay_pinn.png)

# Kolay PINN

Fizik bilgili sinir ağlarını (PINN) sıfırdan, adım adım öğrenme reposu. Her case aynı sırayı izler:
problemi tanımla → boyutsuzlaştır → klasik sayısal referans (FDM/CFD) kur ve analitik çözümle doğrula →
PINN'i referansa karşı eğit ve sına.

## Case'ler

| Case | Problem | Durum | Rapor |
|---|---|---|---|
| [01 · 2D ısı iletimi](cases/01-2d-heat-conduction/) | Kare çelik plaka, üç kenar 70 °C, alt kenar su ile konvektif soğutma (Bi ≈ 4.9) | Adım 1–3 ✅ · PINN ⏳ | [PDF](cases/01-2d-heat-conduction/report/case01_adim1-3_fdm_referans.pdf) |

Ek okuma: [PINN × CFD atlası](docs/pinn-cfd-atlas.html) — en çok yıldız alan 10 projenin görsel rehberi.

## Yapı

```
kolay_pinn/style.py     ortak figür stili: Türkişi paleti + Nature figür kuralları
brand/                  palet (palette.json), maskot, banner ve onu üreten betik
cases/NN-<ad>/          her case: çözücüler, figures/, data/, report/, README
docs/                   ek rehberler
```

## Görsel dil

- **Bilimsel figürler** Nature kurallarına uyar: beyaz zemin, 183 mm / 89 mm genişlik, 5–7 pt sans-serif,
  8 pt kalın küçük harf panel etiketleri, ızgarasız eksenler, vektör PDF/SVG ve düzenlenebilir metin,
  gökkuşağı renk haritası yok. Her figürün bir iddia cümlesi (legend başlığı) vardır.
- **Renkler** Türkişi paletinden (v5): seri 1 Plan Camgöbeği `#15A5B4`, seri 2 Lila `#9174D9`, referans
  çizgileri Titanyum `#808E9B`; sıcaklık alanı Krom → Elektrik → Çelik Mavisi → Derin tek ton ailesi.
  Kimlik kırmızısı `#AF1537` yalnız Ti işaretinde, veride kullanılmaz.
- **Banner, PDF kapağı ve şeritler** kimliği taşır: Lacivert Çelik zemin, Krom yazı, kumpas maskotu, tek vurgu
  Fosfor Sarısı `#E6FF1F`.

```python
import sys; sys.path.insert(0, "<repo kökü>")
from kolay_pinn.style import use_style, C, MM, cmap_thermal, panel_letter, save_figure
use_style()
```

Banner'ı yeniden üretmek (gerekli: `rsvg-convert`):

```bash
python brand/scripts/make_banner.py
python brand/scripts/make_banner.py --case "CASE 02 · ..." --out cases/02-.../figures/banner_case02
```
