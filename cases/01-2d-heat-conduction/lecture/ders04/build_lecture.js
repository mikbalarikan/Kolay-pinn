/**
 * Ders 04 · Ters problem: Bi'yi iç sıcaklık ölçümlerinden geri bulmak (Adım 7)
 * Önce:  python inverse_classical.py ; python inverse_runs.py ; python inverse_summary.py
 *        python lecture/ders04/equations.py ; python lecture/ders04/make_slide_figures.py
 * Sonra: node lecture/ders04/build_lecture.js  ->  lecture/ders04/ders04_ters_problem.pptx
 */
const fs = require("fs");
const path = require("path");
const D = require(path.join(__dirname, "..", "..", "..", "..", "kolay_pinn", "deck", "turkisi_deck.js"));

const CASE = path.join(__dirname, "..", "..");
const ASSETS = path.join(__dirname, "assets");
const S = JSON.parse(fs.readFileSync(path.join(CASE, "data", "summary_inverse.json"), "utf8"));
const CL = JSON.parse(fs.readFileSync(path.join(CASE, "data", "inverse_classical.json"), "utf8"));
const deck = D.createDeck({ course: "KOLAY PINN", lecture: "Ders 04 · Ters problem", assets: ASSETS,
  eqDir: path.join(ASSETS, "eq"), title: "Kolay PINN · Ders 04 · Ters problem: Bi'yi ölçümlerden geri bulmak" });
const { pres, C, W, M, BODY_TOP, hex } = deck;
const YL = "YÜKSEK LİSANS";
const BI = S.Bi_true, V = S.verdict, MS = S.mu_scan, MK = S.mu_scan_skip, G = S.groups, X = S.extra;
const f2 = (v) => v.toFixed(2), f3 = (v) => v.toFixed(3);
const pc = (v) => `%${(100 * Math.abs(v)).toFixed(1)}`;
const sp = (s) => s.replace(".", " nokta ");                   // seslendirme: ondalık
const crlbPct = (k) => [0, 1, 2].reduce((a, s) => a + CL.configs[k].seeds[`s${s}`].crlb_sigma_Bi, 0) / 3 / BI;
const REC = G["20 düzgün"], R0 = REC.runs[0];

const STEPS = [
  { n: 1, t: "Problemi tanımla" }, { n: 2, t: "Boyutsuzlaştır" }, { n: 3, t: "FDM referansı" },
  { n: 4, t: "Forward PINN" }, { n: 5, t: "Doğrula" }, { n: 6, t: "Hibrit PINN" },
  { n: 7, t: "Ters problem" }, { n: 8, t: "Parametrik PINN" }, { n: 9, t: "Framework" },
];
const LOCAL = ["Bi'yi öğren", "Ne kadar iyi olabilir?", "Köşe yanlılığı"].map((t, i) => ({ n: i + 1, t }));

