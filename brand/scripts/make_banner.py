"""
Repo banner: brand/banner_kolay_pinn.svg -> .png (rsvg-convert).
Kimlik: Lacivert Çelik katmanlı zemin, Krom yazı, Ti işareti (kırmızı nokta = kimlik),
kumpas maskotu, tek vurgu Fosfor Sarısı. Arka planda soluk Plan Camgöbeği izotermler.
Çalıştırma (repo kökünden):  python brand/scripts/make_banner.py [--case "CASE 01 · 2D ISI İLETİMİ"]
"""
import argparse, json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
C = {k: v["hex"] for k, v in json.loads((ROOT / "brand/palette.json").read_text(encoding="utf-8"))["colors"].items()}
W, H = 1280, 320


def ti_mark(x, y, s):
    hatch = "".join(f"M{v} 75.5 L{v - 5} 83 " for v in range(22, 83, 10))
    k = C["krom"]
    return (f'<g transform="translate({x},{y}) scale({s / 100})">'
            f'<rect x="16" y="20" width="42" height="11" fill="{k}"/><rect x="31" y="20" width="12" height="52" fill="{k}"/>'
            f'<rect x="64" y="38" width="12" height="34" fill="{k}"/><circle cx="70" cy="27" r="6.5" fill="{C["kirmizi"]}"/>'
            f'<rect x="12" y="72" width="76" height="3.5" fill="{k}"/><path d="{hatch}" stroke="{k}" stroke-width="2.2" fill="none"/></g>')


def mascot(x, y, s, expr="normal"):
    raw = (ROOT / f"brand/maskot_kumpas_{expr}.svg").read_text()
    inner = re.sub(r"^<svg[^>]*>|</svg>\s*$", "", raw.strip())
    return f'<g transform="translate({x},{y}) scale({s / 512})">{inner}</g>'


def isotherms():
    # soluk plaka izotermleri: banner'ın konusuna gönderme
    out = []
    for i, a in enumerate([0.25, 0.4, 0.55, 0.7, 0.85]):
        x0, x1, yb = 640, 1080, 300
        h = 40 + 46 * i
        out.append(f'<path d="M{x0},{yb} C{x0 + 18},{yb - h} {x1 - 18},{yb - h} {x1},{yb}" '
                   f'stroke="{C["plan"]}" stroke-opacity="{0.10 + 0.05 * i:.2f}" stroke-width="2" fill="none"/>')
    return "".join(out)


def grid():
    lines = [f"M{x},0 L{x},{H}" for x in range(0, W + 1, 40)] + [f"M0,{y} L{W},{y}" for y in range(0, H + 1, 40)]
    return f'<path d="{" ".join(lines)}" stroke="{C["krom"]}" stroke-opacity="0.045" stroke-width="1"/>'


def build(case):
    mono = "JetBrains Mono, DejaVu Sans Mono, Liberation Mono, monospace"
    disp = "Archivo, Inter Display, Inter, Arial, sans-serif"
    chip_w = 22 + 10.6 * len(case)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
 <linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{C["panel"]}"/><stop offset="1" stop-color="{C["gece"]}"/></linearGradient>
 <radialGradient id="pool" cx="0.72" cy="0.55" r="0.55"><stop offset="0" stop-color="{C["zemin"]}" stop-opacity="0"/><stop offset="1" stop-color="{C["gece"]}" stop-opacity="0.55"/></radialGradient>
</defs>
<rect width="{W}" height="{H}" fill="url(#g)"/>
{grid()}
{isotherms()}
<rect width="{W}" height="{H}" fill="url(#pool)"/>
{ti_mark(56, 34, 54)}
<text x="118" y="70" font-family="{mono}" font-size="17" letter-spacing="5" fill="{C["krom"]}">TÜRKİŞİ ENGINEERING</text>
<text x="58" y="172" font-family="{disp}" font-weight="900" font-size="92" letter-spacing="-1" fill="{C["krom"]}">KOLAY PINN</text>
<text x="62" y="214" font-family="{disp}" font-weight="500" font-size="24" fill="{C["gumus"]}">Fizik bilgili sinir ağları · adım adım, CFD/FDM referansıyla</text>
<rect x="62" y="240" width="{chip_w:.0f}" height="34" rx="3" fill="{C["fosfor_sarisi"]}"/>
<text x="73" y="263" font-family="{mono}" font-weight="700" font-size="16" letter-spacing="1" fill="{C["derin"]}">{case}</text>
<rect x="0" y="{H - 5}" width="{W}" height="5" fill="{C["celik_mavisi"]}"/>
<rect x="0" y="{H - 5}" width="38" height="5" fill="{C["kirmizi"]}"/>
{mascot(1046, 52, 210)}
</svg>'''


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default="PINN · CFD · FDM")
    ap.add_argument("--out", default=str(ROOT / "brand" / "banner_kolay_pinn"))
    a = ap.parse_args()
    svg = Path(a.out).with_suffix(".svg")
    svg.write_text(build(a.case), encoding="utf-8")
    subprocess.run(["rsvg-convert", "-w", str(2 * W), "-o", str(svg.with_suffix(".png")), str(svg)], check=True)
    print(svg, svg.with_suffix(".png"))
