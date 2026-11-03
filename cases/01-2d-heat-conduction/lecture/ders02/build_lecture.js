/**
 * Ders 02 · Forward PINN: veri kullanmadan çözmek (Adım 4–5)
 * Önce:  python pinn_forward.py --tag uniform ; python pinn_forward.py --corner --tag corner
 *        python plot_pinn.py ; python lecture/ders02/equations.py ; python lecture/ders02/make_slide_figures.py
 * Sonra: node lecture/ders02/build_lecture.js  ->  lecture/ders02/ders02_forward_pinn.pptx
 */
const fs = require("fs");
const path = require("path");
const D = require(path.join(__dirname, "..", "..", "..", "..", "kolay_pinn", "deck", "turkisi_deck.js"));

const CASE = path.join(__dirname, "..", "..");
const ASSETS = path.join(__dirname, "assets");
const S = JSON.parse(fs.readFileSync(path.join(CASE, "data", "summary_pinn.json"), "utf8"));
const S1 = JSON.parse(fs.readFileSync(path.join(CASE, "data", "summary.json"), "utf8"));
const deck = D.createDeck({ course: "KOLAY PINN", lecture: "Ders 02 · Forward PINN", assets: ASSETS,
  eqDir: path.join(ASSETS, "eq"), title: "Kolay PINN · Ders 02 · Forward PINN: veri kullanmadan çözmek" });
const { pres, C, W, M, BODY_TOP, hex } = deck;
const YL = "YÜKSEK LİSANS";
const U = S.uniform, K = S.corner, X3 = S.skip, REF = S.reference;
const T = (th) => 20 + 50 * th;
const pct = (v) => `%${(100 * v).toFixed(1)}`;
const fmt = (v) => String(Math.round(v)).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
const ALL = [["düzgün", U], ["köşe sıklaştırma", K], ["köşe dışlama", X3]];
const best = ALL.map((a) => a[1]).reduce((a, b) => (b.rel_L2 < a.rel_L2 ? b : a));
const bestName = ALL.find((a) => a[1] === best)[0];
const skipGain = U.rel_L2 / X3.rel_L2, cornerLoss = K.rel_L2 / U.rel_L2, lossDrop = U.final_loss / X3.final_loss;
const ST = JSON.parse(fs.readFileSync(path.join(CASE, "data", "summary_study.json"), "utf8"));
const SU = ST.seeds["düzgün"], SK = ST.seeds["köşe sıklaştırma"], SX = ST.seeds["köşe dışlama"], CAPS = ST.capacity, V = ST.verdict;
const SHARE = JSON.parse(fs.readFileSync(path.join(ASSETS, "robin_share.json"), "utf8"));

const STEPS = [
  { n: 1, t: "Problemi tanımla" }, { n: 2, t: "Boyutsuzlaştır" }, { n: 3, t: "FDM referansı" },
  { n: 4, t: "Forward PINN" }, { n: 5, t: "Doğrula" }, { n: 6, t: "Hibrit PINN" },
  { n: 7, t: "Ters problem" }, { n: 8, t: "Parametrik PINN" }, { n: 9, t: "Framework" },
];
const LOCAL = [{ n: 4, t: "Ağı kur" }, { n: 4, t: "Kayıp ve eğitim" }, { n: 5, t: "Doğrula" }];
const localMap = (k) => LOCAL.map((s, i) => ({ n: i + 1, t: s.t }));