// =========================================================== GİRİŞ
pres.addSection({ title: "Giriş" });
{
  const s = pres.addSlide({ masterName: "KAPAK", sectionTitle: "Giriş" });
  deck.chip(s, "KOLAY PINN · DERS 04", M, 1.7);
  s.addText("Ters problem:\nBi'yi ölçümlerden bul", { x: M, y: 2.2, w: 8.6, h: 2.0, fontSize: 44, bold: true,
    color: C.background2, margin: 0, valign: "top", isTextBox: true, objectName: "cover_title" });
  s.addText("Öğrenilen parametre · Bi → 0 tuzağı · klasik referans ve Cramér–Rao sınırı · köşe yanlılığı",
    { x: M, y: 4.35, w: 8.6, h: 0.9, fontSize: 18, color: hex("gumus"), margin: 0, valign: "top", isTextBox: true, objectName: "cover_sub" });
  s.addText("Lisans ve yüksek lisans · Adım 7 · yaklaşık 45 dakika", { x: M, y: 6.2, w: 8, h: 0.4, fontSize: 13,
    color: hex("titanyum"), margin: 0, isTextBox: true, objectName: "cover_meta" });
  s.addImage({ path: deck.A("maskot_mutlu.png"), x: 9.4, y: 1.6, w: 3.4, h: 3.4, objectName: "cover_mascot" });
  s.addNotes("Geçen derste modele bilerek yanlış bir Biot sayısı verdik ve ölçümlerin bu hatayı ancak sınırlı ölçüde düzelttiğini gördük. " +
    "Bugün doğal adımı atıyoruz: Bi'yi sabit değil, ağın ağırlıklarıyla birlikte öğrenilen bir sayı yapıyoruz. Buna ters problem denir. " +
    "Göreceğiz ki bu tek satırlık değişiklik kendi başına çalışmıyor. Neden çalışmadığını anlamak, PINN'lerin kayıp fonksiyonu hakkında bu kursun en öğretici sonuçlarından birini veriyor.");
}
{
  const s = deck.content("Giriş", "Bu dersin sonunda dört şeyi yapabileceksiniz", {
    notes: "Birinci hedef teknik: bir fiziksel parametreyi torch parametresi olarak kayba koymak. " +
      "İkincisi bir hata ayıklama becerisi: parametre yanlış yere gittiğinde bunun optimizasyondan mı yoksa kaybın kendisinden mi kaynaklandığını ayırmak. " +
      "Üçüncüsü klasik bir araç: Cramér–Rao sınırı ile, hangi sensör düzeninin ne kadar doğru sonuç verebileceğini eğitimden önce hesaplamak. " +
      "Dördüncüsü yüksek lisans: köşe çelişkisinin Bi tahminine getirdiği yanlılığı basit bir formülle öngörmek." });
  const objs = [
    ["Parametreyi öğrenmek", "Bi = e^β'yı ağ ağırlıklarıyla birlikte optimize etmek."],
    ["Tuzağı tanımak", "Bi → 0 çöküşünün kayıptan mı optimizasyondan mı geldiğini ayırmak."],
    ["Sınırı hesaplamak", "Duyarlılık ve Cramér–Rao ile ulaşılabilir doğruluğu eğitimden önce bulmak."],
    ["Yanlılığı öngörmek", "Köşe tabanının Bi'yi ne kadar çektiğini formülle tahmin etmek."],
  ];
  const cw = (W - 2 * M - 0.3) / 2, ch = 2.05;
  objs.forEach(([h, b], i) => deck.card(s, { x: M + (i % 2) * (cw + 0.3), y: BODY_TOP + Math.floor(i / 2) * (ch + 0.3),
    w: cw, h: ch, head: h, body: b, num: i + 1, headSize: 18, bodySize: 15 }));
}
{
  const s = deck.content("Giriş", "Ders 03'te fizik yanlışken veri hatayı en çok iki kat düşürdü; bugün Bi'yi veriden öğreniyoruz", {
    notes: "Yol haritasında yedinci adımdayız. Ders 03'ten bir sonuç getiriyoruz: model Bi'yi 2 sanırken veri, alan hatasını en çok iki kat düşürebildi; " +
      "bağıl L2 yüzde dört civarında kaldı. Bugünkü hedef, aynı ölçümlerle Bi'yi kendisi bulan bir model. " +
      "Pratikte bu, bir deneyde ısı taşınım katsayısını termokupl okumalarından geri hesaplamak demek." });
  deck.roadmap(s, STEPS, new Set([7]), { y: 2.6 });
  deck.card(s, { x: M, y: 4.6, w: 5.9, h: 1.6, head: "Ders 03'ten gelen",
    body: "Bi_model = 2, 80 sensör, μ = 100: bağıl L₂ 4.6×10⁻², Q′ hatası %26. Çekişme sınır koyuyor." });
  deck.card(s, { x: M + 6.2, y: 4.6, w: W - 2 * M - 6.2, h: 1.6, head: "Bugünkü soru",
    body: "Aynı 20 sensörle Bi'yi ne kadar doğru bulabiliriz? Sınırı ne belirler?" });
}
{
  const s = deck.content("Giriş", "Bu derste altı kavrama yaslanacağız", {
    notes: "Sözlük. Bi eşittir e üzeri beta: Bi'yi pozitif tutmak için logaritmasını öğreniyoruz. " +
      "Duyarlılık S: Bi biraz değişince bir noktadaki sıcaklık ne kadar değişir. Cramér–Rao sınırı: gürültülü veriyle hiçbir yansız yöntemin geçemeyeceği belirsizlik. " +
      "Köşe tabanı: Ders 02'deki köşe çelişkisinin Robin kaybına eklediği, Bi'nin karesiyle büyüyen sabit pay. " +
      "Delta: köşeden bu mesafedeki Robin noktalarını kayıptan çıkarmak. Bi yıldız: aynı veriye klasik en küçük karelerle uydurulan değer." });
  const terms = [
    ["Öğrenilen parametre", "g_beta", "β öğrenilir; Bi > 0 kendiliğinden", 1],
    ["Duyarlılık", "g_sens", "Bi değişince θ ne kadar değişir", 0.9],
    ["Cramér–Rao sınırı", "g_crlb", "Gürültünün koyduğu alt sınır", 0.9],
    ["Köşe tabanı", "g_floor", "Ders 02'nin çelişkisi, Bi ile büyür", 1],
    ["Köşe dışlama", "g_skip", "Köşe şeridindeki Robin noktaları yok", 1],
    ["Klasik tahmin", "g_ls", "Seri çözüm + en küçük kareler", 0.75],
  ];
  const cw = (W - 2 * M - 0.6) / 3, ch = 2.15;
  terms.forEach(([h, m, b, sc], i) => deck.card(s, { x: M + (i % 3) * (cw + 0.3), y: BODY_TOP + Math.floor(i / 3) * (ch + 0.25),
    w: cw, h: ch, head: h, math: m, mathScale: sc, body: b, headSize: 17, bodySize: 14 }));
}

