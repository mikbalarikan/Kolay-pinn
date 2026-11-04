/**
 * Ders 03 · Hibrit PINN: fizik ile seyrek ölçümü aynı kayba koymak (Adım 6)
 * Önce:  python hybrid_runs.py ; python hybrid_summary.py
 *        python lecture/ders03/equations.py ; python lecture/ders03/make_slide_figures.py
 * Sonra: node lecture/ders03/build_lecture.js  ->  lecture/ders03/ders03_hibrit_pinn.pptx
 */
const fs = require("fs");
const path = require("path");
const D = require(path.join(__dirname, "..", "..", "..", "..", "kolay_pinn", "deck", "turkisi_deck.js"));

const CASE = path.join(__dirname, "..", "..");
const ASSETS = path.join(__dirname, "assets");
const S = JSON.parse(fs.readFileSync(path.join(CASE, "data", "summary_hybrid.json"), "utf8"));
const deck = D.createDeck({ course: "KOLAY PINN", lecture: "Ders 03 · Hibrit PINN", assets: ASSETS,
  eqDir: path.join(ASSETS, "eq"), title: "Kolay PINN · Ders 03 · Hibrit PINN: fizik + seyrek ölçüm" });
const { pres, C, W, M, BODY_TOP, hex } = deck;
const YL = "YÜKSEK LİSANS";
const V = S.verdict, B = S.count["0"].rel_L2, CFG = S.config, NZ = S.noise, WB = S.wrong_bi, CP = S.correct_physics_seed0;
const pct = (v) => `%${(100 * v).toFixed(0)}`;
const x = (v) => v.toFixed(1).replace(".0", "");
const muRatio = V.config_gmean_ratio_vs_none["düzgün, μ = 100"];
const filt = NZ["0.01"].data_rmse_vs_noisy / NZ["0.01"].data_rmse_vs_clean;
const EPS = S.eps_model_no_data.gmean;
const nNeed = Math.round((0.01 / EPS) ** 2 / 10) * 10;
const W0 = WB["veri yok"], W1 = WB["20 sensör μ = 1"], W2 = WB["20 sensör μ = 100"], W3 = WB["80 sensör μ = 100"];

const STEPS = [
  { n: 1, t: "Problemi tanımla" }, { n: 2, t: "Boyutsuzlaştır" }, { n: 3, t: "FDM referansı" },
  { n: 4, t: "Forward PINN" }, { n: 5, t: "Doğrula" }, { n: 6, t: "Hibrit PINN" },
  { n: 7, t: "Ters problem" }, { n: 8, t: "Parametrik PINN" }, { n: 9, t: "Framework" },
];
const LOCAL = ["Veriyi kayba ekle", "Doğru fizik", "Yanlış fizik"].map((t, i) => ({ n: i + 1, t }));