// =========================================================== GİRİŞ
pres.addSection({ title: "Giriş" });
{
  const s = pres.addSlide({ masterName: "KAPAK", sectionTitle: "Giriş" });
  deck.chip(s, "KOLAY PINN · DERS 02", M, 1.7);
  s.addText("Forward PINN:\nveri kullanmadan çözmek", { x: M, y: 2.2, w: 8.6, h: 2.0, fontSize: 44, bold: true,
    color: C.background2, margin: 0, valign: "top", isTextBox: true, objectName: "cover_title" });
  s.addText("Ağ ve katı kısıt · otomatik türev ve kayıp · Adam → L-BFGS · referansa karşı doğrulama",
    { x: M, y: 4.35, w: 8.6, h: 0.9, fontSize: 18, color: hex("gumus"), margin: 0, valign: "top", isTextBox: true, objectName: "cover_sub" });
  s.addText("Lisans ve yüksek lisans · Adım 4–5 · yaklaşık 50 dakika", { x: M, y: 6.2, w: 8, h: 0.4, fontSize: 13,
    color: hex("titanyum"), margin: 0, isTextBox: true, objectName: "cover_meta" });
  s.addImage({ path: deck.A("maskot_mutlu.png"), x: 9.4, y: 1.6, w: 3.4, h: 3.4, objectName: "cover_mascot" });
  s.addNotes("Geçen derste aynı problemi sonlu farklarla çözdük ve seri çözümle doğruladık. Bugün aynı problemi bir sinir ağıyla, hiç veri kullanmadan çözeceğiz. " +
    "Ağa yalnızca fiziği, yani Laplace denklemini ve sınır koşullarını öğreteceğiz. Sonra geçen dersin referansıyla karşılaştırıp PINN'in nerede iyi, nerede zayıf olduğunu ölçeceğiz.");
}
{
  const s = deck.content("Giriş", "Bu dersin sonunda dört şeyi yapabileceksiniz", {
    notes: "İlk iki hedef kodun iskeleti: ağı kurmak ve kaybı yazmak. Üçüncüsü eğitim stratejisi. Dördüncüsü bu kursun ana fikri: bir PINN'i kayıp eğrisiyle değil, bağımsız bir referansla değerlendirmek. " +
      "Yüksek lisans öğrencilerinden ayrıca PINN ile FDM arasındaki ödünleşimi savunabilmelerini bekliyorum." });
  const objs = [
    ["Ağı ve katı kısıtı kurmak", "Dirichlet kenarlarını ağın yapısına gömüp kayıptan çıkarmak."],
    ["Kaybı otomatik türevle yazmak", "Laplace ve Robin artıklarını ağın kendisinden, kesin türevle hesaplamak."],
    ["Eğitim stratejisini uygulamak", "Adam ile kaba arama, L-BFGS ile ince ayar; kolokasyon seçimi."],
    ["Referansa karşı doğrulamak", "L₂ hata, köşe hata haritası ve Q′ ile ölçmek; PINN–FDM ödünleşimini tartışmak."],
  ];
  const cw = (W - 2 * M - 0.3) / 2, ch = 2.05;
  objs.forEach(([h, b], i) => deck.card(s, { x: M + (i % 2) * (cw + 0.3), y: BODY_TOP + Math.floor(i / 2) * (ch + 0.3),
    w: cw, h: ch, head: h, body: b, num: i + 1, headSize: 18, bodySize: 15 }));
}
{
  const s = deck.content("Giriş", "Bugün referans çözümü bir sinir ağıyla yeniden üretiyoruz", {
    notes: "Yol haritasında dördüncü ve beşinci adımdayız. Ders 01'den iki şey getiriyoruz: doğruluğu ölçeceğimiz seri çözüm ve FDM, bir de uyarı: zorluk alt köşelerde. " +
      "Bugün o uyarının PINN için de geçerli olup olmadığını göreceğiz." });
  deck.roadmap(s, STEPS, new Set([4, 5]), { y: 2.6 });
  deck.card(s, { x: M, y: 4.6, w: 5.9, h: 1.6, head: "Ders 01'den gelen referans",
    body: `Seri çözüm (4000 terim) ve FDM (N = 101, bağıl L₂ ${deck.sci(S1.fdm_N101.rel_L2)}). Alt orta ${S1.fdm_N101.T_mid_bottom_C.toFixed(1)} °C.` });
  deck.card(s, { x: M + 6.2, y: 4.6, w: W - 2 * M - 6.2, h: 1.6, head: "Ders 01'in uyarısı",
    body: "Hata alt köşelerde toplanır; maksimum hata yalnız birinci mertebe yakınsar. PINN'i orada sınayacağız." });
}
{
  const s = deck.content("Giriş", "Bu derste altı kavrama yaslanacağız", {
    notes: "Sözlük. MLP: katmanlar halinde doğrusal dönüşüm ve aktivasyon. tanh: türevleri düzgün bir aktivasyon. Otomatik türev: ağın çıktısının girdiye göre türevini kesin hesaplar. " +
      "Kolokasyon noktası: denklemi zorladığımız nokta. Katı kısıt: sınır koşulunu ağın yapısına gömmek. L-BFGS: eğriliği yaklaşıklayan yarı Newton yöntemi." });
  const terms = [
    ["Çok katmanlı ağ (MLP)", "g_mlp", "Doğrusal katman + aktivasyon, art arda", 0.78],
    ["Aktivasyon", "g_tanh", "Türevleri düzgün; ikinci türevi sıfır değil", 1],
    ["Otomatik türev", "g_ad", "Türev, ağın hesap grafiğinden kesin", 0.9],
    ["Kolokasyon noktaları", "g_col", "Denklemin zorlandığı noktalar; ağ gerekmez", 1],
    ["Katı kısıt", "g_hard", "Sınır koşulu ağın yapısında, kayıpta değil", 1],
    ["L-BFGS", "g_lbfgs", "Eğriliği yaklaşıklayan yarı Newton yöntemi", 1],
  ];
  const cw = (W - 2 * M - 0.6) / 3, ch = 2.15;
  terms.forEach(([h, m, b, sc], i) => deck.card(s, { x: M + (i % 3) * (cw + 0.3), y: BODY_TOP + Math.floor(i / 3) * (ch + 0.25),
    w: cw, h: ch, head: h, math: m, mathScale: sc, body: b, headSize: 17, bodySize: 14 }));
}

