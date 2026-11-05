"""
Case 01 raporu (Adım 7) — ters problem: Bi'yi iç sıcaklıklardan geri bulmak, Türkişi kimlikli PDF.
Önce: python inverse_classical.py ; python inverse_runs.py ; python inverse_summary.py
Sonra: python make_report_inverse.py   ->  report/case01_adim7_ters_problem.pdf
"""

import json
import subprocess
import sys
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.platypus import Spacer

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from kolay_pinn.report import CONTENT_W, Report  # noqa: E402

S = json.loads((HERE / "data" / "summary_inverse.json").read_text())
CL = json.loads((HERE / "data" / "inverse_classical.json").read_text())
BI, G, NZ, V, B10 = S["Bi_true"], S["groups"], S["noise"], S["verdict"], S["start_bi10"]
SENS = CL["sensitivity"]
base, nosk, top, bot = G["temel 20 düzgün"], G["köşe dışlama yok"], G["üst yarı"], G["alt şerit"]


def sci(v):
    m, e = f"{v:.1e}".split("e")
    e = int(e)
    return m if e == 0 else f"{m}×10<super>{'−' if e < 0 else ''}{abs(e)}</super>"


p1 = lambda v: f"%{100 * v:.1f}"  # noqa: E731
p2 = lambda v: f"%{100 * v:.2f}"  # noqa: E731
bis = lambda g: ", ".join(f"{r['Bi_hat']:.3f}" for r in g["runs"])  # noqa: E731
lss = lambda g: ", ".join(f"{r['fdm_ls_Bi']:.3f}" for r in g["runs"])  # noqa: E731

banner = HERE / "figures" / "banner_case01_ters.png"
subprocess.run([sys.executable, str(ROOT / "brand" / "scripts" / "make_banner.py"),
                "--case", "CASE 01 · ADIM 7 · TERS PROBLEM", "--out", str(banner.with_suffix(""))],
               check=True, capture_output=True)

R = Report(banner, "KOLAY PINN · Case 01 · 2D ısı iletimi · Adım 7", eq_dir=HERE / "report" / "eq_inverse")
R.equations({
    "inverse": r"\min_{\mathbf{w},\,s}\ \mathcal{L}_{\mathrm{PDE}} + \lambda\,\frac{1}{N_b}\sum_m\Big(\frac{\partial\hat\theta}{\partial\eta} - e^{s}\hat\theta\Big)^2 + \mu\,\frac{1}{N_d}\sum_{i=1}^{N_d}\big(\hat\theta(\mathbf{x}_i) - \theta_i^{\mathrm{ö}}\big)^2, \qquad \mathrm{Bi} = e^{s}",
    "sens": r"S(\mathbf{x}) = \frac{\partial\theta}{\partial\,\mathrm{Bi}} \approx \frac{\theta(\mathbf{x};\mathrm{Bi}+h) - \theta(\mathbf{x};\mathrm{Bi}-h)}{2h}, \qquad h = 10^{-3}\,\mathrm{Bi}",
    "crb": r"\sigma_{\mathrm{Bi}} \;\ge\; I(\mathrm{Bi})^{-1/2} = \frac{\sigma}{\sqrt{\sum_{i=1}^{N_d} S(\mathbf{x}_i)^2}}",
    "ls": r"\widehat{\mathrm{Bi}}_{\mathrm{EKK}} = \exp\Big(\arg\min_{q}\ \sum_{i}\big(\theta_{\mathrm{FDM}}(\mathbf{x}_i; e^{q}) - \theta_i^{\mathrm{ö}}\big)^2\Big)",
    "corner": r"\eta = 0,\ \xi \to 0:\quad r_{\mathrm{Robin}} = \frac{\partial\hat\theta}{\partial\eta} - \mathrm{Bi}\,\hat\theta \;\to\; -\mathrm{Bi}, \qquad \frac{\partial r^2}{\partial\,\mathrm{Bi}} = 2\,\mathrm{Bi}\,\hat\theta^2 > 0",
})
P = R.P

R.story += [P("Adım 7: ters problem — Bi'yi iç sıcaklıklardan geri bulmak", "h1"),
            P("Biot sayısı ağ ağırlıklarıyla birlikte öğrenilen bir parametre yapıldı ve plaka içindeki seyrek, gürültülü sıcaklık ölçümlerinden geri bulundu. "
              "Sonuçlar, aynı sensörlerle FDM + en küçük kareler kestirimi ve Cramér–Rao alt sınırıyla karşılaştırıldı.", "sub")]