// =========================================================== GİRİŞ
pres.addSection({ title: "Giriş" });
{
  const s = pres.addSlide({ masterName: "KAPAK", sectionTitle: "Giriş" });
  deck.chip(s, "KOLAY PINN · DERS 03", M, 1.7);
  s.addText("Hibrit PINN:\nfizik + seyrek ölçüm", { x: M, y: 2.2, w: 8.6, h: 2.0, fontSize: 44, bold: true,
    color: C.background2, margin: 0, valign: "top", isTextBox: true, objectName: "cover_title" });
  s.addText("Veri terimi ve ağırlığı · sensör sayısı, yerleşim, gürültü · doğru ve yanlış fizikte verinin değeri",
    { x: M, y: 4.35, w: 8.6, h: 0.9, fontSize: 18, color: hex("gumus"), margin: 0, valign: "top", isTextBox: true, objectName: "cover_sub" });
  s.addText("Lisans ve yüksek lisans · Adım 6 · yaklaşık 45 dakika", { x: M, y: 6.2, w: 8, h: 0.4, fontSize: 13,
    color: hex("titanyum"), margin: 0, isTextBox: true, objectName: "cover_meta" });
  s.addImage({ path: deck.A("maskot_mutlu.png"), x: 9.4, y: 1.6, w: 3.4, h: 3.4, objectName: "cover_mascot" });
  s.addNotes("Geçen derste PINN'i hiç veri kullanmadan, yalnız fizikle eğittik. Bugün kayba birkaç gürültülü ölçüm ekliyoruz. " +
    "Ölçümleri FDM çözümünden, yani CFD yerine geçen referanstan alıp gürültü ekleyerek üretiyoruz. " +
    "Sorumuz basit ama cevabı şaşırtıcı: veri ne zaman işe yarar? Önce fizik doğruyken, sonra fiziği bilerek yanlış verip bakacağız.");
}
{
  const s = deck.content("Giriş", "Bu dersin sonunda dört şeyi yapabileceksiniz", {
    notes: "Birinci hedef teknik: veri terimini yazmak ve ağırlığını kayıp terimlerinin büyüklüğüne bakarak seçmek. " +
      "İkincisi deneysel: sensör sayısı, yerleşim ve gürültünün etkisini tohum aralığıyla birlikte okumak; Ders 02'deki kuralı burada kullanıyoruz. " +
      "Üçüncüsü bu dersin ana fikri: fiziğin gürültüyü süzmesi. Dördüncüsü yüksek lisans: verinin değerini deney yapmadan, model hatası ile gürültüyü karşılaştırarak tahmin etmek." });
  const objs = [
    ["Veri terimini kayba eklemek", "Ağırlığı μ'yü kayıp terimlerinin ölçeğine bakarak seçmek."],
    ["Deneyi doğru okumak", "Sensör sayısı, yerleşim ve gürültüyü üç tohumun aralığıyla karşılaştırmak."],
    ["Fiziğin süzgecini görmek", "Ağın ölçüme değil gerçeğe yakın oturduğunu göstermek."],
    ["Verinin değerini tahmin etmek", "σ/√N_d ile model hatasını karşılaştırmak; yanlış fizikte verinin sınırını görmek."],
  ];
  const cw = (W - 2 * M - 0.3) / 2, ch = 2.05;
  objs.forEach(([h, b], i) => deck.card(s, { x: M + (i % 2) * (cw + 0.3), y: BODY_TOP + Math.floor(i / 2) * (ch + 0.3),
    w: cw, h: ch, head: h, body: b, num: i + 1, headSize: 18, bodySize: 15 }));
}
{
  const s = deck.content("Giriş", "Bugün forward PINN'e ölçüm ekliyoruz; referans hâlâ seri çözüm", {
    notes: "Yol haritasında altıncı adımdayız. Ders 02'den iki şey getiriyoruz: aynı ağ ve eğitim, ve veri yokken üç tohumun hata aralığı. " +
      `O aralık on üzeri eksi dört mertebesinde: ${deck.sci(B.min)} ile ${deck.sci(B.max)} arası. Bugün her sonucu bu banda göre okuyacağız.` });
  deck.roadmap(s, STEPS, new Set([6]), { y: 2.6 });
  deck.card(s, { x: M, y: 4.6, w: 5.9, h: 1.6, head: "Ders 02'den gelen taban",
    body: `Veri yok, 3 tohum: bağıl L₂ ${deck.sci(B.min)} – ${deck.sci(B.max)}. Ağ, kolokasyon ve eğitim aynen korunuyor.` });
  deck.card(s, { x: M + 6.2, y: 4.6, w: W - 2 * M - 6.2, h: 1.6, head: "Ölçümler nereden?",
    body: "FDM (N = 201) iç düğümlerinden seçilip Gauss gürültüsü eklenir; CFD verisinin yerine geçer." });
}
{
  const s = deck.content("Giriş", "Bu derste altı kavrama yaslanacağız", {
    notes: "Sözlük. Veri terimi: sensörlerde ağın tahmini ile ölçüm arasındaki farkın ortalama karesi. Mu bu terimin ağırlığı. " +
      "Gürültü sıfır ortalamalı, sigma sapmalı. Model hatası: veri olmadan PINN'in gerçekten ne kadar uzak olduğu. " +
      "Yanlış fizik: kayıptaki modelin gerçeği yanlış temsil etmesi; bizde Biot sayısı. Süzgeç: ağın ölçüme gürültü kadar uzak, gerçeğe yakın oturması." });
  const terms = [
    ["Veri terimi", "g_data", "Sensörlerde tahmin − ölçüm", 0.8],
    ["Veri ağırlığı", "g_mu", "Fizik terimlerine göre önem", 1],
    ["Ölçüm gürültüsü", "g_noise", "σ = 0.01 ≙ 0.5 °C", 1],
    ["Model hatası", "g_model", "Veri yokken PINN − gerçek", 0.95],
    ["Yanlış fizik", "g_wrong", "Kayıptaki model gerçeği temsil etmiyor", 1],
    ["Fizik süzgeci", "g_filter", "Ağ gürültüyü değil fiziği izler", 1],
  ];
  const cw = (W - 2 * M - 0.6) / 3, ch = 2.15;
  terms.forEach(([h, m, b, sc], i) => deck.card(s, { x: M + (i % 3) * (cw + 0.3), y: BODY_TOP + Math.floor(i / 3) * (ch + 0.25),
    w: cw, h: ch, head: h, math: m, mathScale: sc, body: b, headSize: 17, bodySize: 14 }));
}

