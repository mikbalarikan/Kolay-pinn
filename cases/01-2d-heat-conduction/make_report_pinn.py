"""
Case 01 raporu (Adım 4–5) — forward PINN ve doğrulama, Türkişi kimlikli PDF.
Önce: üç pinn_forward.py koşusu ve python plot_pinn.py
Sonra: python make_report_pinn.py   ->  report/case01_adim4-5_forward_pinn.pdf
"""

import json
import subprocess
import sys
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Spacer

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from kolay_pinn.report import CONTENT_W, Report  # noqa: E402

S = json.loads((HERE / "data" / "summary_pinn.json").read_text())
S1 = json.loads((HERE / "data" / "summary.json").read_text())
U, K, X3, REF = S["uniform"], S["corner"], S["skip"], S["reference"]
share = json.loads((HERE / "lecture" / "ders02" / "assets" / "robin_share.json").read_text())["uniform"]
sci = lambda v: f"{v:.1e}".replace("e-0", "×10<super>−").replace("e-", "×10<super>−") + "</super>"  # noqa: E731
pct = lambda v: f"%{100 * v:.2f}"  # noqa: E731
fmt = lambda v: f"{v:,.0f}".replace(",", " ")  # noqa: E731

banner = HERE / "figures" / "banner_case01_pinn.png"
subprocess.run([sys.executable, str(ROOT / "brand" / "scripts" / "make_banner.py"),
                "--case", "CASE 01 · ADIM 4–5 · FORWARD PINN", "--out", str(banner.with_suffix(""))],
               check=True, capture_output=True)

R = Report(banner, "KOLAY PINN · Case 01 · 2D ısı iletimi · Adım 4–5", eq_dir=HERE / "report" / "eq_pinn")
R.equations({
    "hard": r"\hat\theta(\xi,\eta) = 1 + \xi\,(1-\xi)\,(1-\eta)\,\mathcal{N}(\xi,\eta)",
    "loss": r"\mathcal{L} = \frac{1}{N_r}\sum_{k=1}^{N_r}\big(\nabla^2\hat\theta(\mathbf{x}_k)\big)^2 + \frac{\lambda}{N_b}\sum_{m=1}^{N_b}\Big(\frac{\partial\hat\theta}{\partial\eta} - \mathrm{Bi}\,\hat\theta\Big)^2_{(\xi_m,0)}",
    "conflict": r"\left.\frac{\partial\theta}{\partial\eta}\right|_{\xi=0} = 0 \;\;(\text{yan duvar, } \theta\equiv1) \qquad\text{ama}\qquad \frac{\partial\theta}{\partial\eta} = \mathrm{Bi}\,\theta = \mathrm{Bi} \;\;(\text{Robin, köşede})",
    "relL2": r"\varepsilon_{L_2} = \|\hat\theta - \theta_{\mathrm{seri}}\|_2 \,/\, \|\theta_{\mathrm{seri}}\|_2",
})
P = R.P

R.story += [P("Adım 4–5: forward PINN ve referansa karşı doğrulama", "h1"),
            P("Ders 01'in problemi bir sinir ağıyla, çözüm verisi kullanmadan çözüldü ve seri çözüme karşı sınandı. "
              "Üç kolokasyon stratejisi karşılaştırıldı; kalan kaybın kaynağı köşe çelişkisi olarak belirlendi ve kaybın doğruluk ölçüsü olmadığı gösterildi.", "sub")]

R.story += [P("4 · Yöntem", "h2"),
            P("Ağ: 4 gizli katman × 50 nöron, tanh, Xavier başlatma, float64. Üç Dirichlet kenarı katı kısıtla ağın yapısına gömüldü:"),
            R.E("hard"),
            P("Kayıp yalnız iç noktalardaki Laplace artığı ile alt kenardaki Robin artığından oluşur (λ = 1; boyutsuz formda terimler aynı ölçekte). "
              "Türevler otomatik türevle, kesin olarak hesaplandı:"),
            R.E("loss"),
            R.table([["Ayar", "Değer"],
                     ["Kolokasyon", f"{U['n_int']} iç (Sobol) · {U['n_bot']} alt kenar (Sobol)"],
                     ["Eğitim", "Adam 6000 adım, lr 10<super>−3</super> → 10<super>−4</super> (üstel) · L-BFGS ≤ 2000 değerlendirme, strong Wolfe"],
                     ["Donanım", f"2 CPU çekirdeği · süre {U['t_total_s']:.0f}–{max(K['t_total_s'], X3['t_total_s']):.0f} s / koşu"],
                     ["Doğrulama", "seri çözüm (4000 terim), 201 × 201 ağ; FDM aynı ağda"]],
                    [32 * mm, CONTENT_W - 32 * mm]),
            Spacer(1, 4),
            P("Üç kolokasyon stratejisi: <b>düzgün</b>; <b>köşe sıklaştırma</b> (alt köşelere log-yoğun 1024 iç + 128 Robin noktası, "
              "FDM sezgisi); <b>köşe dışlama</b> (köşeden δ = 0.02 mesafedeki Robin noktaları kayıptan çıkarıldı).")]

