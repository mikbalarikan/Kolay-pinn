"""
Case 01 raporu (Adım 6) — hibrit PINN: fizik + seyrek gürültülü ölçüm, Türkişi kimlikli PDF.
Önce: python hybrid_runs.py ; python hybrid_summary.py
Sonra: python make_report_hybrid.py   ->  report/case01_adim6_hibrit_pinn.pdf
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

S = json.loads((HERE / "data" / "summary_hybrid.json").read_text())
V, B, NZ, WB, CP = S["verdict"], S["count"]["0"]["rel_L2"], S["noise"], S["wrong_bi"], S["correct_physics_seed0"]
EPS = S["eps_model_no_data"]["gmean"]


def sci(v):
    m, e = f"{v:.1e}".split("e")
    e = int(e)
    return m if e == 0 else f"{m}×10<super>{'−' if e < 0 else ''}{abs(e)}</super>"


pct = lambda v: f"%{100 * v:.1f}"  # noqa: E731
rng = lambda r: f"{sci(r['gmean'])} [{sci(r['min'])}, {sci(r['max'])}]"  # noqa: E731
mu100 = V["config_gmean_ratio_vs_none"]["düzgün, μ = 100"]
filt = NZ["0.01"]["data_rmse_vs_noisy"] / NZ["0.01"]["data_rmse_vs_clean"]
n_need = round((0.01 / EPS) ** 2, -1)

banner = HERE / "figures" / "banner_case01_hibrit.png"
subprocess.run([sys.executable, str(ROOT / "brand" / "scripts" / "make_banner.py"),
                "--case", "CASE 01 · ADIM 6 · HİBRİT PINN", "--out", str(banner.with_suffix(""))],
               check=True, capture_output=True)

R = Report(banner, "KOLAY PINN · Case 01 · 2D ısı iletimi · Adım 6", eq_dir=HERE / "report" / "eq_hybrid")
R.equations({
    "hybrid": r"\mathcal{L} = \mathcal{L}_{\mathrm{PDE}} + \lambda\,\mathcal{L}_{\mathrm{Robin}} + \mu\,\frac{1}{N_d}\sum_{i=1}^{N_d}\big(\hat\theta(\mathbf{x}_i) - \theta_i^{\mathrm{ö}}\big)^2",
    "meas": r"\theta_i^{\mathrm{ö}} = \theta_{\mathrm{FDM}}(\mathbf{x}_i) + \varepsilon_i, \qquad \varepsilon_i \sim \mathcal{N}(0, \sigma^2), \qquad \sigma = 0.01 \;\Leftrightarrow\; 0.5\ ^\circ\mathrm{C}",
    "criterion": r"\frac{\sigma}{\sqrt{N_d}} \;<\; \varepsilon_{\mathrm{model}} = \mathrm{RMS}\big(\hat\theta - \theta\big)_{N_d = 0}",
    "wrong": r"\mathcal{L}_{\mathrm{Robin}} = \frac{1}{N_b}\sum_m\Big(\frac{\partial\hat\theta}{\partial\eta} - \mathrm{Bi}_{\mathrm{model}}\,\hat\theta\Big)^2, \qquad \mathrm{Bi}_{\mathrm{model}} = 2,\ \ \mathrm{Bi} = 4.895",
})
P = R.P

R.story += [P("Adım 6: hibrit PINN — fizik ile seyrek ölçümü aynı kayba koymak", "h1"),
            P("Forward PINN'in kaybına FDM çözümünden üretilmiş seyrek, gürültülü ölçümler eklendi. Sensör sayısı, yerleşim, veri ağırlığı "
              "ve gürültü üç tohumla tarandı; ayrıca kayıptaki Biot sayısı bilerek yanlış verilerek verinin yanlış fiziği ne ölçüde düzelttiği ölçüldü.", "sub")]

R.story += [P("6 · Yöntem", "h2"),
            P("Ağ, katı kısıt, kolokasyon ve eğitim Adım 4 ile aynıdır (4 × 50, tanh; 4096 iç + 256 Robin Sobol noktası; Adam 6000 + L-BFGS ≤ 2000). "
              "Kayba bir veri terimi eklendi:"),
            R.E("hybrid"),
            P("Ölçümler FDM (N = 201) iç düğümlerinden seçildi; gürültü sıfır ortalamalı Gauss:"),
            R.E("meas"),
            R.table([["Deney", "Değişken", "Sabit"],
                     ["Sensör sayısı", "N<sub>d</sub> = 0, 5, 20, 80 · 3 tohum", "σ = 0.01, düzgün, μ = 1"],
                     ["Yerleşim", "düzgün · köşe (r &lt; 0.2) · alt şerit (η &lt; 0.1) · 3 tohum", "N<sub>d</sub> = 20, σ = 0.01, μ = 1"],
                     ["Veri ağırlığı", "μ = 1, 100 · 3 tohum", "N<sub>d</sub> = 20, σ = 0.01, düzgün"],
                     ["Gürültü", "σ = 0, 0.01, 0.05 · tohum 0", "N<sub>d</sub> = 20, düzgün, μ = 1"],
                     ["Yanlış fizik", "Bi<sub>model</sub> = 2; N<sub>d</sub> = 0, 20, 80; μ = 1, 100 · tohum 0", "ölçüm ve doğrulama gerçek Bi ile"]],
                    [30 * mm, 78 * mm, CONTENT_W - 108 * mm]),
            Spacer(1, 3),
            P("N<sub>d</sub> = 0 satırları Adım 5'in üç tohumlu düzgün koşularıdır. Tohum hem ağırlık başlatmayı, Sobol kolokasyonunu hem sensör seçimini ve gürültüyü değiştirir. "
              "Doğrulama her koşuda gerçek Bi = 4.895'in seri çözümüne karşı 201 × 201 ağda yapıldı.")]

legend = ("<b>Fig. 4 | Fizik doğruyken seyrek veri hatayı değiştirmez; fizik yanlışken hatayı yalnız sınırlı ölçüde düşürür.</b> "
          "<b>a</b>, sensör sayısına göre bağıl L<sub>2</sub> hata, üç tohum; çizgi geometrik ortalama; gri bant veri yok koşularının aralığı. "
          "<b>b</b>, N<sub>d</sub> = 20'de yerleşim ve veri ağırlığı. <b>c</b>, tohum 0'da ağın sensörlerdeki değerinin gürültülü ölçüme (boş) ve gerçek değere (dolu) göre RMS farkı; "
          "yatay çizgi gürültü düzeyi; etiketler bağıl L<sub>2</sub>. <b>d</b>, kayıpta Bi = 2 kullanan koşular; kesikli çizgi doğru fizik, veri yok (tohum 0); etiketler ısı akısı Q′ hatası.")
R.story += [Spacer(1, 4), R.figure(HERE / "figures" / "fig04_hybrid.png", 0.95, legend)]

rows = [["", "Bağıl L<sub>2</sub>, geo. ort. [min, maks]", "Veri yok'a oran"]]
for g, v in S["count"].items():
    rows.append([f"N<sub>d</sub> = {g}", rng(v["rel_L2"]), f"{V['count_gmean_ratio_vs_none'][g]:.2f}"])
for g, v in S["config"].items():
    if g != "düzgün, μ = 1":
        rows.append([f"N<sub>d</sub> = 20, {g}", rng(v["rel_L2"]), f"{V['config_gmean_ratio_vs_none'][g]:.2f}"])
R.story += [P("7 · Sonuçlar", "h2"), R.table(rows, [52 * mm, 70 * mm, CONTENT_W - 122 * mm]), Spacer(1, 3)]

R.story += [R.section("Bulgu 1 · Fizik doğruyken seyrek veri bilgi taşımaz",
            P(f"Veri yok koşularının bağıl L<sub>2</sub> aralığı {sci(B['min'])} – {sci(B['max'])}. 5, 20 ve 80 sensör, köşe ve alt şerit yerleşimi bu aralığın dışına "
              f"iyileşme getirmedi; geometrik ortalamalar aralığın içinde ve biraz üstündedir. Gürültüsüz veri (σ = 0) bile tohum 0'da hatayı değiştirmedi "
              f"({sci(NZ['0.0']['rel_L2'])}, veri yokken {sci(CP['rel_L2'])}). Sebep, veri yokken modelin RMS hatasının (ε<sub>model</sub> ≈ {sci(EPS)}) "
              "ölçüm belirsizliğinden küçük olmasıdır:"),
            R.E("criterion", numbered=False),
            P(f"σ = 0.01 ve N<sub>d</sub> = 80'de σ/√N<sub>d</sub> = {sci(0.01 / 80 ** 0.5)}; ölçütün sağlanması için yaklaşık {n_need:.0f} sensör ya da on kat daha az gürültü gerekir. "
              "Ölçüt uzaysal dağılımı hesaba katmaz, ama mertebe olarak deney sonucunu öngörür.")),
            R.section("Bulgu 2 · Fizik gürültüyü süzer; büyük μ ise ağı gürültüye büker",
            P(f"σ = 0.01'de ağın sensörlerdeki değeri ölçüme {sci(NZ['0.01']['data_rmse_vs_noisy'])} (≈ σ), gerçeğe {sci(NZ['0.01']['data_rmse_vs_clean'])} uzaktır: "
              f"gerçeğe <b>{filt:.0f} kat</b> daha yakın. σ = 0.05'te (2.5 °C) de gerçeğe göre fark {sci(NZ['0.05']['data_rmse_vs_clean'])} kalır ve bağıl L<sub>2</sub> değişmez. "
              f"Laplace denklemi düzgün bir çözüm dayatır; ağ rastgele sıçramaları izleyemez. μ = 100 ise hatayı ortalamada {mu100:.1f} kat artırdı: veri terimi "
              "fizik terimleriyle yarışacak kadar güçlenince ağ gürültülü değerlere doğru yerel olarak bükülür ve hata alana yayılır.")),
            R.section("Bulgu 3 · Fizik yanlışken veri hatayı düşürür, ama çekişme sınır koyar",
            R.E("wrong", numbered=False),
            P(f"Yanlış fizikle veri yokken bağıl L<sub>2</sub> {sci(WB['veri yok']['rel_L2'])} (doğru fiziğin {V['wrong_bi_no_data_over_correct']:.0f} katı) ve "
              f"Q′ hatası {pct(WB['veri yok']['Q_rel_err'])}. μ = 1'de 20 sensör etkisizdir ({sci(WB['20 sensör μ = 1']['rel_L2'])}). μ = 100 ile 20 sensör "
              f"{sci(WB['20 sensör μ = 100']['rel_L2'])}, 80 sensör {sci(WB['80 sensör μ = 100']['rel_L2'])} verdi; Q′ hatası {pct(WB['80 sensör μ = 100']['Q_rel_err'])}'ya indi. "
              f"Hata en çok {V['wrong_bi_best_data_reduction']:.1f} kat düştü ve doğru fiziğin {V['wrong_bi_best_over_correct']:.0f} katında kaldı: yanlış Robin terimi ile ölçümler "
              "aynı ağı zıt yönlere çeker, μ yalnız uzlaşmanın yerini belirler.")),
            R.section("Bulgu 4 · Verinin asıl işlevi bilinmeyeni belirlemektir",
            P("Doğru fizikte seyrek veri sessiz, yanlış fizikte sınırlıdır. Ölçümün tam değeri, fiziğin bilinmeyen parametresi (burada Bi) ağırlıklarla birlikte "
              "öğrenildiğinde ortaya çıkar; çekişme ortadan kalkar. Ayrıca eğitim sonunda ölçüme göre RMSE'nin σ'yı belirgin biçimde aşması, referans çözüm olmadan "
              f"fiziğin yanlış olduğunu gösterir (yanlış Bi koşularında ağın sensörlerdeki gerçek hatası {sci(WB['20 sensör μ = 100']['data_rmse_vs_clean'])} – "
              f"{sci(WB['80 sensör μ = 100']['data_rmse_vs_clean'])}, σ'nın 3–4 katı).", "box")),
            Spacer(1, 4),
            R.table([["Yanlış fizik (tohum 0)", "Bağıl L<sub>2</sub>", "Q′ hata", "Sensörlerde ağ − gerçek"]] +
                    [[g, sci(v["rel_L2"]), pct(v["Q_rel_err"]), sci(v["data_rmse_vs_clean"]) if v["data_rmse_vs_clean"] else "—"] for g, v in WB.items()] +
                    [["Doğru fizik, veri yok", sci(CP["rel_L2"]), pct(CP["Q_rel_err"]), "—"]],
                    [52 * mm, 36 * mm, 30 * mm, CONTENT_W - 118 * mm]),
            Spacer(1, 3),
            P("Sıradaki: Adım 7 — ters problem: Bi'yi ölçümlerden ağ ağırlıklarıyla birlikte geri bulmak.", "sub")]

out = R.build(HERE / "report" / "case01_adim6_hibrit_pinn.pdf", "Kolay PINN · Case 01 · Adım 6")
print(out)