// =========================================================== 1 · AĞI KUR
const SEC1 = "1 · Ağı kur";
deck.section(SEC1, "01", "Ağı kur", "Fonksiyon yaklaşımı, katı kısıt ve aktivasyon seçimi",
  { roadmapSteps: localMap(), active: new Set([1]),
    notes: "Birinci bölüm: PINN'in ne olduğunu ve ağı nasıl kurduğumuzu konuşuyoruz. Kayıp ve eğitim ikinci bölümde." });
{
  const s = deck.content(SEC1, "PINN, denklemin artığını sıfıra iten bir fonksiyon yaklaşımıdır", { step: "ADIM 4 · FİKİR",
    notes: "Akışı soldan sağa okuyalım. Girdi bir nokta, xi ve eta. Ağ bir sayı üretiyor. Katı kısıtla bunu theta şapkaya çeviriyoruz. " +
      "Otomatik türevle Laplace'ı ve alt kenardaki Robin artığını hesaplıyoruz. Bu artıkların ortalama karesi kayıp. Optimizer ağırlıkları kaybı azaltacak şekilde güncelliyor ve döngü tekrar ediyor. " +
      "Kritik nokta: hiçbir yerde ölçüm verisi ya da çözüm yok. Ağ yalnızca denklemi sağlamaya zorlanıyor." });
  const y = BODY_TOP + 0.2, bh = 1.15;
  const boxes = [
    { t: "(ξ, η)", l: "kolokasyon noktası", w: 1.7 },
    { t: "MLP 4 × 50\ntanh", l: "N(ξ, η)", w: 1.9 },
    { t: "katı kısıt", l: "Dirichlet gömülü", w: 1.8 },
    { t: "otomatik türev", l: "kesin türevler", w: 2.0 },
    { t: "kayıp L", l: "PDE + Robin", w: 1.6, accent: true },
  ];
  const gap = (W - 2 * M - boxes.reduce((a, b) => a + b.w, 0)) / (boxes.length - 1);
  let x = M;
  boxes.forEach((b, i) => {
    s.addText(b.t, { x, y, w: b.w, h: bh, shape: pres.shapes.RECTANGLE, fill: { color: hex("krom") },
      line: b.accent ? { color: hex("plan"), width: 2.5 } : { type: "none" }, color: C.text1, bold: true,
      fontSize: 16, align: "center", valign: "middle", margin: 4, isTextBox: true, objectName: `flow_box_${i}` });
    s.addText(b.l, { x, y: y + bh + 0.1, w: b.w, h: 0.4, fontSize: 13, color: hex("titanyum"), align: "center",
      margin: 0, isTextBox: true, objectName: `flow_lbl_${i}` });
    if (i < boxes.length - 1) s.addText("→", { x: x + b.w, y: y + 0.28, w: gap, h: 0.6, fontSize: 24, color: hex("titanyum"),
      align: "center", margin: 0, isTextBox: true, objectName: `flow_arr_${i}` });
    x += b.w + gap;
  });
  s.addText("↺  optimizer ağırlıkları günceller: Adam → L-BFGS", { x: M, y: y + bh + 0.6, w: W - 2 * M, h: 0.4, fontSize: 14,
    color: hex("celik_mavisi"), bold: true, align: "center", margin: 0, isTextBox: true, objectName: "flow_loop" });
  deck.mathBox(s, ["residual"], { x: M, y: 4.55, w: 6.2, h: 1.6, label: "PDE ARTIĞI" });
  deck.card(s, { x: M + 6.5, y: 4.55, w: W - 2 * M - 6.5, h: 1.6, head: "Veri yok",
    body: "Ağ hiçbir çözüm değeri görmüyor; yalnızca denklemi ve sınır koşullarını sağlamaya zorlanıyor." });
}
{
  const s = deck.content(SEC1, "Katı kısıt, üç Dirichlet kenarını kayıptan tamamen çıkarır", { step: "ADIM 4 · KATI KISIT",
    notes: "Ağın çıktısını doğrudan theta olarak kullanmıyoruz. Bir eklemiyoruz ve ağı bir mesafe fonksiyonu d ile çarpıyoruz. " +
      "d üç kenarda sıfır: xi sıfır, xi bir ve eta bir. Orada theta şapka ağ ne üretirse üretsin tam olarak bir. Alt kenarda d sıfır değil, çünkü orada değeri bilmiyoruz; onu Robin kaybı öğretecek. " +
      "Avantajı: kayıpta üç terim eksik, sınır hatası sıfır ve kayıp terimlerini dengelemekle uğraşmıyoruz. Bedeli: karmaşık geometride bu d fonksiyonunu kurmak zor." });
  deck.image(s, "01_distance.png", { x: M, y: BODY_TOP - 0.1, w: 5.6, h: 4.85 }, "left");
  deck.mathBox(s, ["hard", "hard_check"], { x: 6.5, y: BODY_TOP, w: W - M - 6.5, h: 2.2, gap: 0.3, scale: 0.92 });
  deck.card(s, { x: 6.5, y: BODY_TOP + 2.45, w: (W - M - 6.5 - 0.3) / 2, h: 2.1, head: "Kazanç",
    body: "Kayıpta iki terim kalır; Dirichlet kenarlarında hata tam sıfır." });
  deck.card(s, { x: 6.5 + (W - M - 6.5 - 0.3) / 2 + 0.3, y: BODY_TOP + 2.45, w: (W - M - 6.5 - 0.3) / 2, h: 2.1, head: "Bedel",
    body: "d her geometri için elle kurulur; karmaşık sınırda zorlaşır." });
}
{
  const s = deck.content(SEC1, "Aktivasyonun ikinci türevi sıfır olmamalı: ReLU Laplace'ı göremez", { step: "ADIM 4 · AKTİVASYON",
    notes: "Bu tuzak çok sık yapılıyor. Görüntü sınıflandırmada standart olan ReLU parçalı doğrusal; ikinci türevi hemen her yerde sıfır. " +
      "PDE artığımız ikinci türev içeriyor. ReLU ağı ile Laplace hesaplarsanız her yerde sıfır bulursunuz; kayıp sıfırdır ama ağ hiçbir şey öğrenmemiştir. " +
      "tanh'ın ikinci türevi düzgün ve sıfırdan farklı; bu yüzden PINN'lerde tanh, sinüs ya da GELU gibi düzgün aktivasyonlar kullanılır." });
  deck.image(s, "02_activations.png", { x: M, y: BODY_TOP - 0.05, w: W - 2 * M, h: 3.4 });
  deck.mathBox(s, ["relu_dd"], { x: M, y: 5.35, w: 7.4, h: 1.0 });
  deck.caption(s, "PDE ikinci türev içeriyorsa aktivasyon en az iki kez düzgün türevlenebilir olmalı: tanh, sin, GELU.",
    { x: M + 7.7, y: 5.45, w: W - 2 * M - 7.7, h: 0.9 });
}
deck.question(SEC1, "Katı kısıt olmasaydı, yani ağın çıktısını doğrudan kullansaydık, kayba ne eklememiz gerekirdi? Hangi yeni sorun doğardı?", {
  hint: "İpucu: üç kenardaki koşul artık yapı gereği sağlanmıyor.",
  notes: "Üç Dirichlet kenarı için ayrı bir kayıp terimi: kenar noktalarında theta şapka eksi bir'in karesi. Bu yumuşak kısıt. " +
    "Yeni sorun: artık üç terimli bir kayıp var ve ağırlıklarını dengelemek gerekiyor. Ağırlık küçükse sınır koşulu tam sağlanmaz; büyükse PDE terimi ihmal edilir. Wang, Teng ve Perdikaris 2021 bu gradyan dengesizliğini inceliyor." });