// =========================================================== 1 · VERİYİ KAYBA EKLE
const SEC1 = "1 · Veriyi kayba ekle";
deck.section(SEC1, "01", "Veriyi kayba ekle", "Veri terimi, sanal sensörler ve terimlerin ölçeği",
  { roadmapSteps: LOCAL, active: new Set([1]), notes: "Birinci bölüm: veriyi kayba nasıl eklediğimiz ve ağırlığını neye göre seçtiğimiz." });
{
  const s = deck.content(SEC1, "Hibrit kayıp, Ders 02'nin kaybına tek bir terim ekler", { step: "ADIM 6 · KAYIP",
    notes: "Fizik kısmı Ders 02 ile aynı: iç noktalarda Laplace artığı, alt kenarda Robin artığı. Dirichlet kenarları yine katı kısıtta. " +
      "Yeni terim: N_d sensörde ağın tahmini ile ölçüm arasındaki farkın ortalama karesi, mu ağırlığıyla. " +
      "Ölçüm, FDM değerine sıfır ortalamalı Gauss gürültüsü eklenerek üretiliyor. Sigma 0.01 boyutsuz; sıcaklık farkı 50 derece olduğu için yarım dereceye karşılık geliyor, tipik bir termokupl belirsizliği." });
  deck.mathBox(s, ["hybrid"], { x: M, y: BODY_TOP, w: W - 2 * M, h: 1.75 });
  deck.mathBox(s, ["meas", "sigma_C"], { x: M, y: BODY_TOP + 2.0, w: 7.6, h: 1.75, gap: 0.3, scale: 0.9 });
  deck.card(s, { x: M + 7.9, y: BODY_TOP + 2.0, w: W - 2 * M - 7.9, h: 1.75, head: "Kodda tek satır",
    body: "l_dat = ((theta_hat(model, Xd) − yd)²).mean()" });
  deck.caption(s, "Ağ, kolokasyon, katı kısıt ve eğitim Ders 02 ile aynı; yalnız veri terimi ve ağırlığı μ değişiyor.",
    { x: M, y: BODY_TOP + 4.0, w: W - 2 * M, h: 0.45 });
}
{
  const s = deck.content(SEC1, "Üç yerleşim deneyeceğiz: düzgün, köşelere yakın ve alt şerit", { step: "ADIM 6 · SENSÖRLER",
    notes: "Sensörler FDM ağının iç düğümlerinden rastgele seçiliyor. Solda alana düzgün dağılmış 20 sensör. " +
      "Ortada Ders 02'nin sezgisi: hata alt köşelerde, o halde ölçümü oraya koy. Köşelerden 0.2 mesafe içinde 20 sensör. " +
      "Sağda pratikteki durum: soğutulan yüzeye yakın bir şerit, eta 0.1'in altında. Isı akısını en çok o bölge belirliyor. " +
      "Ayrıca sensör sayısını 5, 20 ve 80 yapıyoruz, mu'yu 1 ve 100, gürültüyü 0, 0.01 ve 0.05. Hepsi üç tohumla." });
  deck.image(s, "01_sensors.png", { x: M, y: BODY_TOP - 0.1, w: W - 2 * M, h: 4.35 });
  const cw = (W - 2 * M - 0.6) / 3;
  [["Sayı", "N_d = 5, 20, 80 · 3 tohum"], ["Ağırlık", "μ = 1 ve 100"], ["Gürültü", "σ = 0, 0.01, 0.05 · 0 / 0.5 / 2.5 °C"]]
    .forEach(([h, b], i) => deck.card(s, { x: M + i * (cw + 0.3), y: 5.95, w: cw, h: 0.78, head: `${h}: ${b}`, headSize: 13 }));
}
{
  const s = deck.content(SEC1, "μ = 1'de veri terimi toplam kaybın binde birinden az; μ = 100 onu Robin'in onda birine çıkarır", { step: "ADIM 6 · ÖLÇEK",
    notes: "Kayıp terimlerinin eğitim boyunca büyüklüğü. Mor çizgi mu çarpı veri terimi. " +
      "Ağ ölçümlere gürültü kadar yaklaşınca veri terimi sigma kareye, on üzeri eksi dörde oturuyor. Robin terimi ise Ders 02'deki köşe çelişkisi yüzünden 0.1 civarında kalıyor. " +
      "Yani mu bir iken optimizer veriyi neredeyse görmüyor. Bu yüzden mu 100'ü de denedik: veri terimi on üzeri eksi iki mertebesine çıkıyor, hâlâ Robin'in altında ama artık etkili. " +
      "Kural: ağırlığı tahminle değil, terimlerin eğitim sonundaki büyüklüğüne bakarak seçin." });
  deck.image(s, "02_loss_terms.png", { x: M, y: BODY_TOP - 0.1, w: 8.2, h: 3.9 }, "left");
  deck.mathBox(s, ["scale"], { x: M, y: 5.6, w: 8.2, h: 0.95, scale: 0.92 });
  const x0 = 9.2, sw = W - M - x0;
  deck.card(s, { x: x0, y: BODY_TOP, w: sw, h: 2.2, head: "μ = 1", body: "Veri terimi ≈ σ² ≈ 10⁻⁴; kayıp tabanı köşe çelişkisinden 0.1 civarında." });
  deck.card(s, { x: x0, y: BODY_TOP + 2.45, w: sw, h: 2.2, head: "μ = 100", body: "μ·veri ≈ 10⁻²: optimizer veriyi artık görüyor." });
}
deck.question(SEC1, "Veri terimini kayıp tabanıyla karşılaştırmadan μ = 1 seçseydik ne olurdu? Bu durumu deney yapmadan nasıl fark ederdiniz?", {
  hint: "İpucu: ağ ölçüme gürültü düzeyinde uyarsa veri terimi kaç olur?",
  notes: "Ağ ölçümlere sigma kadar uyarsa veri terimi sigma kare, yani on üzeri eksi dört. Bunu Robin teriminin tabanıyla, 0.08 ile karşılaştırmak yeter: binde bir. " +
    "Gradyanlar da kabaca aynı oranda; optimizer veriyi fiilen yok sayar. Deney yapmadan, yalnız terimlerin büyüklüğüne bakarak fark edilir. Wang ve arkadaşlarının gradyan dengeleme yöntemi bunu otomatik yapar." });