R.story += [P("8 · Yöntem", "h2"),
            P("Ağ, katı kısıt, kolokasyon ve eğitim Adım 4 ile aynıdır; tek fark Robin terimindeki Bi'nin logaritmik bir parametre olmasıdır:"),
            R.E("inverse"),
            P("s, Adam'a ayrı bir parametre grubu olarak 10<super>−2</super> öğrenme oranıyla verildi (ağ 10<super>−3</super>); L-BFGS ağırlıklar ve s üzerinde birlikte çalıştı. "
              "Ölçümler Adım 6 ile aynı sanal sensörlerdir: FDM (N = 201, Bi = 4.895) iç düğümleri ve sıfır ortalamalı Gauss gürültüsü. "
              "Köşeden δ = 0.02 mesafedeki Robin noktaları kayıptan çıkarıldı (Bulgu 3). Ölçümlerin Bi'ye duyarlılığı FDM ile merkezi farktan hesaplandı:"),
            R.E("sens"),
            P("Gauss gürültüsünde Fisher bilgisi ∑S²/σ²'dir; Cramér–Rao eşitsizliği yansız her tahmincinin standart sapmasını alttan sınırlar:"),
            R.E("crb"),
            P("Klasik taban olarak FDM (N = 101) çözümü sensörlere doğrusal enterpolasyonla taşındı ve log Bi üzerinde en küçük kareler çözüldü (scipy least_squares):"),
            R.E("ls"),
            R.table([["Deney", "Değişken", "Sabit"],
                     ["Temel", "3 tohum", "Bi₀ = 1, N<sub>d</sub> = 20 düzgün, σ = 0.01, μ = 100, δ = 0.02"],
                     ["Köşe", "δ = 0 · 3 tohum", "temel"],
                     ["Yerleşim", "üst yarı (η &gt; 0.5) · alt şerit (η &lt; 0.1) · 3 tohum", "temel"],
                     ["Sensör sayısı", "N<sub>d</sub> = 5, 80 · 3 tohum", "temel"],
                     ["Veri ağırlığı", "μ = 1 · 3 tohum", "temel"],
                     ["Gürültü", "σ = 0, 0.05 · tohum 0", "temel"],
                     ["Başlangıç", "Bi₀ = 10 · tohum 0", "temel"]],
                    [28 * mm, 70 * mm, CONTENT_W - 98 * mm]),
            Spacer(1, 3),
            P("Tohum ağırlık başlatmayı, Sobol kolokasyonunu, sensör seçimini ve gürültüyü birlikte değiştirir; FDM + EKK her tohumda aynı sensörlerle çözüldü.")]

legend = ("<b>Fig. 8 | PINN, Bi'yi aynı veriden klasik yöntemle aynı doğrulukta, Cramér–Rao sınırı mertebesinde bulur; köşe dışlanmazsa aşağı yanlıdır.</b> "
          "<b>a</b>, her sensör kümesinde PINN ve FDM + en küçük kareler tahmini; kesik çizgiler gerçek Bi. "
          "<b>b</b>, göreli Bi hatası, üç tohum; dolu PINN, boş FDM + EKK; yatay çizgi tohumların ortalama Cramér–Rao sınırı σ<sub>Bi</sub>/Bi. "
          "<b>c</b>, eğitim boyunca Bi tahmini (tohum 0); dikey çizgi Adam'dan L-BFGS'e geçiş. "
          "<b>d</b>, 20 düzgün sensör, tohum 0'da gürültü düzeyine göre hata; etiketler ısı akısı Q′ hatası.")
R.story += [Spacer(1, 4), R.figure(HERE / "figures" / "fig08_inverse.png", 0.95, legend)]

rows = [["", "PINN Bi (3 tohum)", "PINN hata", "FDM + EKK hata", "CRB", "Bağıl L<sub>2</sub>"]]
for gname, v in G.items():
    rows.append([gname, bis(v), p1(v["pinn_rel_err_mean"]), p1(v["fdm_ls_rel_err_mean"]), p1(v["crb_rel"]), sci(v["rel_L2_gmean"])])
R.story += [P("9 · Sonuçlar", "h2"), R.table(rows, [30 * mm, 46 * mm, 20 * mm, 26 * mm, 16 * mm, CONTENT_W - 138 * mm]), Spacer(1, 2),
            P("Hatalar üç tohumun ortalama mutlak göreli hatasıdır; L<sub>2</sub> geometrik ortalama, gerçek Bi'nin seri çözümüne karşı.", "sub"), Spacer(1, 3)]