// =========================================================== 2 · KAYIP VE EĞİTİM
const SEC2 = "2 · Kayıp ve eğitim";
deck.section(SEC2, "02", "Kayıp ve eğitim", "Otomatik türev, kolokasyon, kayıp ve optimizer",
  { roadmapSteps: localMap(), active: new Set([2]),
    notes: "İkinci bölüm: kaybı yazıyoruz ve ağı eğitiyoruz." });
{
  const s = deck.content(SEC2, "Otomatik türev, Laplace'ı ağın kendisinden kesin olarak hesaplar", { step: "ADIM 4 · TÜREV",
    notes: "Sonlu farkta türevi komşu düğümlerden yaklaşıklıyorduk. Burada türev kesin: ağ bir fonksiyon ve PyTorch onun hesap grafiğini tutuyor. " +
      "Birinci türevi alıyoruz, create graph true diyoruz ki o türevin de türevini alabilelim. İkinci çağrı ikinci türevi veriyor. " +
      "Maliyet: her iç nokta için iki geri yayılım. Bizim problemde bir Adam adımı iki çekirdekte yaklaşık 70 milisaniye." });
  deck.mathBox(s, ["lap_ad"], { x: M, y: BODY_TOP, w: 5.6, h: 1.7 });
  s.addShape(pres.shapes.RECTANGLE, { x: 6.5, y: BODY_TOP, w: W - M - 6.5, h: 3.05, fill: { color: hex("derin") }, line: { type: "none" }, objectName: "code_bg" });
  s.addText([
    { text: "th = theta_hat(model, X)", options: { breakLine: true } },
    { text: "g  = grad(th, X, create_graph=True)", options: { breakLine: true } },
    { text: "th_xx = grad(g[:, 0], X)[:, 0]", options: { breakLine: true } },
    { text: "th_yy = grad(g[:, 1], X)[:, 1]", options: { breakLine: true } },
    { text: "r_pde = th_xx + th_yy             # → 0", options: {} },
  ], { x: 6.75, y: BODY_TOP + 0.25, w: W - M - 7.0, h: 2.6, fontFace: "Courier New", fontSize: 14, color: hex("krom"),
    valign: "top", margin: 0, paraSpaceAfter: 9, isTextBox: true, objectName: "code" });
  const cw = (W - 2 * M - 0.6) / 3;
  [["Kesin türev", "Kesme hatası yok; hata yalnız ağın yaklaşıklığından gelir."],
   ["Ağ gerekmez", "Nokta bulutu yeter; geometri değişince yeniden örneklemek yeterli."],
   ["Maliyet", "Her iç nokta için iki geri yayılım; FDM'den çok daha pahalı."]]
    .forEach(([h, b], i) => deck.card(s, { x: M + i * (cw + 0.3), y: 5.3, w: cw, h: 1.15, head: h, body: b, headSize: 16, bodySize: 13 }));
}
{
  const s = deck.content(SEC2, "Kolokasyon noktaları alanı örter; köşeler için üç strateji deneyeceğiz", { step: "ADIM 4 · KOLOKASYON",
    notes: "Solda Sobol dizisiyle düzgün örtülmüş 4096 iç nokta ve alt kenarda 256 Robin noktası. Sobol rastgele örneklemeden daha düzgün; boşluk ve kümelenme daha az. " +
      "Ortada Ders 01'in sezgisi: hata köşede toplanıyorsa oraya nokta koy. Alt köşelere logaritmik yoğunlukla 1024 iç ve 128 Robin noktası ekledik. " +
      "Sağda tersi: köşeden 0.02 mesafedeki Robin noktalarını kayıptan çıkardık. Neden böyle bir şey deneyeceğimizi birazdan kayıp tabanı slaytında göreceksiniz. Üç koşuyu karşılaştıracağız." });
  deck.image(s, "03_collocation.png", { x: M, y: BODY_TOP - 0.1, w: W - 2 * M, h: 4.3 });
  deck.mathBox(s, ["corner"], { x: M + 1.6, y: 6.2, w: 9.0, h: 0.6 });
}
{
  const s = deck.content(SEC2, "Kayıp, iki artığın ortalama karesidir", { step: "ADIM 4 · KAYIP",
    notes: "Birinci terim iç noktalardaki Laplace artığı, ikinci terim alt kenardaki Robin artığı. İkisinin ortalama karesi. " +
      "Lambda Robin teriminin ağırlığı. Boyutsuz formda iki terim aynı ölçekte olduğu için lambda bir ile başlıyoruz; Ders 01'deki boyutsuzlaştırma burada karşılığını veriyor. " +
      "Dirichlet terimi yok: katı kısıt onu yapı gereği sağladı." });
  deck.mathBox(s, ["loss"], { x: M, y: BODY_TOP, w: W - 2 * M, h: 1.6, scale: 0.98 });
  const cw = (W - 2 * M - 0.6) / 3;
  [["İç noktalar", "nr", "Sobol, alanın tamamı"],
   ["Alt kenar", "nb", "Robin artığının zorlandığı noktalar"],
   ["Robin ağırlığı", "lam1", "boyutsuz formda terimler aynı ölçekte"]]
    .forEach(([h, m, b], i) => deck.card(s, { x: M + i * (cw + 0.3), y: 3.95, w: cw, h: 1.85, head: h, math: m, body: b, headSize: 16, bodySize: 14 }));
  deck.caption(s, "Dirichlet terimi yok: katı kısıt üç kenarı yapı gereği sağlıyor.", { x: M, y: 6.05, w: W - 2 * M, h: 0.4 });
}
{
  const s = deck.content(SEC2, "Adam kaba arar, L-BFGS ince ayar yapar", { step: "ADIM 4 · EĞİTİM",
    notes: `Önce Adam: 6000 adım, öğrenme oranı on üzeri eksi üçten on üzeri eksi dörde üstel olarak düşüyor. Adam gürültülü ve kaba ama kötü başlangıçtan kurtulmakta iyi. ` +
      `Sonra L-BFGS: eğriliği geçmiş gradyanlardan yaklaşıklayan yarı Newton yöntemi. İyi bir havzaya geldikten sonra kaybı birkaç mertebe daha indiriyor; grafikte gri bölgedeki keskin düşüş bu. ` +
      `Toplam süre iki çekirdekte yaklaşık ${Math.round(U.t_total_s / 60)} dakika. Aynı problemi FDM bir saniyenin altında çözüyordu; bunu karşılaştırmada konuşacağız.` });
  deck.image(s, "04_loss.png", { x: M, y: BODY_TOP - 0.1, w: 7.4, h: 4.6 }, "left");
  const x0 = 8.4, sw = W - M - x0;
  deck.mathBox(s, ["adam_lr"], { x: x0, y: BODY_TOP, w: sw, h: 0.9 });
  deck.card(s, { x: x0, y: BODY_TOP + 1.1, w: sw, h: 1.45, head: "Adam · 6000 adım", body: "Kaba arama; kötü başlangıçtan kurtulur." });
  deck.card(s, { x: x0, y: BODY_TOP + 2.75, w: sw, h: 1.45, head: "L-BFGS · ≤ 2000 değerlendirme", body: "Strong Wolfe çizgi araması; kaybı mertebelerce indirir." });
  deck.caption(s, `Son kayıp ${deck.sci(U.final_loss)} · süre ${Math.round(U.t_total_s)} s (2 CPU çekirdeği)`, { x: x0, y: BODY_TOP + 4.35, w: sw, h: 0.4 });
}
{
  const s = deck.content(SEC2, `Kaybın tabanını köşe çelişkisi belirler: kenarın %2'lik köşe şeridi Robin kaybında %${Math.round(100 * SHARE.uniform)} paya sahip`, { step: "ADIM 4 · KAYIP TABANI", level: YL,
    notes: `Eğitimin sonunda toplam kayıp ${deck.sci(U.final_loss)} civarında kalıyor ve neredeyse tamamı Robin teriminden geliyor. İlk refleks ağı büyütmek olur; yanlış. ` +
      `Alt kenar boyunca Robin artığına bakın: ortada on üzeri eksi iki mertebesinde, köşelere yaklaşınca Bi'ye, yani 4.89'a çıkıyor. Kaybın yüzde ${Math.round(100 * SHARE.uniform)} kadarı kenarın yüzde ikilik köşe şeridinden geliyor. ` +
      "Sebep fizik: yan duvarda theta her yerde bir, dolayısıyla duvar boyunca eta türevi sıfır. Robin ise köşede bu türevin Bi olmasını istiyor. İki koşul köşe noktasında çelişiyor; hiçbir düzgün fonksiyon ikisini birden sağlayamaz. Bu, Ders 01'deki köşe tekilliğinin kayıptaki yansıması. " +
      "Çıkarım: PINN'de kaybın mutlak değeri doğruluk ölçüsü değildir. Problemin kendisi sıfır olmayan bir taban koyabilir. Doğruluğu referansla ölçeriz." });
  deck.image(s, "08_robin_residual.png", { x: M, y: BODY_TOP - 0.1, w: 7.4, h: 3.55 }, "left");
  deck.mathBox(s, ["conflict"], { x: M, y: 5.65, w: 7.4, h: 1.05, scale: 0.78 });
  const x0 = 8.4, sw = W - M - x0;
  deck.stat(s, { x: x0, y: BODY_TOP, w: sw, value: `%${Math.round(100 * SHARE.uniform)}`, unit: "", label: "Robin kaybının köşe şeridindeki payı (kenarın %2'si)" });
  deck.card(s, { x: x0, y: BODY_TOP + 1.6, w: sw, h: 2.95, head: "Çıkarım",
    body: `Köşe çelişkisi sıfır olmayan bir taban koyar; ağı büyütmek kaldırmaz. Köşe noktaları dışlanınca kayıp ${Math.round(lossDrop)} kat düşüyor (3. bölüm).` });
}
deck.question(SEC2, "Neden önce Adam, sonra L-BFGS? Doğrudan L-BFGS ile başlasak ne olurdu?", {
  hint: "İpucu: L-BFGS eğriliği geçmiş gradyanlardan tahmin eder ve çizgi araması yapar.",
  notes: "L-BFGS yerel ve deterministik bir yöntem; kötü bir başlangıçta eğrilik tahmini anlamsız olur ve çizgi araması küçük adımlarla takılır ya da kötü bir yerel minimuma gider. " +
    "Adam gürültülü adımlarla kayıp yüzeyinin kaba yapısını aşar. İyi bir havzaya girince L-BFGS'in süperlineer yakınsaması devreye girer. Pratikte Adam'ın sonundaki plato, L-BFGS'e geçme zamanını gösterir." });