// =========================================================== 1 · Bi'Yİ ÖĞREN
const SEC1 = "1 · Bi'yi öğren";
deck.section(SEC1, "01", "Bi'yi öğren", "Tek satırlık değişiklik ve beklenmedik sonucu",
  { roadmapSteps: LOCAL, active: new Set([1]), notes: "Birinci bölüm: Bi'yi parametre yapıyoruz ve ne olduğuna bakıyoruz." });
{
  const s = deck.content(SEC1, "Ters PINN, Ders 03'ün kaybını ağırlıklar ve Bi üzerinden birlikte küçültür", { step: "ADIM 7 · KAYIP",
    notes: "Kayıp Ders 03 ile aynı: Laplace artığı, Robin artığı ve veri terimi. Tek fark Robin terimindeki Bi'nin artık bir sabit değil, beta adında bir torch parametresinin üsteli olması. " +
      "Üstel yazmamızın nedeni Bi'nin pozitif kalması ve onlarca kat değişebilmesi; logaritmada öğrenmek bunu kolaylaştırıyor. Başlangıç Bi sıfır eşittir 2, Ders 03'ün yanlış değeri. " +
      "Bi'yi öğrenince ısı taşınım katsayısı h ve alt yüzeyden çıkan ısı da hesaplanabilir; gerçek h artık bilinmiyor. " +
      "Kodda iki satır: beta'yı parametre olarak tanımla ve optimizere ekle. Bi için öğrenme oranını ağırlıklarınkinden on kat büyük seçtik." });
  deck.mathBox(s, ["inverse"], { x: M, y: BODY_TOP, w: W - 2 * M, h: 1.35 });
  deck.mathBox(s, ["robin_bi", "h_from_bi"], { x: M, y: BODY_TOP + 1.6, w: 7.6, h: 2.3, gap: 0.3, scale: 0.85 });
  deck.card(s, { x: M + 7.9, y: BODY_TOP + 1.6, w: W - 2 * M - 7.9, h: 2.3, head: "Kodda iki satır",
    body: "beta = nn.Parameter(log(2.0))\nAdam([{w, lr 1e-3}, {beta, lr 1e-2}])" });
  deck.caption(s, "Ağ, kolokasyon, sensörler (20, σ = 0.01 ≙ 0.5 °C) ve eğitim Ders 03 ile aynı.",
    { x: M, y: BODY_TOP + 4.15, w: W - 2 * M, h: 0.45 });
}
{
  const s = deck.content(SEC1, `Saf kayıpla Bi, 2'den ${f2(MS["1"].Bi_est)}'e çöker; köşe dışlansa da μ = 1 yetmez`, { step: "ADIM 7 · TUZAK",
    notes: `Soldaki grafik öğrenilen Bi'nin eğitim boyunca yolu. Gri çizgi en doğal ayar: köşe dışlama yok, mu bir. Bi ikiden başlıyor ve ${sp(f2(MS["1"].Bi_est))}'e iniyor. ` +
      `Mor çizgide köşeyi dışladık ama mu hâlâ bir: sonuç ${sp(f2(MK["1"].Bi_est))}. Turuncuda mu yüz, köşe dışlama yok: Bi yükseliyor ama ${sp(f2(MS["100"].Bi_est))}'de duruyor. ` +
      `Yalnız mavi çizgi, köşe dışlama ile mu yüz birlikte, gerçek değere ulaşıyor: ${sp(f3(R0.Bi_est))}. ` +
      "Sağda gri koşunun kayıp terimleri. Başlangıçta ağın çıktısı birdir, Robin artığı eksi Bi olur, Robin kaybı Bi kare. " +
      "Bi'yi küçültmek Robin kaybını düşürmenin en ucuz yolu; bedeli yalnız veri terimi, o da yüzde iki civarında. Bi sıfıra giderse teta her yerde bir olur ve fiziği tam sağlar." });
  deck.image(s, "01_trap.png", { x: M, y: BODY_TOP - 0.1, w: W - 2 * M, h: 4.4 });
  const cw = (W - 2 * M - 0.6) / 3;
  [[`δ = 0, μ = 1 → Bi = ${f2(MS["1"].Bi_est)}`], [`δ = 0, μ = 100 → Bi = ${f2(MS["100"].Bi_est)}`], [`δ = 0.02, μ = 100 → Bi = ${f3(R0.Bi_est)}`]]
    .forEach(([h], i) => deck.card(s, { x: M + i * (cw + 0.3), y: 6.05, w: cw, h: 0.68, head: h, headSize: 13 }));
}
deck.question(SEC1, "Bi → 0 çöküşü bir optimizasyon sorunu mu, yoksa kaybın kendisi mi yanlış? Nasıl ayırt edersiniz?", {
  hint: "İpucu: doğru Bi'deki ve Bi → 0'daki toplam kaybı karşılaştırın.",
  notes: `Bi sıfıra giderken teta bire gider, fizik terimleri sıfırlanır ve geriye yalnız veri terimi kalır: yaklaşık 0.02. ` +
    `Doğru Bi'de ise köşe çelişkisi Robin kaybına Bi kare çarpı c kadar, yaklaşık ${sp((S.c_corner * BI * BI).toFixed(2))} ekler; mu birde veri terimi buna göre önemsiz. ` +
    "Yani mu birde yanlış çözüm kaybın gerçek minimumudur: optimizer görevini yapıyor, kayıp yanlış. Ayırt etmek için iki noktada kaybı hesaplamak yeter. " +
    "Köşeyi dışlayınca taban kalkıyor ve doğru Bi minimum oluyor; ama mu birde optimizer yine de Bi'yi önce küçültüp geri dönemiyor. Bu ikinci durum gerçekten bir optimizasyon sorunu." });