f1 = (f"Bi₀ = 10'dan başlayan koşu {B10['Bi_hat']:.3f} buldu (aynı tohum, Bi₀ = 1: {B10['same_as_bi0_1_seed0']:.3f}); başlangıç noktası sonucu belirlemedi. "
      if B10 else "")
mu1 = G.get("μ = 1")
f1b = (f"μ = 1'de veri terimi zayıf kalır ve Bi {bis(mu1)} olur; Adım 6'daki ölçek kuralı geçerlidir." if mu1 else "")
nz = " · ".join(f"σ = {s}: {p2(r['Bi_rel_err'])}" for s, r in NZ.items())
R.story += [R.section("Bulgu 1 · PINN, Bi'yi gürültünün izin verdiği doğrulukta bulur",
            P(f"Temel ayarda (Bi₀ = 1, 20 düzgün sensör, σ = 0.01) üç tohum {bis(base)} buldu; gerçek değer {BI:.3f}. "
              f"Ortalama hata {p1(base['pinn_rel_err_mean'])}, Cramér–Rao sınırı {p1(base['crb_rel'])}. Bi, Adam boyunca yavaş yükselir ve son yaklaşmayı L-BFGS yapar (Fig. 8c). "
              + f1 + f1b + f" Gürültüye göre tohum 0'da hata: {nz}.")),
            R.section("Bulgu 2 · Bilgi, soğutulan yüzeyin yakınındadır; yerleşim sayı kadar etkilidir",
            P(f"|∂θ/∂Bi| alt yüzey ortasında {SENS['max']:.3f}, merkezde {abs(SENS['center']):.4f}, üst yarıda en çok {SENS['top_half_max']:.3f}'tür. "
              f"20 sensör için Cramér–Rao sınırı alt şeritte {p1(bot['crb_rel'])}, düzgün yerleşimde {p1(base['crb_rel'])}, üst yarıda {p1(top['crb_rel'])}. "
              f"PINN hataları bu sıralamayı izledi: {p1(bot['pinn_rel_err_mean'])}, {p1(base['pinn_rel_err_mean'])}, {p1(top['pinn_rel_err_mean'])}. "
              "Sınır √N<sub>d</sub> ile ölçeklenir; sensörü alt şeride almak düzgün yerleşimde sensör sayısını 4–5 katına çıkarmaya denktir.")),
            R.section("Bulgu 3 · Köşe çelişkisi Bi'yi aşağı çeker",
            R.E("corner", numbered=False),
            P(f"Köşede yan duvar θ = 1 ve sıfır eğim dayattığı için Robin artığı −Bi'ye gider ve kayıp küçük Bi'yi ödüllendirir. Köşe noktaları dahilken (δ = 0) "
              f"üç tohum {bis(nosk)} buldu; aynı sensörlerle δ = 0.02'de {bis(base)}, FDM + EKK {lss(base)}. Ortalama yanlılık {V['noskip_bias_mean']:+.2f}. "
              "Modeldeki tekillik ters problemde parametre yanlılığına dönüşür; ölçümler bunu kendiliğinden düzeltmez.")),
            R.section("Bulgu 4 · Klasik yöntem aynı sonucu yüzlerce kat hızlı verir",
            P(f"Köşe dışlamalı koşularda PINN ile FDM + EKK tahmini arasındaki fark Bi'nin ortanca {p2(V['pinn_vs_fdm_ls_abs_diff_rel_median_skip'])}'sidir "
              f"(en çok {p1(V['pinn_vs_fdm_ls_abs_diff_rel_max_skip'])}): iki yöntem aynı veriden aynı Bi'yi bulur ve kalan hata gürültüden gelir. "
              f"Bir PINN koşusu ~{V['pinn_time_s_median']:.0f} s, FDM + EKK ~{V['fdm_ls_time_s_median']:.1f} s sürdü. Hızlı ve türevlenebilir bir çözücüsü olan tek parametreli "
              "bu problemde klasik yöntem tercih edilir. PINN'in ters problemdeki yeri pahalı çözücüler, alan olarak bilinmeyenler (örneğin h(ξ)) "
              "ve her Bi için çözüm veren parametrik ağlardır.", "box")),
            Spacer(1, 4),
            P("Sıradaki: Adım 8 — parametrik PINN: Bi'yi ağın girdisi yapmak ve ters problemi eğitimsiz bir aramaya dönüştürmek.", "sub")]

out = R.build(HERE / "report" / "case01_adim7_ters_problem.pdf", "Kolay PINN · Case 01 · Adım 7")
print(out)