// =========================================================== 3 · DOĞRULA
const SEC3 = "3 · Doğrula";
deck.section(SEC3, "03", "Doğrula", "Seri çözüme ve FDM'ye karşı: alan, köşeler ve ısı akısı",
  { roadmapSteps: localMap(), active: new Set([3]),
    notes: "Üçüncü bölüm: PINN'i Ders 01'in referansıyla karşılaştırıyoruz. Toplam kaybı değil; alanı, hata haritasını ve mühendislik çıktısını." });
{
  const s = deck.content(SEC3, `PINN sıcaklık alanını yakalıyor: alt orta ${T(U.theta_mid_bottom).toFixed(1)} °C, referans ${T(REF.theta_mid_bottom).toFixed(1)} °C`, { step: "ADIM 5 · ALAN",
    notes: `PINN'in sıcaklık alanı, düzgün kolokasyonla. Gözle Ders 01'deki FDM alanından ayırt edilemiyor. ` +
      `Alt yüzeyin ortasında PINN ${T(U.theta_mid_bottom).toFixed(2)} derece, seri çözüm ${T(REF.theta_mid_bottom).toFixed(2)} derece veriyor. Bağıl L2 hata ${deck.sci(U.rel_L2)}. ` +
      `Ama FDM'nin aynı ağdaki hatası ${deck.sci(REF.rel_L2_fdm_N201)}; yani PINN bu problemde FDM'den daha az doğru. Bunu dürüstçe söylemek gerekiyor.` });
  deck.image(s, "05_pinn_field.png", { x: M, y: BODY_TOP - 0.1, w: 6.2, h: 4.85 }, "left");
  const x0 = 7.4, sw = W - M - x0;
  deck.stat(s, { x: x0, y: BODY_TOP, w: sw, value: deck.sci(U.rel_L2), unit: "", label: "bağıl L₂ hata, PINN (düzgün)" });
  deck.stat(s, { x: x0, y: BODY_TOP + 1.45, w: sw, value: deck.sci(REF.rel_L2_fdm_N201), unit: "", label: "bağıl L₂ hata, FDM (N = 201)", color: hex("titanyum") });
  deck.mathBox(s, ["relL2"], { x: x0, y: BODY_TOP + 2.95, w: sw, h: 1.3 });
}
{
  const title = `Köşeye nokta eklemek hatayı ${cornerLoss.toFixed(1)} kat artırır; köşeyi dışlamak kaybı ${Math.round(lossDrop)} kat düşürür ama hatayı değiştirmez`;
  const s = deck.content(SEC3, title, { step: "ADIM 5 · KÖŞELER · TOHUM 0",
    notes: `Üç koşunun hata haritası. Solda düzgün kolokasyon: bağıl L2 ${deck.sci(U.rel_L2)}, en büyük hata yine alt köşede, ${deck.sci(U.max_err)}. ` +
      `Ortada köşe sıklaştırma. FDM sezgisiyle beklentimiz iyileşmeydi; tersi oldu: bağıl L2 ${deck.sci(K.rel_L2)}, yani ${cornerLoss.toFixed(1)} kat daha kötü ve bozulma tüm alana yayılıyor. ` +
      "Sebep kayıp tabanı slaytında gördüğümüz çelişki: köşeye eklenen her nokta, hiçbir düzgün fonksiyonun sağlayamayacağı bir artık taşıyor. Bu noktalar kaybı domine ediyor ve optimizer, onları biraz azaltmak için alanın geri kalanını feda ediyor. " +
      `Sağda tersini yaptık: köşe şeridindeki Robin noktalarını kayıptan çıkardık. Toplam kayıp ${Math.round(lossDrop)} kat düştü, ${deck.sci(U.final_loss)}'den ${deck.sci(X3.final_loss)}'e. Ama bağıl L2 ${deck.sci(X3.rel_L2)}: düzgün koşuyla neredeyse aynı. ` +
      "İki ders var. Bir: FDM'de çözünürlüğü zor yere yığmak işe yarar; PINN'de çözümü olmayan noktaları çoğaltmak tüm çözümü bozar. " +
      "Bu sayılar tohum sıfırdan; birkaç slayt sonra üç tohumla tekrarlayıp bulguların sağlam olduğunu göreceğiz. " +
      "İki: kayıp iki yüz kat düştü ama çözüm iyileşmedi. Kayıp tabanı köşeden geliyordu ve çözümün geri kalanına zarar vermiyordu. Kaybın küçülmesi çözümün iyileştiği anlamına gelmez; bu kursun ana cümlesi." });
  deck.image(s, "06_error_maps.png", { x: M, y: BODY_TOP - 0.15, w: W - 2 * M, h: 4.25 });
  const cw = (W - 2 * M - 0.6) / 3;
  ALL.forEach(([n, r], i) => deck.card(s, { x: M + i * (cw + 0.3), y: 6.0, w: cw, h: 0.72,
    head: `${n}: L₂ ${deck.sci(r.rel_L2)} · Q′ ${pct(r.Q_rel_err)}`, headSize: 13 }));
}
{
  const s = deck.content(SEC3, `Mühendislik çıktısı Q′: en iyi koşu referansın ${pct(best.Q_rel_err)} içinde`, { step: "ADIM 5 · ISI AKISI",
    notes: `Alt yüzey boyunca hata. FDM gri, üç PINN renkli. Ortada PINN hatası on binde bir mertebesinde; köşelere yaklaştıkça artıyor. ` +
      `Mühendislik açısından asıl soru alttan ne kadar ısı çekildiği. Seri çözüm ${fmt(REF.Q_W_m)} watt bölü metre. ` +
      `Düzgün koşu ${fmt(U.Q_W_m)}, yüzde ${(100 * U.Q_rel_err).toFixed(2)} hata; köşe sıklaştırma ${fmt(K.Q_W_m)}, yüzde ${(100 * K.Q_rel_err).toFixed(2)}; köşe dışlama ${fmt(X3.Q_W_m)}, yüzde ${(100 * X3.Q_rel_err).toFixed(2)}.` });
  deck.image(s, "07_bottom_error.png", { x: M, y: BODY_TOP - 0.1, w: 7.6, h: 3.75 }, "left");
  deck.mathBox(s, ["qprime"], { x: M, y: 5.85, w: 7.3, h: 0.85, scale: 0.9 });
  const x0 = 8.6, sw = W - M - x0;
  [[REF.Q_W_m, "seri çözüm", hex("titanyum")], [U.Q_W_m, `düzgün · ${pct(U.Q_rel_err)}`, hex("plan")],
   [K.Q_W_m, `köşe sıklaştırma · ${pct(K.Q_rel_err)}`, hex("parca_mandalina")], [X3.Q_W_m, `köşe dışlama · ${pct(X3.Q_rel_err)}`, hex("lila")]]
    .forEach(([v, l, col], i) => deck.stat(s, { x: x0, y: BODY_TOP + i * 1.12, w: sw, value: fmt(v), unit: "W/m", label: l, color: col }));
}
{
  const cap = (n) => CAPS[n].rel_L2;
  const s = deck.content(SEC3, `Tohum değiştirmek hatayı ${(SU.rel_L2.max / SU.rel_L2.min).toFixed(0)} kat oynatır; daha büyük ağ ya da uzun eğitim bu aralığın dışına çıkmaz`, { step: "ADIM 5 · SAĞLAMLIK", level: YL,
    notes: "Buraya kadar her koşu tek bir tohumla yapıldı. Bilimsel olarak bu yetmez; aynı ayarı farklı rastgele başlatma ve farklı kolokasyon noktalarıyla tekrarladık. " +
      `Solda üç strateji, üçer tohum. Düzgün kolokasyonda bağıl L2 ${deck.sci(SU.rel_L2.min)} ile ${deck.sci(SU.rel_L2.max)} arasında; yani yalnız tohum değiştirerek ${(SU.rel_L2.max / SU.rel_L2.min).toFixed(0)} kat fark görüyoruz. Bizim ilk koşumuz, tohum sıfır, şanssız tohummuş: üçünün en kötüsü. ` +
      `Köşe sıklaştırma her tohumda düzgünden kötü; ortalamada ${V.corner_vs_uniform_ratio_of_means.toFixed(1)} kat. Bu bulgu sağlam. Köşe dışlamanın aralığı ise düzgünle örtüşüyor: hatayı değiştirmiyor, ama kaybı ortalamada ${Math.round(V.loss_ratio_uniform_over_skip)} kat düşürüyor. Kayıp doğruluk değildir cümlesi de sağlam. ` +
      `Sağda sizin sorunuz: daha uzun eğitim, daha geniş ya da daha derin ağ. Uzun L-BFGS ${deck.sci(cap("uzun L-BFGS (6000)"))}, geniş ağ ${deck.sci(cap("geniş 4×100"))}; ikisi de tohum aralığının içinde, süre ise bir buçuk ila iki kat. Derin ağ ${deck.sci(cap("derin 8×50"))}, daha kötü. ` +
      "Sonuç: bu problemde hatayı kapasite ya da eğitim süresi sınırlamıyor; köşe tekilliği ve optimizasyonun rastgeleliği sınırlıyor. Bir PINN sonucunu raporlarken en az üç tohumun ortalamasını ve aralığını verin." });
  deck.image(s, "09_robustness.png", { x: M, y: BODY_TOP - 0.1, w: W - 2 * M, h: 4.3 });
  const cw = (W - 2 * M - 0.6) / 3;
  [[`düzgün: ${deck.sci(SU.rel_L2.mean)} ± ${deck.sci(SU.rel_L2.std)}`, hex("plan")],
   [`köşe sıklaştırma: her tohumda kötü · ${V.corner_vs_uniform_ratio_of_means.toFixed(1)}×`, hex("parca_mandalina")],
   [`köşe dışlama: hata aynı aralıkta · kayıp ${Math.round(V.loss_ratio_uniform_over_skip)}× düşük`, hex("lila")]]
    .forEach(([h], i) => deck.card(s, { x: M + i * (cw + 0.3), y: 6.05, w: cw, h: 0.68, head: h, headSize: 12 }));
}
deck.question(SEC3, "Tek bir eğitim koşusunun sonucunu rapora yazmak neden yeterli değil? Hangi iki şeyi birlikte vermelisiniz?", {
  hint: "İpucu: tohum hem ağırlık başlatmayı hem kolokasyon noktalarını değiştirir.",
  notes: `Tohum değiştirmek bu problemde hatayı ${(SU.rel_L2.max / SU.rel_L2.min).toFixed(0)} kat oynattı; tek koşu bu dağılımdan rastgele bir örnek. İki stratejiyi karşılaştırırken farkın tohum aralığından büyük olup olmadığına bakmalıyız. ` +
    "Raporlanacak iki şey: en az üç tohumun ortalaması ve yayılımı, ve bağımsız bir referansa karşı hata. Kapasite ya da eğitim süresini artırmak ancak bu aralığın dışına çıkarsa anlamlı bir iyileşmedir." });
{
  const s = deck.content(SEC3, "Bu problemde FDM daha doğru ve hızlı; PINN'in kazancı başka yerde", { step: "ADIM 5 · ÖDÜNLEŞİM", level: YL,
    notes: "Dürüst karşılaştırma. Bu basit, iki boyutlu, doğrusal problemde FDM hem daha doğru hem binlerce kat daha hızlı. PINN'i burada FDM'nin yerine önermiyoruz. " +
      "PINN'in kazancı tablonun alt satırlarında: ağ gerekmiyor, çözüm sürekli ve türevlenebilir, ve en önemlisi ölçüm verisini ve bilinmeyen parametreleri aynı kayba koyabiliyoruz. " +
      "Önümüzdeki dersler tam olarak bunları kullanacak: hibrit PINN, ters problem ve parametrik PINN." });
  const rows = [
    ["", "FDM (N = 101)", "PINN (4 × 50, tanh)"],
    ["Bağıl L₂ hata", deck.sci(S1.fdm_N101.rel_L2), `${deck.sci(best.rel_L2)} (${bestName})`],
    ["Süre (2 CPU)", "< 1 s", `≈ ${Math.round(U.t_total_s)} s`],
    ["Ağ / mesh", "gerekli", "gerekmez, nokta bulutu"],
    ["Çözüm", "düğüm değerleri", "sürekli, türevlenebilir fonksiyon"],
    ["Yeni Bi", "yeniden çöz (ms)", "yeniden eğit · Adım 8: parametrik"],
    ["Ölçüm verisi ekleme", "zor (veri asimilasyonu)", "kayba bir terim · Adım 6"],
    ["Bilinmeyen parametre", "dış optimizasyon döngüsü", "aynı eğitimde · Adım 7"],
  ].map((r, i) => r.map((t, j) => ({ text: t, options: { bold: i === 0 || j === 0, color: i === 0 ? "FFFFFF" : hex("derin"),
    fill: { color: i === 0 ? hex("celik_mavisi") : (i >= 5 && j === 2 ? "E3F4F6" : (i % 2 ? "FFFFFF" : hex("krom"))) } } })));
  s.addTable(rows, { x: M, y: BODY_TOP, w: W - 2 * M, colW: [3.1, 4.0, W - 2 * M - 7.1], fontSize: 15, fontFace: "Arial",
    rowH: 0.52, border: { type: "solid", pt: 0.5, color: hex("gumus") }, margin: [0.04, 0.12, 0.04, 0.12], valign: "middle", objectName: "tradeoff" });
  deck.caption(s, "Vurgulu satırlar: PINN'i sonraki adımlarda değerli kılan özellikler.", { x: M, y: 6.3, w: W - 2 * M, h: 0.35 });
}
deck.question(SEC3, "FDM'de köşeye çözünürlük eklemek işe yarar. PINN'de köşeye nokta eklemek neden ters tepti?", {
  hint: "İpucu: kayıp, kolokasyon noktalarındaki artıkların ortalamasıdır. Köşedeki artık sıfırlanabilir mi?",
  notes: "FDM'de her düğüm kendi denklemini tam olarak sağlar; köşeye düğüm eklemek oradaki ayrıklaştırma hatasını azaltır ve başka yeri etkilemez. " +
    "PINN'de ise tek bir düzgün fonksiyon bütün noktalardaki artıkların ortalamasını küçültmeye çalışır. Köşedeki Robin artığı hiçbir düzgün fonksiyonla sıfırlanamaz; o noktaları çoğaltmak kaybın ağırlığını oraya kaydırır ve optimizer o imkânsız terimi azaltmak için alanın geri kalanını bozar. " +
    "Çare: çelişkili noktaları dışlamak, ağırlığını düşürmek ya da tekilliği çözüme analitik olarak eklemek. Bi = 50 gibi daha zor durumlarda bu daha da önemli hale gelir." });

