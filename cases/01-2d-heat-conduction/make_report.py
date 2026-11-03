"""
Case 01 raporu (Adım 1–3) — Türkişi kimlikli PDF.
Önce:  python plot_reference.py     (figür + data/summary.json)
Sonra: python make_report.py         -> report/case01_adim1-3_fdm_referans.pdf
"""

import json
import sys
from pathlib import Path

from reportlab.lib.enums import TA_LEFT  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.platypus import (Image, KeepTogether, Paragraph, SimpleDocTemplate,  # noqa: E402
                                Spacer, Table, TableStyle)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from kolay_pinn.style import C  # noqa: E402

# ---------------------------------------------------------------- fonts
from matplotlib import font_manager as fm  # noqa: E402


def _font(family, weight="normal", style="normal"):
    return fm.findfont(fm.FontProperties(family=family, weight=weight, style=style), fallback_to_default=False)


for name, fam, w, s in [("Body", "Liberation Sans", "normal", "normal"), ("BodyB", "Liberation Sans", "bold", "normal"),
                        ("BodyI", "Liberation Sans", "normal", "italic"), ("Mono", "DejaVu Sans Mono", "normal", "normal")]:
    try:
        pdfmetrics.registerFont(TTFont(name, _font(fam, w, s)))
    except Exception:
        pdfmetrics.registerFont(TTFont(name, _font("DejaVu Sans", w, s)))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyB", italic="BodyI", boldItalic="BodyB")

col = {k: colors.HexColor(v) for k, v in C.items()}
INK, MUTED = col["derin"], col["titanyum"]

st = {
    "h1": ParagraphStyle("h1", fontName="BodyB", fontSize=15, leading=19, textColor=INK, spaceAfter=2),
    "sub": ParagraphStyle("sub", fontName="Body", fontSize=9, leading=12, textColor=MUTED, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName="BodyB", fontSize=10.5, leading=14, textColor=INK, spaceBefore=8, spaceAfter=3),
    "p": ParagraphStyle("p", fontName="Body", fontSize=8.6, leading=12.2, textColor=INK, alignment=TA_LEFT, spaceAfter=4),
    "eq": ParagraphStyle("eq", fontName="Mono", fontSize=8, leading=11, textColor=INK, leftIndent=8,
                         backColor=col["krom"], borderPadding=(4, 6, 4, 6), spaceBefore=3, spaceAfter=7),
    "cap": ParagraphStyle("cap", fontName="Body", fontSize=7.6, leading=10.4, textColor=INK, spaceBefore=3),
    "cell": ParagraphStyle("cell", fontName="Body", fontSize=7.8, leading=10, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="BodyB", fontSize=7.8, leading=10, textColor=INK),
}
P = lambda t, s="p": Paragraph(t, st[s])  # noqa: E731


def table(rows, widths, header=True):
    data = [[P(c, "cellb" if (header and i == 0) else "cell") for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, hAlign="LEFT")
    style = [("LINEABOVE", (0, 0), (-1, 0), 0.8, INK), ("LINEBELOW", (0, -1), (-1, -1), 0.8, INK),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 2.5),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5), ("LEFTPADDING", (0, 0), (-1, -1), 4)]
    if header:
        style.append(("LINEBELOW", (0, 0), (-1, 0), 0.4, MUTED))
    for r in range(2 if header else 1, len(rows), 2):
        style.append(("BACKGROUND", (0, r), (-1, r), col["kagit"]))
    t.setStyle(TableStyle(style))
    return t


# ---------------------------------------------------------------- page chrome
PAGE_W, PAGE_H = A4
BANNER = HERE / "figures" / "banner_case01.png"
BAND_H = PAGE_W * 320 / 1280


def first_page(cv, doc):
    cv.drawImage(str(BANNER), 0, PAGE_H - BAND_H, width=PAGE_W, height=BAND_H)
    footer(cv, doc)


def later_pages(cv, doc):
    # ince kimlik şeridi: çelik mavisi + kırmızı başlangıç
    cv.setFillColor(col["celik_mavisi"]); cv.rect(0, PAGE_H - 3 * mm, PAGE_W, 3 * mm, stroke=0, fill=1)
    cv.setFillColor(col["kirmizi"]); cv.rect(0, PAGE_H - 3 * mm, 8 * mm, 3 * mm, stroke=0, fill=1)
    cv.setFont("Body", 7.5); cv.setFillColor(MUTED)
    cv.drawString(18 * mm, PAGE_H - 9 * mm, "KOLAY PINN · Case 01 · 2D ısı iletimi · Adım 1–3")
    footer(cv, doc)