// =========================================================== 2 · DOĞRU FİZİK
const SEC2 = "2 · Doğru fizik";
deck.section(SEC2, "02", "Doğru fizik", "Fizik doğruyken veri ne katar?",
  { roadmapSteps: LOCAL, active: new Set([2]), notes: "İkinci bölüm: kayıptaki Bi gerçek değer, 4.895. Veri bir şey katıyor mu?" });
{
  const s = deck.content(SEC2, `Fizik doğruyken sensörler hatayı veri yok aralığının dışına taşımıyor; μ = 100 hatayı ${x(muRatio)} kat artırıyor`, { step: "ADIM 6 · SAYI VE YERLEŞİM",
    notes: `Gri bant, veri olmadan üç tohumun aralığı. Solda sensör sayısı: 5, 20, 80. Hiçbiri bandın dışına iyileşme getirmiyor; geometrik ortalamalar bandın içinde ve hatta biraz üstünde. ` +
      "Sağda 20 sensörle yerleşim: köşe ve alt şerit düzgünle aynı aralıkta. Ders 02'nin köşe sezgisi burada da işe yaramadı. " +
      `En sağda mu 100: üç tohumun ikisi bandın üstünde, ortalamada ${x(muRatio)} kat kötü. Veriye fazla ağırlık verince ağ gürültüye doğru eğiliyor. ` +
      "Bu, deneyden önce beklediğimiz sonuç değildi. Neden böyle olduğunu sonraki iki slayt açıklıyor." });
  deck.image(s, "03_count_config.png", { x: M, y: BODY_TOP - 0.1, w: W - 2 * M, h: 4.3 });
  const cw = (W - 2 * M - 0.6) / 3;
  [[`veri yok: ${deck.sci(B.min)} – ${deck.sci(B.max)}`, hex("titanyum")],
   ["N_d = 5, 20, 80 · köşe · alt şerit: aynı aralık", hex("plan")],
   [`μ = 100: ${x(muRatio)}× kötü`, hex("derin")]]
    .forEach(([h], i) => deck.card(s, { x: M + i * (cw + 0.3), y: 6.05, w: cw, h: 0.68, head: h, headSize: 13 }));
}
{
  const s = deck.content(SEC2, `Fizik gürültüyü süzer: ağ ölçüme σ kadar, gerçeğe ${Math.round(filt)} kat daha yakın oturur`, { step: "ADIM 6 · GÜRÜLTÜ",
    notes: "Ağın sensör noktalarındaki değerini iki şeyle karşılaştırıyoruz. Boş daire: gürültülü ölçüme göre fark. Dolu daire: gerçek, gürültüsüz değere göre fark. " +
      `Sigma 0.01'de ölçüme göre fark ${deck.sci(NZ["0.01"].data_rmse_vs_noisy)}, yani tam gürültü düzeyi. Gerçeğe göre fark ${deck.sci(NZ["0.01"].data_rmse_vs_clean)}: ${Math.round(filt)} kat küçük. ` +
      `Sigma 0.05'te, iki buçuk derece gürültüde bile gerçeğe göre fark ${deck.sci(NZ["0.05"].data_rmse_vs_clean)}. ` +
      "Ağ gürültüyü ezberlemiyor, çünkü Laplace denklemi düzgün bir çözüm dayatıyor; rastgele sıçramaları izleyemez. Fizik bir süzgeç gibi çalışıyor. " +
      `Ters taraf: gürültüsüz veri de hatayı değiştirmedi, bağıl L2 ${deck.sci(NZ["0.0"].rel_L2)}. Demek ki sorun gürültü değil; verinin taşıdığı bilgi.` });
  deck.image(s, "04_noise.png", { x: M, y: BODY_TOP - 0.1, w: 7.0, h: 4.6 }, "left");
  const x0 = 8.0, sw = W - M - x0;
  deck.stat(s, { x: x0, y: BODY_TOP, w: sw, value: deck.sci(NZ["0.01"].data_rmse_vs_clean), unit: "", label: "σ = 0.01'de ağ − gerçek (sensörlerde)" });
  deck.stat(s, { x: x0, y: BODY_TOP + 1.45, w: sw, value: deck.sci(NZ["0.01"].data_rmse_vs_noisy), unit: "", label: "ağ − ölçüm ≈ σ", color: hex("titanyum") });
  deck.mathBox(s, ["g_filter"], { x: x0, y: BODY_TOP + 2.95, w: sw, h: 0.9 });
  deck.caption(s, `Gürültüsüz veri (σ = 0) bile hatayı değiştirmedi: ${deck.sci(NZ["0.0"].rel_L2)}.`, { x: x0, y: BODY_TOP + 4.0, w: sw, h: 0.6 });
}
{
  const s = deck.content(SEC2, `Veri, ancak σ/√N_d model hatasının altına inerse bilgi taşır: burada ≈ ${nNeed} sensör gerekir`, { step: "ADIM 6 · BİLGİ ÖLÇÜTÜ", level: YL,
    notes: "Deneyi yapmadan bu sonucu tahmin edebilir miydik? Evet. N_d bağımsız ölçümün ortalamasındaki belirsizlik sigma bölü kök N_d. " +
      `Veri yokken PINN'in gerçek hatası, alan RMS'i olarak ${deck.sci(EPS)}. Sigma 0.01 ve 80 sensörde sigma bölü kök N_d ${deck.sci(0.01 / Math.sqrt(80))}: hâlâ modelden belirsiz. ` +
      `Ölçümlerin modele bir şey öğretebilmesi için yaklaşık ${nNeed} sensör ya da on kat daha az gürültü gerekir. ` +
      "Bu kaba bir ölçüt: sensörlerin uzayda nasıl dağıldığını ve hatanın nerede olduğunu hesaba katmıyor. Ama mertebe olarak doğru ve deney tasarımını yönlendirmek için yeterli. " +
      "Genel ders: hibrit PINN'in değeri fiziğin ne kadar iyi olduğuna bağlıdır. Fizik iyi ve sayısal hata küçükse seyrek veri bir şey katmaz." });
  deck.mathBox(s, ["criterion"], { x: M, y: BODY_TOP, w: W - 2 * M, h: 1.4 });
  const cw = (W - 2 * M - 0.6) / 3;
  deck.stat(s, { x: M, y: BODY_TOP + 1.75, w: cw, value: deck.sci(EPS), unit: "", label: "ε_model · veri yok, 3 tohum (alan RMS)" });
  deck.stat(s, { x: M + cw + 0.3, y: BODY_TOP + 1.75, w: cw, value: deck.sci(0.01 / Math.sqrt(80)), unit: "", label: "σ/√N_d · σ = 0.01, N_d = 80", color: hex("titanyum") });
  deck.stat(s, { x: M + 2 * (cw + 0.3), y: BODY_TOP + 1.75, w: cw, value: `≈ ${nNeed}`, unit: "sensör", label: "(σ / ε_model)² · gereken sayı", color: hex("lila") });
  deck.card(s, { x: M, y: BODY_TOP + 3.35, w: W - 2 * M, h: 1.3, head: "Çıkarım",
    body: "Doğru fizik ve küçük sayısal hata → seyrek, gürültülü veri yeni bilgi taşımaz. Verinin asıl yeri fiziğin eksik ya da yanlış olduğu durumdur." });
}
deck.question(SEC2, "μ = 100 neden hatayı artırdı? Ağın sensörlerdeki davranışıyla açıklayın.", {
  hint: "İpucu: μ = 100'de ağ − gerçek farkını sensörlerde μ = 1 ile karşılaştırın.",
  notes: "Mu bir iken ağ sensörlerde gerçeğe on üzeri eksi dört mertebesinde yakın; gürültüyü fizik süzüyor. Mu yüzde veri terimi fizik terimleriyle yarışacak kadar güçleniyor ve ağ gürültülü değerlere doğru eğiliyor. " +
    "Tohum ikide ağın sensörlerdeki gerçek hatası 1.5 çarpı on üzeri eksi üçe çıktı. Bu yerel bükülmeler Laplace'ı bozar ve hata alana yayılır. Klasik aşırı uyum, ama burada fizik düzenleyici olarak onu sınırlıyor." });