// =========================================================== 2 · NE KADAR İYİ OLABİLİR?
const SEC2 = "2 · Ne kadar iyi olabilir?";
deck.section(SEC2, "02", "Ne kadar iyi olabilir?", "Klasik referans, duyarlılık ve Cramér–Rao sınırı",
  { roadmapSteps: LOCAL, active: new Set([2]), notes: "İkinci bölüm: PINN'i neye karşı ölçeceğiz? Aynı veriyle ulaşılabilecek en iyi sonuca." });
{
  const s = deck.content(SEC2, "Bi'nin izi soğutulan yüzeyde: alt şeritteki 20 sensör, düzgün 80 sensör kadar bilgi taşır", { step: "ADIM 7 · BELİRLENEBİLİRLİK", level: YL,
    notes: "PINN'i değerlendirmek için önce aynı veriyle ulaşılabilecek en iyi sonucu bilmemiz gerekir. Klasik yol: analitik seri çözümü al, Bi'yi tek değişkenli en küçük karelerle uydur. Bir saniyeden kısa sürer. " +
      "Belirsizliği duyarlılık belirler: S, Bi biraz değişince bir noktadaki sıcaklığın ne kadar değiştiği. Fisher bilgisi S karelerin toplamı bölü sigma kare; tersinin karekökü Cramér–Rao alt sınırı. " +
      `Soldaki harita eksi S. Bilgi alt yüzeyde toplanmış, üst yarıda hızla sönüyor. Sağda sınır: üst yarıdaki yirmi sensörle yüzde ${sp((100 * crlbPct("n20_top")).toFixed(1))}, ` +
      `düzgünle yüzde ${sp((100 * crlbPct("n20_uniform")).toFixed(1))}, alt şeritle yüzde ${sp((100 * crlbPct("n20_bottom")).toFixed(1))}. ` +
      `Alt şeritteki yirmi sensör, düzgün dağılmış seksen sensörle aynı bilgiyi taşıyor. Monte Carlo yayılımı da bu sınırla örtüşüyor. ` +
      "Deney tasarımını PINN eğitmeden, ucuz klasik modelle yapabiliriz." });
  deck.mathBox(s, ["crlb"], { x: M, y: BODY_TOP - 0.05, w: W - 2 * M, h: 1.05, scale: 0.9 });
  deck.image(s, "03_sensitivity.png", { x: M, y: BODY_TOP + 1.1, w: W - 2 * M, h: 3.65 });
}
deck.question(SEC2, "Bütçeniz 20 termokupl. Bi'yi en doğru bulmak için nereye koyarsınız? Ya ısı akısı Q′'yu?", {
  hint: "İpucu: duyarlılık haritası S(x) nerede büyük?",
  notes: "Bi için cevap duyarlılık haritasında: soğutulan yüzeye en yakın şerit. Orada Cramér–Rao sınırı düzgün yerleşimin yaklaşık yarısı. " +
    "Bir uyarı: sensörlerin hepsini aynı küçük bölgeye koymak, modeliniz yanlışsa onu fark etme şansınızı azaltır; birkaç sensörü uzağa koymak bir model kontrolüdür. " +
    "Isı akısı için de alt şerit iyi bir seçim, çünkü Q′ alt yüzey sıcaklığının integrali ve Bi'nin çarpımı." });

