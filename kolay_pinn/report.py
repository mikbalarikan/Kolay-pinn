"""
Kimlikli teknik rapor iskeleti (reportlab): Türkişi kapak bandı, şerit, altbilgi, tablo ve LaTeX denklem yardımcıları.

    from kolay_pinn.report import Report
    R = Report(banner_png, header="KOLAY PINN · Case 01 · …")
    R.story += [R.P("Başlık", "h1"), R.E("loss"), R.table(rows, widths)]
    R.build(out_pdf, title="…")
"""

from pathlib import Path

from matplotlib import font_manager as fm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from kolay_pinn.mathtex import render_set
from kolay_pinn.style import C

PAGE_W, PAGE_H = A4
CONTENT_W = PAGE_W - 36 * mm
_FONTS = False


def _register_fonts():
    global _FONTS
    if _FONTS:
        return
    def f(family, weight="normal", style="normal"):
        return fm.findfont(fm.FontProperties(family=family, weight=weight, style=style), fallback_to_default=False)
    for name, fam, w, s in [("Body", "Liberation Sans", "normal", "normal"), ("BodyB", "Liberation Sans", "bold", "normal"),
                            ("BodyI", "Liberation Sans", "normal", "italic"), ("Mono", "DejaVu Sans Mono", "normal", "normal")]:
        try:
            pdfmetrics.registerFont(TTFont(name, f(fam, w, s)))
        except Exception:
            pdfmetrics.registerFont(TTFont(name, f("DejaVu Sans", w, s)))
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyB", italic="BodyI", boldItalic="BodyB")
    _FONTS = True


