"""
Denklem dizgisi: tek LaTeX kaynağından
  - LaTeX ile dizilmiş saydam PNG (Latin Modern; slayt yedeği, PDF raporu)
  - PowerPoint'in düzenlenebilir denklem XML'i (OMML, pandoc ile)
üretir. Boyut, denklemin doğal boyutudur: `size` pt'de dizilir, slayta da o fiziksel boyutta konur.

    from kolay_pinn.mathtex import render_set
    render_set({"laplace": r"\\nabla^2\\theta = 0"}, out_dir, size=22, color="0D161F")

Gereken: pdflatex, pdftocairo (poppler), pandoc.
"""

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

PREAMBLE = r"""\documentclass[border=1.5pt]{standalone}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{amsmath,amssymb,bm}
\usepackage{xcolor}
\usepackage[utf8]{inputenc}
\begin{document}
"""


def _pdf_size_pt(pdf):
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout
    m = re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts", out)
    return float(m.group(1)), float(m.group(2))


def render_png(tex, png, size=22, color="0D161F", dpi=600, display=True):
    """LaTeX -> saydam PNG. Döner: (genişlik_inç, yükseklik_inç) doğal boyut."""
    body = (rf"\fontsize{{{size}}}{{{size * 1.25:.1f}}}\selectfont\color[HTML]{{{color}}}"
            + (rf"$\displaystyle {tex}$" if display else rf"{tex}"))
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "eq.tex").write_text(PREAMBLE + body + "\n\\end{document}\n", encoding="utf-8")
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "eq.tex"],
                           cwd=td, capture_output=True, text=True)
        if r.returncode != 0:
            err = "\n".join(l for l in r.stdout.splitlines() if l.startswith("!") or "l." in l)
            raise RuntimeError(f"LaTeX hatası: {tex}\n{err}")
        w, h = _pdf_size_pt(td / "eq.pdf")
        subprocess.run(["pdftocairo", "-png", "-singlefile", "-transp", "-r", str(dpi),
                        str(td / "eq.pdf"), str(td / "eq")], check=True)
        shutil.copy(td / "eq.png", png)
    return w / 72.0, h / 72.0


def latex_to_omml(tex):
    """LaTeX -> <m:oMath>…</m:oMath> (pandoc docx yolundan)."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "eq.md").write_text(f"$${tex}$$\n", encoding="utf-8")
        subprocess.run(["pandoc", "eq.md", "-o", "eq.docx"], cwd=td, check=True)
        xml = zipfile.ZipFile(td / "eq.docx").read("word/document.xml").decode("utf-8")
    m = re.search(r"<m:oMath>.*</m:oMath>", xml, re.S)
    if not m:
        raise RuntimeError(f"pandoc OMML üretmedi: {tex}")
    return m.group(0)


def render_set(eqs, out_dir, size=22, color="0D161F", omml=True):
    """
    eqs: {id: tex} ya da {id: {"tex":…, "size":…, "color":…}}
    Yazar: <id>.png, <id>.omml.xml ve index.json (id -> png, omml, w, h, size).
    Değişmeyen denklemler önbellekten atlanır.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    idx_path = out / "index.json"
    old = json.loads(idx_path.read_text()) if idx_path.exists() else {}
    index = {}
    for key, spec in eqs.items():
        spec = {"tex": spec} if isinstance(spec, str) else dict(spec)
        tex, sz, col = spec["tex"], spec.get("size", size), spec.get("color", color)
        digest = hashlib.sha1(f"{tex}|{sz}|{col}".encode()).hexdigest()[:12]
        png, om = out / f"{key}.png", out / f"{key}.omml.xml"
        if key in old and old[key].get("hash") == digest and png.exists() and (om.exists() or not omml):
            index[key] = old[key]
            continue
        w, h = render_png(tex, png, size=sz, color=col)
        if omml:
            om.write_text(latex_to_omml(tex), encoding="utf-8")
        index[key] = {"png": png.name, "omml": om.name if omml else None, "w": round(w, 4), "h": round(h, 4),
                      "size": sz, "color": col, "tex": tex, "hash": digest}
    idx_path.write_text(json.dumps(index, indent=1, ensure_ascii=False), encoding="utf-8")
    return index