def footer(cv, doc):
    y = 10 * mm
    # Ti işareti (vektör)
    s, x0 = 4.2 * mm / 100 * 1.6, 18 * mm
    cv.saveState(); cv.translate(x0, y - 1.2 * mm); cv.scale(s, -s); cv.translate(0, -84)
    cv.setFillColor(INK)
    cv.rect(16, 20, 42, 11, stroke=0, fill=1); cv.rect(31, 20, 12, 52, stroke=0, fill=1)
    cv.rect(64, 38, 12, 34, stroke=0, fill=1); cv.rect(12, 72, 76, 3.5, stroke=0, fill=1)
    cv.setFillColor(col["kirmizi"]); cv.circle(70, 27, 6.5, stroke=0, fill=1)
    cv.restoreState()
    cv.setFont("Mono", 7); cv.setFillColor(INK)
    cv.drawString(x0 + 8 * mm, y, "TÜRKİŞİ ENGINEERING")
    cv.setFillColor(MUTED); cv.setFont("Body", 7)
    cv.drawCentredString(PAGE_W / 2, y, "github.com/mikbalarikan/kolay-pinn")
    cv.drawRightString(PAGE_W - 18 * mm, y, f"{doc.page}")
    cv.setStrokeColor(col["gumus"]); cv.setLineWidth(0.4)
    cv.line(18 * mm, y + 4 * mm, PAGE_W - 18 * mm, y + 4 * mm)


# ---------------------------------------------------------------- content
S = json.loads((HERE / "data" / "summary.json").read_text())
cor, fdm, cv_ = S["correlation"], S["fdm_N101"], S["convergence"]

# figure: matplotlib's own raster (same fonts as the vector PDF/SVG)
fig_png = HERE / "figures" / "fig01_fdm_reference.png"

content_w = PAGE_W - 36 * mm
story = [Spacer(1, BAND_H - 12 * mm)]
story += [P("Adım 1–3: problem tanımı, boyutsuzlaştırma ve FDM referansı", "h1"),
          P("Kare çelik plaka, üç kenar 70 °C, alt kenar suyla konvektif soğutma. "
            "PINN adımlarından önce sayısal referansın kurulup analitik çözümle doğrulanması.", "sub")]

story += [P("1 · Problem tanımı", "h2"),
          table([["Büyüklük", "Değer", "Not"],
                 ["Plaka boyu L", "0.1 m", "kare"],
                 ["Isı iletim katsayısı k", "49 W m<super>−1</super> K<super>−1</super>", "çelik"],
                 ["Duvar sıcaklığı T<sub>w</sub>", "70 °C", "üst, sol, sağ"],
                 ["Akışkan", "su, 1 m s<super>−1</super>, 20 °C", "alt kenar boyunca"],
                 ["Re<sub>L</sub> = UL/ν", f"{cor['Re']:,}".replace(",", " "), "&lt; 5×10<super>5</super> → laminer"],
                 ["Nu<sub>L</sub> = 0.664 Re<super>1/2</super> Pr<super>1/3</super>", f"{cor['Nu']}", "izotermal düz levha"],
                 ["h = Nu k<sub>f</sub>/L", f"{cor['h_W_m2K']:,} W m<super>−2</super> K<super>−1</super>".replace(",", " "),
                  "su 20 °C: ν = 1.004×10<super>−6</super>, k<sub>f</sub> = 0.598, Pr = 7.01"],
                 ["Bi = hL/k", f"<b>{cor['Bi']:.2f}</b>", "h = 2000 ile 4.08; film 35 °C ile 5.3"]],
                [48 * mm, 42 * mm, content_w - 90 * mm]),
          Spacer(1, 3),
          P("Bi ≈ 5 ≫ 0.1: plaka içinde güçlü gradyan var, toplu kapasite yaklaşımı geçersiz — PINN için iyi bir test. "
            "Korelasyon izotermal yüzey varsayar; burada alt yüzey 37–70 °C arasında değiştiği için sabit h bir "
            "mühendislik kabulüdür.")]

story += [P("2 · Boyutsuzlaştırma", "h2"),
          P("θ = (T − T<sub>∞</sub>)/(T<sub>w</sub> − T<sub>∞</sub>), ξ = x/L, η = y/L tanımlarıyla tek parametre Bi kalır:"),
          P("∂²θ/∂ξ² + ∂²θ/∂η² = 0          (ξ, η) ∈ [0, 1]²<br/>"
            "θ = 1                          ξ = 0, ξ = 1, η = 1<br/>"
            "∂θ/∂η = Bi · θ                 η = 0   (k ∂T/∂y = h (T − T∞))", "eq"),
          P("Alttan çıkan ısı (birim derinlik): Q′ = h L (T<sub>w</sub> − T<sub>∞</sub>) ∫<sub>0</sub><super>1</super> θ(ξ, 0) dξ.")]