class Report:
    def __init__(self, banner_png, header, eq_dir=None):
        _register_fonts()
        self.banner = Path(banner_png)
        self.header = header
        self.col = {k: colors.HexColor(v) for k, v in C.items()}
        self.INK, self.MUTED = self.col["derin"], self.col["titanyum"]
        self.band_h = PAGE_W * 320 / 1280
        self.st = {
            "h1": ParagraphStyle("h1", fontName="BodyB", fontSize=15, leading=19, textColor=self.INK, spaceAfter=2),
            "sub": ParagraphStyle("sub", fontName="Body", fontSize=9, leading=12, textColor=self.MUTED, spaceAfter=8),
            "h2": ParagraphStyle("h2", fontName="BodyB", fontSize=10.5, leading=14, textColor=self.INK, spaceBefore=8, spaceAfter=3),
            "p": ParagraphStyle("p", fontName="Body", fontSize=8.6, leading=12.2, textColor=self.INK, alignment=TA_LEFT, spaceAfter=4),
            "cap": ParagraphStyle("cap", fontName="Body", fontSize=7.6, leading=10.4, textColor=self.INK, spaceBefore=3),
            "cell": ParagraphStyle("cell", fontName="Body", fontSize=7.8, leading=10, textColor=self.INK),
            "cellb": ParagraphStyle("cellb", fontName="BodyB", fontSize=7.8, leading=10, textColor=self.INK),
            "box": ParagraphStyle("box", fontName="Body", fontSize=8.4, leading=11.8, textColor=self.INK,
                                  backColor=self.col["krom"], borderPadding=(6, 8, 6, 8), spaceBefore=6, spaceAfter=8),
        }
        self.story = [Spacer(1, self.band_h - 12 * mm)]
        self.eq_dir, self.eqx, self._n = (Path(eq_dir) if eq_dir else None), {}, 0

    # ---- text & tables
    def P(self, text, style="p"):
        return Paragraph(text, self.st[style])

    def table(self, rows, widths, header=True):
        data = [[c if not isinstance(c, str) else self.P(c, "cellb" if (header and i == 0) else "cell") for c in r]
                for i, r in enumerate(rows)]
        t = Table(data, colWidths=widths, hAlign="LEFT")
        style = [("LINEABOVE", (0, 0), (-1, 0), 0.8, self.INK), ("LINEBELOW", (0, -1), (-1, -1), 0.8, self.INK),
                 ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                 ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5), ("LEFTPADDING", (0, 0), (-1, -1), 4)]
        if header:
            style.append(("LINEBELOW", (0, 0), (-1, 0), 0.4, self.MUTED))
        for r in range(2 if header else 1, len(rows), 2):
            style.append(("BACKGROUND", (0, r), (-1, r), self.col["kagit"]))
        t.setStyle(TableStyle(style))
        return t

    def figure(self, png, width_ratio, legend):
        """Figür + legend birlikte; width_ratio içerik genişliğine oran (1 = tam genişlik)."""
        from PIL import Image as PILImage
        w, h = PILImage.open(png).size
        fw = CONTENT_W * width_ratio
        img = Image(str(png), width=fw, height=fw * h / w)
        img.hAlign = "CENTER"
        return KeepTogether([img, self.P(legend, "cap")])

    def section(self, title, *flowables):
        """Başlığı ilk paragrafıyla birlikte tutar (sayfa sonunda yalnız başlık kalmaz)."""
        return KeepTogether([self.P(title, "h2"), *flowables])

    # ---- equations (LaTeX)
    def equations(self, eqs, size=10.5):
        self.eqx = render_set({k: {"tex": v, "size": size} for k, v in eqs.items()}, self.eq_dir,
                              color=C["derin"].lstrip("#"), omml=False)

    def E(self, key, numbered=True):
        e = self.eqx[key]
        img = Image(str(self.eq_dir / e["png"]), width=e["w"] * 72, height=e["h"] * 72)
        if numbered:
            self._n += 1
        t = Table([["", img, self.P(f"({self._n})" if numbered else "")]],
                  colWidths=[14 * mm, CONTENT_W - 28 * mm, 14 * mm], hAlign="CENTER")
        t.setStyle(TableStyle([("ALIGN", (1, 0), (1, 0), "CENTER"), ("ALIGN", (2, 0), (2, 0), "RIGHT"),
                               ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 4),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        return t

    # ---- page chrome
    def _first(self, cv, doc):
        cv.drawImage(str(self.banner), 0, PAGE_H - self.band_h, width=PAGE_W, height=self.band_h)
        self._footer(cv, doc)

    def _later(self, cv, doc):
        cv.setFillColor(self.col["celik_mavisi"]); cv.rect(0, PAGE_H - 3 * mm, PAGE_W, 3 * mm, stroke=0, fill=1)
        cv.setFillColor(self.col["kirmizi"]); cv.rect(0, PAGE_H - 3 * mm, 8 * mm, 3 * mm, stroke=0, fill=1)
        cv.setFont("Body", 7.5); cv.setFillColor(self.MUTED)
        cv.drawString(18 * mm, PAGE_H - 9 * mm, self.header)
        self._footer(cv, doc)

    def _footer(self, cv, doc):
        y, x0 = 10 * mm, 18 * mm
        s = 4.2 * mm / 100 * 1.6
        cv.saveState(); cv.translate(x0, y - 1.2 * mm); cv.scale(s, -s); cv.translate(0, -84)
        cv.setFillColor(self.INK)
        cv.rect(16, 20, 42, 11, stroke=0, fill=1); cv.rect(31, 20, 12, 52, stroke=0, fill=1)
        cv.rect(64, 38, 12, 34, stroke=0, fill=1); cv.rect(12, 72, 76, 3.5, stroke=0, fill=1)
        cv.setFillColor(self.col["kirmizi"]); cv.circle(70, 27, 6.5, stroke=0, fill=1)
        cv.restoreState()
        cv.setFont("Mono", 7); cv.setFillColor(self.INK)
        cv.drawString(x0 + 8 * mm, y, "TÜRKİŞİ ENGINEERING")
        cv.setFillColor(self.MUTED); cv.setFont("Body", 7)
        cv.drawCentredString(PAGE_W / 2, y, "github.com/mikbalarikan/kolay-pinn")
        cv.drawRightString(PAGE_W - 18 * mm, y, f"{doc.page}")
        cv.setStrokeColor(self.col["gumus"]); cv.setLineWidth(0.4)
        cv.line(18 * mm, y + 4 * mm, PAGE_W - 18 * mm, y + 4 * mm)

    def build(self, out, title):
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=14 * mm,
                                bottomMargin=18 * mm, title=title, author="Türkişi Engineering")
        doc.build(self.story, onFirstPage=self._first, onLaterPages=self._later)
        return out