legend = ("<b>Fig. 2 | Köşeye nokta eklemek hatayı artırır; köşeyi dışlamak kaybı düşürür ama hatayı değiştirmez.</b> "
          "<b>a</b>, üç koşunun toplam kaybı; gri bölge L-BFGS evresi. <b>b</b>, soğutulan yüzey boyunca seri çözüme göre mutlak hata; "
          "kesikli çizgi FDM (N = 201). <b>c–e</b>, 201 × 201 ağda log<sub>10</sub> mutlak hata haritaları; halkalar alt köşeler. "
          "Tüm koşularda aynı ağ, başlatma tohumu ve eğitim bütçesi; yalnız kolokasyon değişti.")
R.story += [Spacer(1, 4), R.figure(HERE / "figures" / "fig02_pinn_forward.png", 0.86, legend)]

rows = [["", "Bağıl L<sub>2</sub>", "İç bölge L<sub>2</sub>", "Maks. hata", "Alt orta T", "Q′ (W/m)", "Q′ hata"],
        ["Seri çözüm", "—", "—", "—", f"{20 + 50 * REF['theta_mid_bottom']:.2f} °C", fmt(REF["Q_W_m"]), "—"],
        ["FDM, N = 201", sci(REF["rel_L2_fdm_N201"]), "—", "—", "—", "—", "—"]]
for name, r in [("PINN, düzgün", U), ("PINN, köşe sıklaştırma", K), ("PINN, köşe dışlama", X3)]:
    rows.append([name, sci(r["rel_L2"]), sci(r["rel_L2_interior"]), sci(r["max_err"]), f"{r['T_mid_bottom_C']:.2f} °C",
                 fmt(r["Q_W_m"]), pct(r["Q_rel_err"])])
R.story += [P("5 · Sonuçlar", "h2"),
            R.table(rows, [38 * mm, 21 * mm, 22 * mm, 20 * mm, 22 * mm, 19 * mm, CONTENT_W - 142 * mm]),
            Spacer(1, 3), P("İç bölge: kenarlardan 0.05 L'lik şerit hariç. Hata ölçüsü:"), R.E("relL2", numbered=False)]

R.story += [R.section("Bulgu 1 · Kayıp tabanını köşe çelişkisi belirler",
            P(f"Eğitim sonunda kalan kaybın neredeyse tamamı Robin teriminden gelir; alt kenarın %2'lik köşe şeridi Robin kaybında "
              f"<b>%{100 * share:.0f} paya</b> sahiptir. Köşede artık |r| = Bi'ye ulaşır. Sebep fizikseldir:"),
            R.E("conflict", numbered=False),
            P("Hiçbir düzgün fonksiyon iki koşulu birden sağlayamaz; bu, Ders 01'deki köşe tekilliğinin kayıptaki yansımasıdır. "
              "Sonuç: PINN'de kaybın mutlak değeri doğruluk ölçüsü değildir; problem sıfır olmayan bir taban koyabilir.")),
            R.section("Bulgu 2 · FDM sezgisi PINN'e doğrudan taşınmaz",
            P(f"Köşe sıklaştırma bağıl L<sub>2</sub> hatayı {K['rel_L2'] / U['rel_L2']:.1f} kat <b>artırdı</b> ve bozulma iç bölgeye yayıldı "
              f"(iç bölge L<sub>2</sub> {K['rel_L2_interior'] / U['rel_L2_interior']:.1f} kat). FDM'de her düğüm kendi denklemini sağlar; "
              "PINN'de tek bir düzgün fonksiyon tüm artıkların ortalamasını küçültür. Sağlanamaz noktaları çoğaltmak kaybın ağırlığını "
              "imkânsız bir hedefe kaydırır.")),
            R.section("Bulgu 3 · Kaybın küçülmesi çözümün iyileştiği anlamına gelmez",
            P(f"Köşe dışlama son kaybı <b>{U['final_loss'] / X3['final_loss']:.0f} kat</b> düşürdü ({sci(U['final_loss'])} → {sci(X3['final_loss'])}), "
              f"ama bağıl L<sub>2</sub> hata neredeyse değişmedi ({sci(U['rel_L2'])} → {sci(X3['rel_L2'])}). Kayıp tabanı köşe çelişkisinden "
              "geliyordu ve çözümün geri kalanına zarar vermiyordu. PINN'in başarısı kayıpla değil, bağımsız bir referansla ölçülmelidir.")),
            R.section("Bulgu 4 · Bu problemde FDM üstündür",
            P(f"FDM aynı ağda {sci(REF['rel_L2_fdm_N201'])} bağıl hataya bir saniyenin altında ulaşır; PINN birkaç dakikada "
              f"{sci(min(U['rel_L2'], X3['rel_L2']))} seviyesindedir. PINN'in değeri ölçüm verisi (Adım 6), bilinmeyen parametre (Adım 7) "
              "ve parametrik çözüm (Adım 8) devreye girdiğinde ortaya çıkar.", "box")),
            P("Sıradaki: Adım 6 — FDM çözümünden seyrek, gürültülü ölçümlerle hibrit PINN.", "sub")]

out = R.build(HERE / "report" / "case01_adim4-5_forward_pinn.pdf", "Kolay PINN · Case 01 · Adım 4–5")
print(out)