// =========================================================== KAPANIŞ
const SEC4 = "Kapanış";
pres.addSection({ title: SEC4 });
{
  const s = deck.content(SEC4, "Bu dersin üç çıkarımı", { dark: true,
    notes: "Özetleyelim. Bir: PINN, denklemi kayıp olarak yazarak veri olmadan çözüm üretir; katı kısıt ve doğru aktivasyon işi kolaylaştırır. " +
      "İki: başarıyı kayıp eğrisi değil referans ölçer, ve tek koşu değil birkaç tohum; daha büyük ağ ya da uzun eğitim burada hatayı tohum aralığının dışına taşımadı. Üç: bu problemde FDM daha iyi; PINN'in değeri veri ve bilinmeyenler devreye girince ortaya çıkıyor." });
  const cw = (W - 2 * M - 0.6) / 3;
  [["Fizik kayıp olur", "Laplace ve Robin artıkları kayba girer; katı kısıt Dirichlet'i yapıya gömer, tanh ikinci türevi taşır."],
   ["Kayıp ≠ doğruluk", `Köşeyi dışlamak kaybı ${Math.round(V.loss_ratio_uniform_over_skip)} kat düşürdü, hata tohum aralığında kaldı; köşeye nokta eklemek hatayı ${V.corner_vs_uniform_ratio_of_means.toFixed(1)} kat artırdı. Üç tohum, bir referans.`],
   ["Doğru araç seçimi", "Bu problemde FDM üstün. PINN'in gücü veri, bilinmeyen parametre ve parametrik çözümde."]]
    .forEach(([h, b], i) => deck.card(s, { x: M + i * (cw + 0.3), y: BODY_TOP + 0.2, w: cw, h: 2.7, head: h, body: b, num: i + 1, dark: true, headSize: 19, bodySize: 16 }));
  s.addText("Sıradaki adım: seyrek ve gürültülü ölçümleri aynı kayba eklemek (hibrit PINN).", { x: M, y: 5.4, w: W - 2 * M, h: 0.5,
    fontSize: 16, color: hex("gumus"), margin: 0, isTextBox: true, objectName: "sum_next" });
}
{
  const s = deck.content(SEC4, "Uygulama: kodu çalıştırın, sonra deneyleri düzeyinize göre yapın", { step: "UYGULAMA",
    notes: "Eğitim iki çekirdekte birkaç dakika sürüyor; deneyleri kısaltmak için Adam adım sayısını düşürebilirsiniz. Lisans öğrencileri sol sütunu, yüksek lisans öğrencileri ayrıca sağ sütunu yapsın. " +
      "Teslim: bir sayfalık not, hata haritaları ve bir tablo." });
  s.addShape(pres.shapes.RECTANGLE, { x: M, y: BODY_TOP, w: 4.5, h: 4.35, fill: { color: hex("derin") }, line: { type: "none" }, objectName: "code_bg2" });
  s.addText([
    { text: "pip install torch", options: { breakLine: true } },
    { text: "python pinn_forward.py", options: { breakLine: true } },
    { text: "python pinn_forward.py \\", options: { breakLine: true } },
    { text: "   --corner --tag corner", options: { breakLine: true } },
    { text: "python pinn_forward.py \\", options: { breakLine: true } },
    { text: "   --skip 0.02 --tag skip", options: {} },
  ], { x: M + 0.25, y: BODY_TOP + 0.25, w: 4.05, h: 3.85, fontFace: "Courier New", fontSize: 13, color: hex("krom"),
    valign: "top", margin: 0, paraSpaceAfter: 8, isTextBox: true, objectName: "code2" });
  const cx = M + 4.8, cw = (W - M - cx - 0.3) / 2;
  deck.card(s, { x: cx, y: BODY_TOP, w: cw, h: 4.35, head: "Lisans",
    body: "1. Ağ genişliği 20, 50, 100 · her biri 3 tohum: ortalama ± sapma ve süreyi tablolayın.\n2. λ = 0.1, 1, 10 ile Robin teriminin etkisini ölçün.\n3. Q′'yü PINN'den hesaplayıp seri çözümle karşılaştırın.", headSize: 18, bodySize: 14 });
  deck.card(s, { x: cx + cw + 0.3, y: BODY_TOP, w: cw, h: 4.35, head: "Yüksek lisans",
    body: "1. Yumuşak kısıt (Dirichlet kaybı) ile katı kısıtı karşılaştırın.\n2. ReLU ile eğitip kaybın neden sıfıra gittiğini gösterin.\n3. Tekilliği çözüme analitik olarak ekleyin; L₂ ve Q′ değişir mi?", headSize: 18, bodySize: 14 });
}
{
  const s = deck.content(SEC4, "Sıradaki ders: seyrek ölçümleri aynı kayba ekleyeceğiz", { step: "DERS 03 · ÖNİZLEME",
    notes: "Gelecek ders altıncı adım, hibrit PINN. FDM çözümünden birkaç noktayı gürültü ekleyerek ölçüm gibi kullanacağız ve kayba bir veri terimi ekleyeceğiz. " +
      "Soru şu: birkaç ölçüm köşedeki hatayı ne kadar düzeltir, gürültü ne kadar zarar verir? Bu, yedinci adımdaki ters problemin de hazırlığı." });
  deck.mathBox(s, ["pv_hybrid"], { x: M, y: BODY_TOP, w: W - 2 * M, h: 1.6 });
  const cw = (W - 2 * M - 0.6) / 3;
  [["Veri", "FDM çözümünden 10–20 nokta, %1 gürültü"], ["Soru", "Birkaç ölçüm köşe hatasını ne kadar düzeltir?"], ["Hazırlık", "Adım 7: aynı kurguyla Bi'yi ölçümden geri bulmak"]]
    .forEach(([h, b], i) => deck.card(s, { x: M + i * (cw + 0.3), y: 4.0, w: cw, h: 1.6, head: h, body: b, headSize: 18, bodySize: 14 }));
}
{
  const s = deck.content(SEC4, "Kaynaklar", {
    notes: "Raissi ve arkadaşlarının makalesi PINN'in temel referansı. Lagaris 1998 katı kısıt fikrinin kaynağı. Wang, Teng ve Perdikaris kayıp terimlerinin dengesizliğini inceliyor. DeepXDE makalesi uyarlamalı örnekleme RAR'ı tanıtıyor. Adam ve L-BFGS'in özgün makaleleri de listede." });
  deck.card(s, { x: M, y: BODY_TOP, w: W - 2 * M, h: 3.0, head: "Okuma listesi",
    body: "M. Raissi, P. Perdikaris, G. E. Karniadakis · Physics-informed neural networks, J. Comput. Phys. 378 (2019) 686–707\n" +
      "I. E. Lagaris, A. Likas, D. I. Fotiadis · Artificial neural networks for solving ODEs and PDEs, IEEE Trans. Neural Netw. 9 (1998) · katı kısıt\n" +
      "S. Wang, Y. Teng, P. Perdikaris · Understanding and mitigating gradient flow pathologies in PINNs, SIAM J. Sci. Comput. 43 (2021)\n" +
      "L. Lu, X. Meng, Z. Mao, G. E. Karniadakis · DeepXDE, SIAM Review 63 (2021) · uyarlamalı örnekleme (RAR)\n" +
      "D. P. Kingma, J. Ba · Adam, ICLR 2015  ·  D. C. Liu, J. Nocedal · L-BFGS, Math. Program. 45 (1989)\n" +
      "Kod: github.com/mikbalarikan/kolay-pinn · cases/01-2d-heat-conduction/pinn_forward.py", headSize: 18, bodySize: 14 });
}

const out = path.join(__dirname, "ders02_forward_pinn.pptx");
deck.write(out).then((f) => console.log(f));