// =========================================================== 3 · KÖŞE YANLILIĞI
const SEC3 = "3 · Köşe yanlılığı";
deck.section(SEC3, "03", "Köşe yanlılığı", "Kayıp tabanı Bi'yi ne kadar çeker?",
  { roadmapSteps: LOCAL, active: new Set([3]), notes: "Üçüncü bölüm: köşe çelişkisinin Bi tahminine etkisini öngörüyoruz ve gideriyoruz." });
{
  const s = deck.content(SEC3, `Köşe yanlılığı önceden hesaplanabilir: μ = 100'de öngörü ${f2(MS["100"].Bi_pred)}, PINN ${f2(MS["100"].Bi_est)}`, { step: "ADIM 7 · YANLILIK", level: YL,
    notes: "Basit bir model kuralım. Köşe çelişkisi Robin kaybına Bi'nin karesiyle büyüyen bir taban ekler; c sabitini Ders 02'nin veri yok koşularından okuyoruz, ters koşulara bakmadan. " +
      "Veri terimi ise en iyi tahmin Bi yıldız çevresinde parabol: mu çarpı m çarpı fark kare, m sensörlerdeki ortalama S kare. İki parabolün toplamının minimumu bu formül. " +
      `Öngörü mu yüzde ${sp(f2(MS["100"].Bi_pred))}, PINN ${sp(f2(MS["100"].Bi_est))}. Mu binde öngörü ${sp(f2(MS["1000"].Bi_pred))}, PINN ${sp(f2(MS["1000"].Bi_est))}. ` +
      "Mu bir ve onda formül çöküşü niteliksel olarak doğru veriyor. Yanlılık mu ile azalıyor ama hiç sıfırlanmıyor; mu'yu sonsuz büyütemeyiz, çünkü Ders 03'te gördük, ağ gürültüye bükülür. " +
      "Mavi noktalar köşe dışlama ile: taban yüz kat küçülüyor ve mu yüzde Bi gri bandın, yani klasik tahminin belirsizliğinin içine düşüyor." });
  deck.image(s, "02_corner_bias.png", { x: M, y: BODY_TOP - 0.1, w: 7.4, h: 4.15 }, "left");
  const x0 = 8.2, sw = W - M - x0;
  deck.mathBox(s, ["bias"], { x: x0, y: BODY_TOP, w: sw, h: 1.3, scale: 0.62 });
  deck.stat(s, { x: x0, y: BODY_TOP + 1.55, w: sw, value: deck.sci(S.c_corner), unit: "",
    label: "c · Ders 02, δ = 0 (son Robin kaybı / Bi²)" });
  deck.stat(s, { x: x0, y: BODY_TOP + 3.0, w: sw, value: `${Math.round(S.c_corner / S.c_skip)}×`, unit: "",
    label: "δ = 0.02 ile köşe tabanındaki düşüş", color: hex("plan") });
}
{
  const s = deck.content(SEC3, `δ = 0.02 ve μ = 100 ile PINN, klasik tahminin gürültü sınırında: fark Cramér–Rao sınırının ${f2(REC.gap_over_crlb)} katı`, { step: "ADIM 7 · ÖNERİLEN AYAR",
    notes: "Önerilen ayar: köşe şeridini Robin kaybından çıkar, veri ağırlığını yüz yap. Her sensör kümesi için üç tohum: mavi nokta PINN, beyaz daire aynı verinin klasik tahmini, çubuk Cramér–Rao sınırı. " +
      `Yirmi düzgün sensörde ortalama mutlak Bi hatası yüzde ${sp((100 * REC.mean_abs_rel_err).toFixed(1))}. Ama asıl ölçüt gerçek değer değil, aynı veriyle ulaşılabilecek değer: ` +
      `PINN ile klasik tahmin arasındaki fark sınırın ${sp(f2(REC.gap_over_crlb))} katı. Yani kalan hata gürültüden geliyor, yöntemden değil. ` +
      `Üst yarıda belirsizlik büyük ve PINN de klasik de dağılıyor; alt şeritte ikisi de sıkı. ` +
      `Gürültüsüz veride PINN ${sp(f3(X["σ = 0"].Bi_est))} buluyor. Başlangıcı 0.5 ya da 8 yapınca ${sp(f3(X["Bi₀ = 0.5"].Bi_est))} ve ${sp(f3(X["Bi₀ = 8"].Bi_est))}: başlangıca duyarlı değil.` });
  deck.image(s, "04_pinn_vs_classical.png", { x: M, y: BODY_TOP - 0.1, w: W - 2 * M, h: 4.25 });
  const cw = (W - 2 * M - 0.6) / 3;
  [`20 düzgün: |Bi hatası| ${pc(REC.mean_abs_rel_err)}`, `σ = 0: Bi = ${f3(X["σ = 0"].Bi_est)}`,
   `Bi₀ = 0.5 / 8 → ${f3(X["Bi₀ = 0.5"].Bi_est)} / ${f3(X["Bi₀ = 8"].Bi_est)}`]
    .forEach((h, i) => deck.card(s, { x: M + i * (cw + 0.3), y: 6.0, w: cw, h: 0.72, head: h, headSize: 13 }));
}
{
  const s = deck.content(SEC3, `Ders 03'ün yanlış fiziği düzeldi: alan hatası ${deck.sci(V.recommended_rel_L2_gmean)}, iki mertebe daha küçük`, { step: "ADIM 7 · SONUÇ",
    notes: "Ders 03'ün sorusuna dönelim. Kesikli mor çizgi, Bi ikiye sabitlenmiş ve yirmi sensörle eğitilmiş modelin alt yüzey sıcaklığı: gerçeğin birkaç derece üstünde. " +
      `Mavi çizgi bugünkü model, aynı yirmi sensörle Bi'yi kendisi buluyor: ${sp(f3(R0.Bi_est))}. Gerçek profilin üstüne oturuyor. ` +
      `Alan hatası Ders 03'teki yüzde dokuzdan ${deck.sci(V.recommended_rel_L2_gmean)} mertebesine indi. Ders 03'te dediğimiz gibi: verinin asıl değeri bilinmeyeni belirlemek.` });
  deck.image(s, "05_bottom_fixed.png", { x: M, y: BODY_TOP - 0.1, w: 7.6, h: 4.3 }, "left");
  const x0 = 8.4, sw = W - M - x0;
  deck.stat(s, { x: x0, y: BODY_TOP, w: sw, value: f3(R0.Bi_est), unit: "", label: "öğrenilen Bi · 20 sensör, tohum 0 (gerçek 4.895)" });
  deck.stat(s, { x: x0, y: BODY_TOP + 1.45, w: sw, value: deck.sci(V.recommended_rel_L2_gmean), unit: "", label: "bağıl L₂ · 3 tohum (Ders 03, Bi = 2: 9.2×10⁻²)", color: hex("lila") });
  deck.caption(s, "Öğrenilen h ile ısı akısı: Q′ hatası " + pc(R0.Q_rel_err_est) + " (tohum 0).", { x: x0, y: BODY_TOP + 3.0, w: sw, h: 0.8 });
}
deck.question(SEC3, "Köşe tabanının olmadığı bir problemde (ör. düzgün sınır koşulları) μ'yü nasıl seçerdiniz?", {
  hint: "İpucu: ağ ölçüme gürültü kadar uyarsa veri terimi σ²; bunu fizik terimlerinin tabanıyla karşılaştırın.",
  notes: "Kural aynı: mu çarpı sigma kare, eğitim sonundaki fizik terimleriyle aynı mertebede olmalı. Taban yoksa fizik terimleri çok küçülür ve mu bir bile yeterli olabilir. " +
    "Ama başlangıç evresini unutmayın: Bi çöküşü ilk binlerce adımda oluyor, fizik terimi büyükken. Pratik bir yol, mu'yu terimlerin gradyan büyüklüklerine göre eğitim boyunca uyarlamak; Wang ve arkadaşlarının yöntemi." });

