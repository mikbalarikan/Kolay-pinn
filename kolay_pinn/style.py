"""
Türkişi Engineering kimliği + Nature figür kuralları — tek stil kaynağı.

Kullanım:
    from kolay_pinn.style import use_style, C, cmap_thermal, cmap_error, cmap_diverging, save_figure, MM
    use_style()
    fig = plt.figure(figsize=(183 * MM, 120 * MM))
    ...
    save_figure(fig, "figures/fig01_reference")   # .pdf + .svg (vektör) + .png (README önizleme)

Kurallar (Nature, nature-figure / figure-style rehberinden):
  - beyaz zemin, ızgara yok, eksen çizgisi + dışa dönük tick
  - sans-serif 5-7 pt, panel harfi 8 pt kalın küçük harf
  - 89 mm (tek sütun) / 183 mm (çift sütun), yükseklik <= 170 mm
  - düzenlenebilir metin: pdf.fonttype 42, svg.fonttype none
  - bbox_inches="tight" yok: tuval boyutu korunur
  - gökkuşağı yok, kırmızı/yeşil karşıtlığı yok, renkli yazı yok
Kimlik (brand/palette.json, palet v5):
  - seri 1 = Plan Camgöbeği, seri 2 = Lila, referans = Titanyum
  - kimlik kırmızısı (#AF1537) veri grafiğinde kullanılmaz
"""

import json
from pathlib import Path

import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parents[1]
MM = 1 / 25.4  # inch per mm

_pal = json.loads((ROOT / "brand" / "palette.json").read_text(encoding="utf-8"))
C = {k: v["hex"] for k, v in _pal["colors"].items()}

# rol eşlemesi (grafik)
INK = C["derin"]          # yazı, eksen
MUTED = C["titanyum"]     # ikincil yazı, referans çizgisi
SERIES = [C["plan"], C["lila"], C["parca_mandalina"], C["celik_mavisi"]]

# --- renk haritaları -------------------------------------------------------
# sıcaklık: tek ton ailesi (mavi çelik), açık = soğuk, koyu = sıcak
cmap_thermal = LinearSegmentedColormap.from_list(
    "turkisi_thermal",
    [C["krom"], C["elektrik_isigi"], C["elektrik"], C["celik_mavisi"], C["derin"]])
# hata büyüklüğü (log|e|): kağıt -> lila -> derin
cmap_error = LinearSegmentedColormap.from_list(
    "turkisi_error", [C["kagit"], "#C9BCEC", C["lila"], "#4B3A80", C["derin"]])
# işaretli fark: plan (−) / kağıt (0) / mandalina (+)
cmap_diverging = LinearSegmentedColormap.from_list(
    "turkisi_div", [C["plan"], C["kagit"], C["parca_mandalina"]])


def use_style():
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "mathtext.fontset": "custom",
        "mathtext.rm": "Liberation Sans",
        "mathtext.it": "Liberation Sans:italic",
        "mathtext.bf": "Liberation Sans:bold",
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "font.size": 7,
        "axes.titlesize": 7,
        "axes.labelsize": 7,
        "xtick.labelsize": 6,
        "ytick.labelsize": 6,
        "legend.fontsize": 6,
        "axes.linewidth": 0.6,
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 2.5,
        "ytick.major.size": 2.5,
        "xtick.minor.size": 1.5,
        "ytick.minor.size": 1.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "axes.prop_cycle": mpl.cycler(color=SERIES),
        "lines.linewidth": 1.0,
        "lines.markersize": 3,
        "legend.frameon": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "image.cmap": "turkisi_thermal",
    })
    for cm in (cmap_thermal, cmap_error, cmap_diverging):
        try:
            mpl.colormaps.register(cm)
        except ValueError:
            pass  # zaten kayıtlı


def panel_letter(ax, letter, dx=-0.16, dy=1.04):
    """Nature: 8 pt kalın, dik, küçük harf."""
    ax.text(dx, dy, letter, transform=ax.transAxes, fontsize=8, fontweight="bold",
            va="bottom", ha="left", color=INK)


def save_figure(fig, stem, png_dpi=300):
    """Vektör (pdf, svg) + README önizlemesi (png). Tuval kırpılmaz."""
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".pdf"))
    fig.savefig(stem.with_suffix(".svg"))
    fig.savefig(stem.with_suffix(".png"), dpi=png_dpi)


def use_slide_style():
    """Ders slaytları için: aynı palet ve kurallar, projeksiyonda okunur boyutlar (14-16 pt)."""
    use_style()
    mpl.rcParams.update({
        "font.size": 15, "axes.titlesize": 15, "axes.labelsize": 15,
        "xtick.labelsize": 13, "ytick.labelsize": 13, "legend.fontsize": 13,
        "axes.linewidth": 1.0, "xtick.major.width": 1.0, "ytick.major.width": 1.0,
        "xtick.major.size": 5, "ytick.major.size": 5, "lines.linewidth": 2.2,
        "lines.markersize": 7,
    })