// =========================================================== 3 · YANLIŞ FİZİK
const SEC3 = "3 · Yanlış fizik";
deck.section(SEC3, "03", "Yanlış fizik", "Model Bi'yi yanlış bilirse veri ne yapar?",
  { roadmapSteps: LOCAL, active: new Set([3]), notes: "Üçüncü bölüm: fiziği bilerek bozuyoruz. Veri burada işe yarayacak mı?" });
{
  const s = deck.content(SEC3, `Fizik yanlışken veri hatayı en çok ${x(V.wrong_bi_best_data_reduction)} kat düşürür; sonuç doğru fiziğin ${Math.round(V.wrong_bi_best_over_correct)} katı kötü kalır`, { step: "ADIM 6 · YANLIŞ Bi",
    notes: "Pratikte ısı taşınım katsayısı bir korelasyondan gelir ve yüzde yirmi otuz belirsizdir. Burada uç bir durum kuruyoruz: model Bi'yi 2 sanıyor, gerçek 4.9. Ölçümler gerçekten geliyor. " +
      `Veri olmadan bağıl L2 ${deck.sci(W0.rel_L2)}; doğru fiziğin ${Math.round(V.wrong_bi_no_data_over_correct)} katı. Alt yüzey sıcaklığı 11 derece kadar yüksek, ısı akısı yüzde ${Math.round(100 * W0.Q_rel_err)} eksik. ` +
      `Mu birde veri etkisiz: ${deck.sci(W1.rel_L2)}, çünkü yine veri terimi küçük kalıyor. Mu yüzle 20 sensör ${deck.sci(W2.rel_L2)}, 80 sensör ${deck.sci(W3.rel_L2)}. ` +
      `En iyi durumda bile hata yalnız ${x(V.wrong_bi_best_data_reduction)} kat düştü ve Q hatası yüzde ${Math.round(100 * W3.Q_rel_err)}. Profil gerçeğe doğru çekiliyor ama oraya varamıyor.` });
  deck.mathBox(s, ["wrong"], { x: M, y: BODY_TOP - 0.05, w: W - 2 * M, h: 1.0, scale: 0.95 });
  deck.image(s, "05_wrong_bi.png", { x: M, y: BODY_TOP + 1.05, w: W - 2 * M, h: 3.65 });
}
{
  const s = deck.content(SEC3, "Yanlış Robin terimi ile ölçümler aynı ağı zıt yönlere çeker; çözüm Bi'yi öğrenilecek bir parametre yapmak", { step: "ADIM 6 · NEDEN SINIRLI?",
    notes: "Neden veri hatayı yalnız iki kat düşürebildi? Kayıpta iki terim birbiriyle çekişiyor. Robin terimi Bi 2 olan bir çözüm istiyor; ölçümler Bi 4.9 olan çözümü gösteriyor. " +
      "Hiçbir fonksiyon ikisini birden sağlayamaz. Mu, ikisi arasındaki uzlaşmanın yerini belirliyor: mu büyüdükçe ölçümlere yaklaşıyoruz ama yanlış fizik alt kenarda hâlâ baskın. " +
      "Daha çok veri ya da daha büyük mu tek başına çözüm değil: mu çok büyürse doğru fizik durumunda gördüğümüz gibi gürültüye uyum başlıyor. " +
      "Doğal çözüm: Bi'yi sabit değil, öğrenilecek bir parametre yapmak. O zaman çelişki ortadan kalkar ve ölçümler Bi'yi belirler. Bu, gelecek dersin konusu, ters problem." });
  const cw = (W - 2 * M - 0.6) / 3;
  [["Çekişme", "Robin terimi Bi = 2 çözümünü, ölçümler Bi = 4.9 çözümünü ister; ikisi birden sağlanamaz."],
   ["μ bir uzlaşmadır", "μ büyüdükçe ölçüme yaklaşılır; ama çok büyük μ gürültüye uyumu başlatır (bölüm 2)."],
   ["Çözüm: Bi'yi öğren", "Bi'yi ağırlıklarla birlikte optimize et; ölçümler parametreyi belirler. Ders 04."]]
    .forEach(([h, b], i) => deck.card(s, { x: M + i * (cw + 0.3), y: BODY_TOP, w: cw, h: 2.5, head: h, body: b, num: i + 1, headSize: 18, bodySize: 15 }));
  deck.mathBox(s, ["pv_inverse"], { x: M, y: BODY_TOP + 2.85, w: W - 2 * M, h: 1.2, label: "DERS 04 · TERS PROBLEM" });
}
deck.question(SEC3, "Gerçek bir deneyde fiziğinizin doğru olup olmadığını, referans çözüm olmadan nasıl anlarsınız?", {
  hint: "İpucu: eğitimden sonra ölçüme göre RMSE'yi bilinen gürültü düzeyiyle karşılaştırın.",
  notes: "Fizik doğruysa ağ ölçümlere gürültü düzeyinde uyar: ölçüme göre RMSE yaklaşık sigma. Fizik yanlışsa ağ ölçümlere uyamaz ve bu fark sigmanın çok üstünde kalır. " +
    `Bizim yanlış Bi koşularında ağın sensörlerdeki gerçek hatası ${deck.sci(W2.data_rmse_vs_clean)} ile ${deck.sci(W3.data_rmse_vs_clean)}, yani sigmanın üç ila dört katı. Bu, artık analizi denen bir model doğrulama testidir ve referans çözüm gerektirmez.` });