story += [P("3 · FDM referans çözücü ve analitik doğrulama", "h2"),
          P("Düzgün N×N düğüm ağı, ikinci mertebe merkezi farklar. Robin koşulu alt kenarda hayalet düğümle: "
            "θ<sub>i,−1</sub> = θ<sub>i,1</sub> − 2Δ Bi θ<sub>i,0</sub>. Alt köşeler yan duvarlara aittir (θ = 1). "
            "Seyrek doğrudan çözücü. Doğrulama için değişkenlere ayırma serisi:"),
          P("θ = 1 − Σ<sub>n tek</sub> A<sub>n</sub> sin(nπξ) sinh(nπ(1−η)),<br/>"
            "A<sub>n</sub> = (4Bi/nπ) / (nπ cosh nπ + Bi sinh nπ)", "eq")]

img = Image(str(fig_png), width=content_w, height=content_w * 112 / 183)
legend = P("<b>Fig. 1 | İkinci mertebe FDM seri çözümü yeniden üretiyor; hata alt köşelerdeki tekillikte toplanıyor.</b> "
           f"<b>a</b>, N = 101 ağında sıcaklık alanı; izotermler °C. Alt kenar suyla soğutuluyor (Bi = {cor['Bi']:.2f}). "
           "<b>b</b>, soğutulan yüzeyin sıcaklığı: FDM (çizgi) ve 4000 terimli seri çözüm (her 5. düğüm). "
           "<b>c</b>, N = 101'de mutlak hatanın log<sub>10</sub> haritası; açık bant, hatanın işaret değiştirdiği yer. "
           "<b>d</b>, N = 26, 51, 101, 201 için seri çözüme göre bağıl L<sub>2</sub> ve maksimum hata; p, en küçük kareler eğimi. "
           "Tüm büyüklükler boyutsuz θ üzerinden hesaplandı; T = 20 + 50θ °C.", "cap")
story += [Spacer(1, 4), KeepTogether([img, legend])]

story += [P("Sonuçlar", "h2"),
          table([["Büyüklük", "Değer"],
                 ["Alt yüzey orta noktası θ(0.5, 0)", f"{fdm['theta_mid_bottom']:.3f} → <b>{fdm['T_mid_bottom_C']:.1f} °C</b>"],
                 ["Plakadaki en düşük sıcaklık", f"{fdm['T_mid_bottom_C']:.1f} °C (alt orta)"],
                 ["∫ θ(ξ, 0) dξ  — FDM / seri", f"{fdm['int_theta_bottom']:.4f} / {S['series']['int_theta_bottom']:.4f}"],
                 ["Alttan çıkan ısı Q′", f"<b>≈ {fdm['Q_per_depth_W_m']:,} W m<super>−1</super></b>".replace(",", " ")],
                 ["Bağıl L<sub>2</sub> / maks. hata (N = 101)", f"{fdm['rel_L2']:.1e} / {fdm['max_err']:.1e}"]],
                [70 * mm, content_w - 70 * mm]),
          Spacer(1, 6),
          table([["N", "bağıl L<sub>2</sub>", "maks. |hata|", "∫ θ(ξ,0) dξ"]] +
                [[str(n), f"{a:.2e}", f"{b:.2e}", f"{q:.4f}"]
                 for n, a, b, q in zip(cv_["N"], cv_["rel_L2"], cv_["max_err"], cv_["int_theta_bottom"])],
                [20 * mm, 32 * mm, 32 * mm, 32 * mm]),
          Spacer(1, 4),
          P(f"L<sub>2</sub> hatası p ≈ {cv_['order_L2']:.2f} ile ikinci mertebeye yakın yakınsıyor; maksimum hata ise yalnızca "
            f"p ≈ {cv_['order_max']:.2f}. Sebep alt köşeler: yan duvar θ = 1 isterken alt kenar soğuyor ve ∂θ/∂ξ köşede "
            "logaritmik olarak ıraksıyor. PINN'in de en çok burada zorlanması bekleniyor; Adım 5'te toplam kayıp yerine "
            "hata haritasına ve alt yüzey ısı akısına bakılacak."),
          P("Sıradaki: Adım 4 — PyTorch forward PINN (Dirichlet kenarları katı kısıt, kayıp = PDE + Robin, Adam → L-BFGS).", "sub")]

out = HERE / "report" / "case01_adim1-3_fdm_referans.pdf"
doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                        topMargin=14 * mm, bottomMargin=18 * mm,
                        title="Kolay PINN · Case 01 · Adım 1–3", author="Türkişi Engineering")
doc.build(story, onFirstPage=first_page, onLaterPages=later_pages)
print(out)
