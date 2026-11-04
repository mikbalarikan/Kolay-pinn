"""
Case 01 raporu (Adım 7) — ters problem: Bi'yi iç sıcaklık ölçümlerinden geri bulmak, Türkişi kimlikli PDF.
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
V, MS, MK, G, X = S["verdict"], S["mu_scan"], S["mu_scan_skip"], S["groups"], S["extra"]
BI = S["Bi_true"]


def sci(v):
    m, e = f"{v:.1e}".split("e")
    e = int(e)
    return m if e == 0 else f"{m}×10<super>{'−' if e < 0 else ''}{abs(e)}</super>"


pct = lambda v: f"%{100 * v:.1f}"  # noqa: E731
sg = lambda v: f"{'+' if v >= 0 else '−'}%{100 * abs(v):.1f}"  # noqa: E731
f3 = lambda v: f"{v:.3f}"  # noqa: E731
crlb_pct = {k: sum(CL["configs"][k]["seeds"][f"s{s}"]["crlb_sigma_Bi"] for s in (0, 1, 2)) / 3 / BI
            for k in CL["configs"]}

banner = HERE / "figures" / "banner_case01_ters.png"
subprocess.run([sys.executable, str(ROOT / "brand" / "scripts" / "make_banner.py"),
                "--case", "CASE 01 · ADIM 7 · TERS PROBLEM", "--out", str(banner.with_suffix(""))],
               check=True, capture_output=True)

R = Report(banner, "KOLAY PINN · Case 01 · 2D ısı iletimi · Adım 7", eq_dir=HERE / "report" / "eq_inverse")
R.equations({
    "inverse": r"\min_{\mathbf{w},\,\beta}\ \mathcal{L}_{\mathrm{PDE}}(\mathbf{w}) + \lambda\,\mathcal{L}_{\mathrm{Robin}}(\mathbf{w}, e^{\beta}) + \mu\,\frac{1}{N_d}\sum_{i=1}^{N_d}\big(\hat\theta(\mathbf{x}_i;\mathbf{w}) - \theta_i^{\mathrm{ö}}\big)^2, \qquad \mathrm{Bi} = e^{\beta}",
    "classical": r"\mathrm{Bi}^{*} = \arg\min_{\mathrm{Bi}} \sum_{i=1}^{N_d}\big(\theta_{\mathrm{seri}}(\mathbf{x}_i;\mathrm{Bi}) - \theta_i^{\mathrm{ö}}\big)^2, \qquad \sigma_{\mathrm{Bi}} \geq \frac{\sigma}{\sqrt{\sum_i S(\mathbf{x}_i)^2}}, \quad S = \frac{\partial\theta}{\partial\mathrm{Bi}}",
    "bias": r"\mathcal{L}_{\mathrm{Robin}}\big|_{\text{köşe}} \approx c\,\mathrm{Bi}^2 \quad\Rightarrow\quad \mathrm{Bi}_{\mathrm{PINN}} \approx \frac{\mu\,m}{c + \mu\,m}\,\mathrm{Bi}^{*}, \qquad m = \frac{1}{N_d}\sum_i S(\mathbf{x}_i)^2",
})
P = R.P

R.story += [P("Adım 7: ters problem — Biot sayısını iç sıcaklıklardan geri bulmak", "h1"),
            P("Adım 6'nın yanlış fizik deneyinin doğal devamı: kayıptaki Bi artık sabit değil, ağ ağırlıklarıyla birlikte öğrenilen bir parametre. "
              "Aynı ters problem seri çözüm ve en küçük karelerle de çözüldü; Cramér–Rao alt sınırı her sensör kümesinin ulaşılabilir doğruluğunu verdi.", "sub")]

R.story += [P("8 · Yöntem", "h2"),
            P("Ağ, katı kısıt, kolokasyon ve eğitim Adım 6 ile aynıdır (4 × 50, tanh; 4096 iç + 256 Robin Sobol noktası; Adam 6000 + L-BFGS ≤ 2000). "
              "Robin koşulundaki Bi, pozitif kalması için ln Bi = β üzerinden öğrenilir; β Adam'da 10<super>−2</super>, ağırlıklar 10<super>−3</super> öğrenme oranıyla, "
              "L-BFGS'te birlikte güncellenir. Başlangıç Bi<sub>0</sub> = 2 (Adım 6'nın yanlış değeri). Ölçümler Adım 6 ile aynıdır: FDM (N = 201) iç düğümleri, σ = 0.01 (≙ 0.5 °C)."),
            R.E("inverse"),
            P("Klasik referans aynı sensör kümelerini kullanır; ileri model analitik seri çözümdür (veriyi üreten FDM'den farklı, ters suç yok). "
              "Duyarlılık S ile Fisher bilgisi ve Cramér–Rao sınırı hesaplandı; her küme için 100–400 gürültü gerçeklemesiyle Monte Carlo yapıldı:"),
            R.E("classical"),
            R.table([["Deney", "Değişken", "Sabit"],
                     ["Veri ağırlığı, δ = 0", "μ = 1, 10, 100, 1000 · tohum 0", "N<sub>d</sub> = 20, düzgün"],
                     ["Veri ağırlığı, δ = 0.02", "μ = 1, 100, 1000; μ = 1 + ısınma · tohum 0", "N<sub>d</sub> = 20, düzgün"],
                     ["Sensör sayısı", "N<sub>d</sub> = 5, 20, 80 · 3 tohum", "δ = 0.02, μ = 100, düzgün"],
                     ["Yerleşim", "üst yarı (η &gt; 0.5) · alt şerit (η &lt; 0.1) · 3 tohum", "N<sub>d</sub> = 20, δ = 0.02, μ = 100"],
                     ["Gürültü, başlangıç", "σ = 0, 0.05 · Bi<sub>0</sub> = 0.5, 8 · tohum 0", "N<sub>d</sub> = 20, δ = 0.02, μ = 100"]],
                    [36 * mm, 76 * mm, CONTENT_W - 112 * mm]),
            Spacer(1, 3),
            P("δ: köşeden bu mesafedeki Robin noktalarının kayıptan çıkarılması (Adım 5). Tohum ağırlık başlatmayı, kolokasyonu, sensör seçimini ve gürültüyü değiştirir; "
              "klasik çözüm her tohumda aynı sensör ve gürültüyü kullanır.")]

legend = ("<b>Fig. 5 | Köşe çelişkisi Bi'yi öngörülebilir biçimde aşağı çeker; köşe dışlanınca PINN klasik tahminin gürültü sınırına ulaşır.</b> "
          "<b>a</b>, öğrenilen Bi'nin eğitim boyunca yolu (tohum 0, N<sub>d</sub> = 20); kesikli çizgi gerçek değer. "
          "<b>b</b>, veri ağırlığı μ; çizgi Adım 5'ten alınan köşe tabanı c ile öngörü, gri bant aynı verinin klasik tahmini ± Cramér–Rao sınırı. "
          "<b>c</b>, duyarlılık −∂θ/∂Bi ve üç sensör yerleşimi (tohum 0). "
          "<b>d</b>, önerilen ayarda (δ = 0.02, μ = 100) PINN (dolu) ve aynı verinin klasik tahmini ± σ<sub>CR</sub> (boş); her nokta bir tohum.")
R.story += [Spacer(1, 4), R.figure(HERE / "figures" / "fig05_inverse.png", 0.95, legend)]

rows = [["N<sub>d</sub>, yerleşim (δ = 0.02, μ = 100)", "PINN Bi (3 tohum)", "Klasik Bi* (aynı veri)", "σ<sub>CR</sub>", "|PINN − klasik| / σ<sub>CR</sub>", "Bağıl L<sub>2</sub>"]]
for g, v in G.items():
    rows.append([g, " · ".join(f3(r["Bi_est"]) for r in v["runs"]), " · ".join(f3(r["Bi_classical"]) for r in v["runs"]),
                 f"{v['mean_crlb']:.3f}", f"{v['gap_over_crlb']:.2f}", sci(v["rel_L2_gmean"])])
R.story += [P("9 · Sonuçlar", "h2"), R.table(rows, [38 * mm, 36 * mm, 36 * mm, 14 * mm, 24 * mm, CONTENT_W - 148 * mm]), Spacer(1, 3)]

R.story += [R.section("Bulgu 1 · Saf kayıpla Bi sıfıra çöker",
            P(f"δ = 0, μ = 1 ile Bi, 2'den {f3(MS['1']['Bi_est'])}'e indi. Başlangıçta θ̂ ≈ 1 olduğundan Robin artığı ≈ −Bi ve Robin kaybı ≈ Bi²; "
              "Bi'yi küçültmek kaybı düşürmenin en ucuz yoludur. Bi → 0'da θ ≡ 1 fiziği tam sağlar, bedeli yalnız veri terimidir (≈ 0.02). "
              f"Doğru Bi'de ise köşe çelişkisi Robin kaybına ≈ {S['c_corner'] * BI ** 2:.2f}'lik bir taban ekler (Adım 5). Yani μ = 1'de yanlış çözüm "
              "kaybın gerçek minimumudur; optimizasyon değil, kayıp yanlıştır.")),
            R.section("Bulgu 2 · Köşe yanlılığı önceden hesaplanabilir",
            R.E("bias", numbered=False),
            P(f"c, Adım 5'in üç tohumlu forward koşularından (son Robin kaybı / Bi²) {sci(S['c_corner'])}; m, tohum 0'ın 20 sensöründe {sci(S['m_n20_s0'])}. "
              f"Ters koşulara bakmadan yapılan öngörü μ = 100'de {f3(MS['100']['Bi_pred'])}, PINN {f3(MS['100']['Bi_est'])}; "
              f"μ = 1000'de {f3(MS['1000']['Bi_pred'])} ve {f3(MS['1000']['Bi_est'])}. μ = 1 ve 10'da öngörü ({f3(MS['1']['Bi_pred'])}, {f3(MS['10']['Bi_pred'])}) "
              f"çöküşü niteliksel olarak doğru verir ({f3(MS['1']['Bi_est'])}, {f3(MS['10']['Bi_est'])}). Yanlılık μ ile azalır ama sıfırlanmaz; "
              "çok büyük μ ise Adım 6'da görüldüğü gibi ağı gürültüye büker.")),
            R.section("Bulgu 3 · Köşeyi dışlamak gerekli; ısınma tek başına yetmez",
            P(f"δ = 0.02 köşe tabanını ~{S['c_corner'] / S['c_skip']:.0f} kat düşürür. μ = 100 ile Bi = {f3(MK['100']['Bi_est'])} (klasik, aynı veri: "
              f"{f3(S['Bi_classical_n20_s0'])}). μ = 1'de ise δ = 0.02 de yetmedi: Bi = {f3(MK['1']['Bi_est'])}. Kayıp yüzeyinin gerçek minimumu doğru Bi'ye yakın olsa da "
              f"Adam'ın ilk binlerce adımında Bi Robin terimini küçültmek için küçülür ve geri dönemez. Önce PDE + veriyle ısınıp Bi'yi en küçük karelerle başlatmak da "
              f"çöküşü önlemedi ({f3(X['ısınma, μ = 1']['Bi_est'])}): Robin açıldığında aynı gradyan baskın. Gerekli olan, veri teriminin optimizasyon boyunca Robin kaybıyla "
              "aynı mertebede tutulmasıdır (μσ² ~ L<sub>Robin</sub>).")),
            R.section("Bulgu 4 · Önerilen ayarda PINN klasik yöntemin gürültü sınırına ulaşır",
            P(f"δ = 0.02, μ = 100 ile 20 düzgün sensörde ortalama mutlak Bi hatası {pct(G['20 düzgün']['mean_abs_rel_err'])}. PINN ile aynı verinin klasik tahmini arasındaki fark, "
              f"Cramér–Rao sınırının {G['20 düzgün']['gap_over_crlb']:.2f} katı: kalan hata gürültüden gelir, yöntemden değil. "
              f"Gürültüsüz veride PINN {f3(X['σ = 0']['Bi_est'])} (klasik {f3(X['σ = 0']['Bi_classical'])}); "
              f"başlangıç Bi<sub>0</sub> = 0.5 ve 8 ile {f3(X['Bi₀ = 0.5']['Bi_est'])} ve {f3(X['Bi₀ = 8']['Bi_est'])}. "
              f"Alan hatası (bağıl L<sub>2</sub> {sci(V['recommended_rel_L2_gmean'])}) Adım 6'nın yanlış fiziğinden (9.2×10<super>−2</super>) iki mertebe küçük.", "box")),
            R.section("Bulgu 5 · Doğruluğu sensör sayısı değil sensör yeri belirler",
            P(f"Duyarlılık soğutulan yüzeyde toplanır ve üst yarıda hızla söner. Cramér–Rao sınırı 20 sensörde üst yarıda %{100 * crlb_pct['n20_top']:.1f}, "
              f"düzgünde %{100 * crlb_pct['n20_uniform']:.1f}, alt şeritte %{100 * crlb_pct['n20_bottom']:.1f}; alt şeritteki 20 sensör, düzgün dağılmış 80 sensörle "
              f"(%{100 * crlb_pct['n80_uniform']:.1f}) aynı bilgiyi taşır. Monte Carlo yayılımı sınırla örtüşür (doğrusal rejim). PINN bu sıralamayı izler: "
              f"üst yarı |PINN − klasik|/σ<sub>CR</sub> = {G['20 üst yarı']['gap_over_crlb']:.2f}, alt şerit {G['20 alt şerit']['gap_over_crlb']:.2f}. "
              "Deney tasarımı PINN eğitiminden önce, ucuz klasik modelle yapılabilir."))]

R.story += [Spacer(1, 4),
            R.table([["Ek koşular (tohum 0, N<sub>d</sub> = 20)", "Bi", "Bi hatası", "Bağıl L<sub>2</sub>", "Q′ hatası (öğrenilen h ile)"]] +
                    [[f"δ = 0, μ = {k}", f3(v["Bi_est"]), sg(v["Bi_rel_err"]), sci(v["rel_L2"]), sg(v["Q_rel_err_est"])] for k, v in MS.items()] +
                    [[f"δ = 0.02, μ = {k}", f3(v["Bi_est"]), sg(v["Bi_rel_err"]), sci(v["rel_L2"]), sg(v["Q_rel_err_est"])] for k, v in MK.items()] +
                    [[f"δ = 0.02, μ = 100, {k}" if "μ" not in k else f"δ = 0.02, {k}", f3(v["Bi_est"]), sg(v["Bi_rel_err"]), sci(v["rel_L2"]),
                      sg(v["Q_rel_err_est"])] for k, v in X.items()],
                    [56 * mm, 20 * mm, 24 * mm, 26 * mm, CONTENT_W - 126 * mm]),
            Spacer(1, 3),
            P("Sıradaki: Adım 8 — parametrik vekil model: Bi'yi girdi yapıp tek eğitimle tüm Bi aralığını çözmek.", "sub")]

out = R.build(HERE / "report" / "case01_adim7_ters_problem.pdf", "Kolay PINN · Case 01 · Adım 7")
print(out)