// =========================================================== KAPANIŞ
const SEC4 = "Kapanış";
pres.addSection({ title: SEC4 });
{
  const s = deck.content(SEC4, "Bu dersin üç çıkarımı", { dark: true,
    notes: "Özetleyelim. Bir: veri terimi tek satır, ama ağırlığı kayıp terimlerinin ölçeğine bakarak seçilmeli. " +
      "İki: fizik doğru ve model hatası gürültüden küçükse seyrek veri bilgi taşımaz; fizik gürültüyü süzer, büyük mu ise zarar verir. " +
      "Üç: fizik yanlışsa veri hatayı düşürür ama çekişme sınır koyar; asıl çözüm bilinmeyeni öğrenmektir." });
  const cw = (W - 2 * M - 0.6) / 3;
  [["μ ölçekle seçilir", "μ = 1'de veri terimi kaybın binde biri; terimlerin büyüklüğüne bakmadan ağırlık seçmeyin."],
   ["Doğru fizikte veri sessiz", `Sayı, yerleşim, gürültüsüz veri: hata tohum aralığında. Ağ gerçeğe ${Math.round(filt)} kat daha yakın; μ = 100 ${x(muRatio)}× kötü.`],
   ["Yanlış fizikte veri sınırlı", `Hata en çok ${x(V.wrong_bi_best_data_reduction)} kat düştü, Q hatası ${pct(W0.Q_rel_err)} → ${pct(W3.Q_rel_err)}. Bilinmeyeni öğrenmek gerekir.`]]
    .forEach(([h, b], i) => deck.card(s, { x: M + i * (cw + 0.3), y: BODY_TOP + 0.2, w: cw, h: 2.7, head: h, body: b, num: i + 1, dark: true, headSize: 19, bodySize: 16 }));
  s.addText("Sıradaki adım: Bi'yi ölçümlerden geri bulmak (ters problem).", { x: M, y: 5.4, w: W - 2 * M, h: 0.5,
    fontSize: 16, color: hex("gumus"), margin: 0, isTextBox: true, objectName: "sum_next" });
}
{
  const s = deck.content(SEC4, "Uygulama: kodu çalıştırın, sonra deneyleri düzeyinize göre yapın", { step: "UYGULAMA",
    notes: "Her koşu iki çekirdekte yaklaşık sekiz dakika. Lisans öğrencileri sol sütunu, yüksek lisans öğrencileri ayrıca sağ sütunu yapsın. Teslim: bir sayfalık not, bir figür ve bir tablo; her sonuç üç tohumla." });
  s.addShape(pres.shapes.RECTANGLE, { x: M, y: BODY_TOP, w: 4.5, h: 4.35, fill: { color: hex("derin") }, line: { type: "none" }, objectName: "code_bg2" });
  s.addText([
    { text: "python pinn_hybrid.py \\", options: { breakLine: true } },
    { text: "  --n-data 20 --noise 0.01 \\", options: { breakLine: true } },
    { text: "  --mu 100 --tag deneme", options: { breakLine: true } },
    { text: "python pinn_hybrid.py \\", options: { breakLine: true } },
    { text: "  --bi-model 2 --mu 100 \\", options: { breakLine: true } },
    { text: "  --tag yanlis", options: { breakLine: true } },
    { text: "python hybrid_summary.py", options: {} },
  ], { x: M + 0.25, y: BODY_TOP + 0.25, w: 4.05, h: 3.85, fontFace: "Courier New", fontSize: 13, color: hex("krom"),
    valign: "top", margin: 0, paraSpaceAfter: 8, isTextBox: true, objectName: "code2" });
  const cx = M + 4.8, cw = (W - M - cx - 0.3) / 2;
  deck.card(s, { x: cx, y: BODY_TOP, w: cw, h: 4.35, head: "Lisans",
    body: "1. σ = 0.001 ile 20 sensör: bilgi ölçütüne göre veri işe yarar mı? Deneyin.\n2. μ = 0.1, 1, 10, 100 taraması (doğru fizik), 3 tohum.\n3. Yanlış fizikte sensörleri yalnız alt şeride koyun.", headSize: 18, bodySize: 14 });
  deck.card(s, { x: cx + cw + 0.3, y: BODY_TOP, w: cw, h: 4.35, head: "Yüksek lisans",
    body: "1. μ'yü gradyan büyüklüklerine göre otomatik ayarlayın (Wang vd. 2021).\n2. Bi_model = 3, 4, 6 için hata ve Q eğrisini çizin.\n3. Ölçüme göre RMSE ile yanlış fiziği referanssız tespit edin.", headSize: 18, bodySize: 14 });
}
{
  const s = deck.content(SEC4, "Sıradaki ders: Bi'yi ölçümlerden geri bulacağız", { step: "DERS 04 · ÖNİZLEME",
    notes: "Gelecek ders yedinci adım, ters problem. Bi'yi bir torch parametresi yapıp ağırlıklarla birlikte optimize edeceğiz. " +
      "Sorular: kaç sensör ve ne kadar gürültüyle Bi'yi yüzde birin altında bulabiliriz? Başlangıç tahmini ne kadar yanlış olabilir? Bugünkü yanlış fizik deneyinin doğal devamı." });
  deck.mathBox(s, ["pv_inverse"], { x: M, y: BODY_TOP, w: W - 2 * M, h: 1.5 });
  const cw = (W - 2 * M - 0.6) / 3;
  [["Bilinmeyen", "Bi: ağırlıklarla birlikte öğrenilen tek bir sayı"], ["Soru", "Kaç sensör, ne kadar gürültüyle Bi %1'in altında?"], ["Bağlantı", "Bugünkü çekişme ortadan kalkar"]]
    .forEach(([h, b], i) => deck.card(s, { x: M + i * (cw + 0.3), y: 3.9, w: cw, h: 1.6, head: h, body: b, headSize: 18, bodySize: 14 }));
}
{
  const s = deck.content(SEC4, "Kaynaklar", {
    notes: "Raissi ve arkadaşları hibrit ve ters PINN'i aynı makalede tanıtıyor. Karniadakis ve arkadaşlarının derlemesi fizik bilgili öğrenmenin veri ile fizik arasındaki yerini tartışıyor. Wang, Teng ve Perdikaris kayıp ağırlıklarını gradyanlarla dengeliyor." });
  deck.card(s, { x: M, y: BODY_TOP, w: W - 2 * M, h: 2.7, head: "Okuma listesi",
    body: "M. Raissi, P. Perdikaris, G. E. Karniadakis · Physics-informed neural networks, J. Comput. Phys. 378 (2019) 686–707\n" +
      "G. E. Karniadakis, I. G. Kevrekidis, L. Lu, P. Perdikaris, S. Wang, L. Yang · Physics-informed machine learning, Nat. Rev. Phys. 3 (2021) 422–440\n" +
      "S. Wang, Y. Teng, P. Perdikaris · Understanding and mitigating gradient flow pathologies in PINNs, SIAM J. Sci. Comput. 43 (2021)\n" +
      "Kod: github.com/mikbalarikan/kolay-pinn · cases/01-2d-heat-conduction/pinn_hybrid.py", headSize: 18, bodySize: 14 });
}

const out = path.join(__dirname, "ders03_hibrit_pinn.pptx");
deck.write(out).then((f) => console.log(f));