// =========================================================== KAPANIŞ
const SEC4 = "Kapanış";
pres.addSection({ title: SEC4 });
{
  const s = deck.content(SEC4, "Bu dersin üç çıkarımı", { dark: true,
    notes: "Özetleyelim. Bir: Bi'yi parametre yapmak iki satır, ama saf kayıpla Bi sıfıra çöker. Sebep kaybın kendisi: köşe tabanı Bi ile büyür. " +
      "İki: aynı veriyle ulaşılabilecek en iyi sonucu klasik bir modelle ve Cramér–Rao sınırıyla önceden hesaplayın; sensör yeri, sayısından önemli. " +
      "Üç: köşeyi dışlayıp veri terimini fizik tabanıyla aynı mertebeye getirince PINN gürültü sınırına ulaşıyor." });
  const cw = (W - 2 * M - 0.6) / 3;
  [["Saf kayıp çöker", `δ = 0, μ = 1: Bi 2 → ${f2(MS["1"].Bi_est)}. Köşe tabanı c·Bi² yanlış çözümü ödüllendiriyor.`],
   ["Sınırı önce hesapla", `Cramér–Rao: alt şerit %${(100 * crlbPct("n20_bottom")).toFixed(1)}, üst yarı %${(100 * crlbPct("n20_top")).toFixed(1)}. Yer, sayıdan önemli.`],
   ["Gürültü sınırında PINN", `δ = 0.02, μ = 100: |PINN − klasik| = ${f2(REC.gap_over_crlb)} × Cramér–Rao sınırı; başlangıca duyarsız.`]]
    .forEach(([h, b], i) => deck.card(s, { x: M + i * (cw + 0.3), y: BODY_TOP + 0.2, w: cw, h: 2.7, head: h, body: b, num: i + 1, dark: true, headSize: 19, bodySize: 16 }));
  s.addText("Sıradaki adım: Bi'yi girdi yapıp tek eğitimle bütün Bi aralığını çözmek (parametrik vekil model).", { x: M, y: 5.4, w: W - 2 * M, h: 0.5,
    fontSize: 16, color: hex("gumus"), margin: 0, isTextBox: true, objectName: "sum_next" });
}
{
  const s = deck.content(SEC4, "Uygulama: kodu çalıştırın, sonra deneyleri düzeyinize göre yapın", { step: "UYGULAMA",
    notes: "Her ters koşu iki çekirdekte yaklaşık on dakika. Klasik referans bir dakikadan kısa. Lisans öğrencileri sol sütunu, yüksek lisans öğrencileri ayrıca sağ sütunu yapsın. Teslim: bir sayfalık not, bir figür ve bir tablo." });
  s.addShape(pres.shapes.RECTANGLE, { x: M, y: BODY_TOP, w: 4.5, h: 4.35, fill: { color: hex("derin") }, line: { type: "none" }, objectName: "code_bg2" });
  s.addText([
    { text: "python inverse_classical.py", options: { breakLine: true } },
    { text: "python pinn_inverse.py \\", options: { breakLine: true } },
    { text: "  --n-data 20 --skip 0.02 \\", options: { breakLine: true } },
    { text: "  --mu 100 --tag deneme", options: { breakLine: true } },
    { text: "python pinn_inverse.py \\", options: { breakLine: true } },
    { text: "  --mu 1 --tag tuzak", options: { breakLine: true } },
    { text: "python inverse_summary.py", options: {} },
  ], { x: M + 0.25, y: BODY_TOP + 0.25, w: 4.05, h: 3.85, fontFace: "Courier New", fontSize: 13, color: hex("krom"),
    valign: "top", margin: 0, paraSpaceAfter: 8, isTextBox: true, objectName: "code2" });
  const cx = M + 4.8, cw = (W - M - cx - 0.3) / 2;
  deck.card(s, { x: cx, y: BODY_TOP, w: cw, h: 4.35, head: "Lisans",
    body: "1. 20 sensörü alt şeride koyup Bi hatasını düzgünle karşılaştırın.\n2. σ = 0.05 ile Bi'yi bulun; Cramér–Rao sınırı ne öngörüyor?\n3. Öğrenilen Bi'den h ve Q′'yu W/m cinsinden hesaplayın.", headSize: 18, bodySize: 14 });
  deck.card(s, { x: cx + cw + 0.3, y: BODY_TOP, w: cw, h: 4.35, head: "Yüksek lisans",
    body: "1. Yanlılık formülünü δ = 0'da μ = 30 ve 300 için sınayın.\n2. μ'yü gradyan dengeleme ile uyarlayıp δ = 0'da Bi'yi bulun.\n3. Aynı yöntemle k'yı ya da h(x)'i (konuma bağlı) öğrenin.", headSize: 18, bodySize: 14 });
}
{
  const s = deck.content(SEC4, "Sıradaki ders: Bi'yi girdi yapıp bütün aralığı tek eğitimle çözeceğiz", { step: "DERS 05 · ÖNİZLEME",
    notes: "Gelecek ders sekizinci adım, parametrik vekil model. Ağa üçüncü bir girdi ekliyoruz: Bi. Tek bir eğitimden sonra yarım ile yirmi arasındaki her Bi için çözüm bir ileri geçiş kadar ucuz. " +
      "Soru: bu tek ağ, her Bi için ayrı eğitilmiş ağlar kadar doğru mu? Ve ters problemi bu vekil ile milisaniyede çözebilir miyiz?" });
  deck.mathBox(s, ["pv_param"], { x: M, y: BODY_TOP, w: W - 2 * M, h: 1.5 });
  const cw = (W - 2 * M - 0.6) / 3;
  [["Girdi", "(ξ, η, Bi): tek ağ, bütün aralık"], ["Soru", "Ayrı ayrı eğitilmiş ağlar kadar doğru mu?"], ["Bağlantı", "Bugünkü ters problem milisaniyede çözülür"]]
    .forEach(([h, b], i) => deck.card(s, { x: M + i * (cw + 0.3), y: 3.9, w: cw, h: 1.6, head: h, body: b, headSize: 18, bodySize: 14 }));
}
{
  const s = deck.content(SEC4, "Kaynaklar", {
    notes: "Raissi ve arkadaşları ters PINN'i ilk makalede tanıtıyor. Cai ve arkadaşları ısı transferinde bilinmeyen ısı taşınım katsayısını PINN ile buluyor. Kay'in kitabı Cramér–Rao sınırının standart kaynağı. Wang, Teng ve Perdikaris gradyan dengeleme." });
  deck.card(s, { x: M, y: BODY_TOP, w: W - 2 * M, h: 3.1, head: "Okuma listesi",
    body: "M. Raissi, P. Perdikaris, G. E. Karniadakis · Physics-informed neural networks, J. Comput. Phys. 378 (2019) 686–707\n" +
      "S. Cai, Z. Wang, S. Wang, P. Perdikaris, G. E. Karniadakis · Physics-informed neural networks for heat transfer problems, J. Heat Transfer 143 (2021) 060801\n" +
      "S. M. Kay · Fundamentals of Statistical Signal Processing: Estimation Theory, Prentice Hall (1993), Bölüm 3\n" +
      "S. Wang, Y. Teng, P. Perdikaris · Understanding and mitigating gradient flow pathologies in PINNs, SIAM J. Sci. Comput. 43 (2021)\n" +
      "Kod: github.com/mikbalarikan/kolay-pinn · cases/01-2d-heat-conduction/pinn_inverse.py", headSize: 18, bodySize: 14 });
}

const out = path.join(__dirname, "ders04_ters_problem.pptx");
deck.write(out).then((f) => console.log(f));
