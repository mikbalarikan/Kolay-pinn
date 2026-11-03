/**
 * Ders 01 · 2D ısı iletimi: referans çözümü kurmak (Adım 1–3)
 * Önce:  python lecture/make_slide_figures.py
 * Sonra: node lecture/build_lecture.js   ->  lecture/ders01_2d_isi_iletimi_referans.pptx
 */
const fs = require("fs");
const path = require("path");
const D = require(path.join(__dirname, "..", "..", "..", "kolay_pinn", "deck", "turkisi_deck.js"));

const ASSETS = path.join(__dirname, "assets");
const S = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "data", "summary.json"), "utf8"));
const deck = D.createDeck({ course: "KOLAY PINN", lecture: "Ders 01 · 2D ısı iletimi", assets: ASSETS,
  eqDir: path.join(ASSETS, "eq"),
  title: "Kolay PINN · Ders 01 · 2D ısı iletimi: referans çözüm" });
const { pres, C, W, M, BODY_TOP, hex } = deck;
const YL = "YÜKSEK LİSANS";
const fmt = (v) => String(v).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
const cor = S.correlation, fdm = S.fdm_N101, cv = S.convergence;

const STEPS = [
  { n: 1, t: "Problemi tanımla" }, { n: 2, t: "Boyutsuzlaştır" }, { n: 3, t: "FDM referansı" },
  { n: 4, t: "Forward PINN" }, { n: 5, t: "Doğrula" }, { n: 6, t: "Hibrit PINN" },
  { n: 7, t: "Ters problem" }, { n: 8, t: "Parametrik PINN" }, { n: 9, t: "Framework" },
];

// =========================================================== GİRİŞ
pres.addSection({ title: "Giriş" });
{
  const s = pres.addSlide({ masterName: "KAPAK", sectionTitle: "Giriş" });
  deck.chip(s, "KOLAY PINN · DERS 01", M, 1.7);
  s.addText("2D ısı iletimi:\nreferans çözümü kurmak", { x: M, y: 2.2, w: 8.6, h: 2.0, fontSize: 44, bold: true,
    color: C.background2, margin: 0, valign: "top", isTextBox: true, objectName: "cover_title" });
  s.addText("Problem tanımı · boyutsuzlaştırma · sonlu farklar ve analitik doğrulama",
    { x: M, y: 4.35, w: 8.6, h: 0.9, fontSize: 18, color: hex("gumus"), margin: 0, valign: "top", isTextBox: true, objectName: "cover_sub" });
  s.addText("Lisans ve yüksek lisans · Adım 1–3 · yaklaşık 50 dakika", { x: M, y: 6.2, w: 8, h: 0.4, fontSize: 13,
    color: hex("titanyum"), margin: 0, isTextBox: true, objectName: "cover_meta" });
  s.addImage({ path: deck.A("maskot_normal.png"), x: 9.4, y: 1.6, w: 3.4, h: 3.4, objectName: "cover_mascot" });
  s.addNotes("Hoş geldiniz. Bu kurs boyunca fizik bilgili sinir ağlarını, yani PINN'leri, tek bir problem üzerinden adım adım kuracağız. " +
    "Bugünkü ders PINN'den önceki en önemli işi yapıyor: güvenilir bir referans çözüm. Bir PINN'in iyi olup olmadığını ancak doğru olduğunu bildiğimiz bir çözüme karşı söyleyebiliriz. " +
    "Problemimiz bir kare çelik plaka: üç kenarı 70 derecede tutuluyor, alt kenarı suyla soğutuluyor.");
}
{
  const s = deck.content("Giriş", "Bu dersin sonunda dört şeyi yapabileceksiniz", {
    notes: "Hedefleri baştan söylüyorum çünkü dersin her bölümü bunlardan birine hizmet ediyor. İlk üç hedef lisans düzeyinde herkes için. " +
      "Dördüncü hedefte, yani yakınsama mertebesini okumakta, yüksek lisans öğrencilerinden biraz daha fazlasını bekliyorum: neden L2 ve maksimum hatanın farklı hızlarda düştüğünü açıklayabilmek." });
  const objs = [
    ["h ve Bi'yi hesaplamak", "Konvektif sınır için h'yi korelasyondan bulup Biot sayısını fiziksel olarak yorumlamak."],
    ["Problemi boyutsuzlaştırmak", "Sıcaklık ve uzunluğu ölçekleyip problemi tek parametreye, Bi'ye indirmek."],
    ["FDM ile çözmek", "Robin koşullu Laplace denklemini hayalet düğümle ayrıklaştırıp çözmek."],
    ["Çözümü doğrulamak", "Sayısal çözümü seri çözüme karşı sınamak ve yakınsama mertebesini okumak."],
  ];
  const cw = (W - 2 * M - 0.3) / 2, ch = 2.05;
  objs.forEach(([h, b], i) => deck.card(s, { x: M + (i % 2) * (cw + 0.3), y: BODY_TOP + Math.floor(i / 2) * (ch + 0.3),
    w: cw, h: ch, head: h, body: b, num: i + 1, headSize: 18, bodySize: 15 }));
  s.addText(YL + " · 4. hedefte derinlik", { x: W - M - 3.6, y: 6.55, w: 3.6, h: 0.3, fontSize: 11, color: hex("lila"),
    bold: true, align: "right", margin: 0, isTextBox: true, objectName: "obj_yl" });
}
{
  const s = deck.content("Giriş", "PINN'e geçmeden önce güvenilir bir referans çözüm kuruyoruz", {
    notes: "Kursun yol haritası dokuz adım. Bugün ilk üçünü yapıyoruz ve sarı ile işaretli. " +
      "Neden bu kadar uğraşıyoruz? Çünkü PINN'in kaybı sıfıra yaklaşsa bile çözüm yanlış olabilir. Kayıp eğrisi doğruluğun kanıtı değildir; referansla karşılaştırma kanıttır. " +
      "Bu referans ileride hibrit PINN'de veri kaynağı, ters problemde de sentetik ölçüm olarak işimize yarayacak." });
  deck.roadmap(s, STEPS, new Set([1, 2, 3]), { y: 2.7 });
  deck.card(s, { x: M, y: 4.75, w: W - 2 * M, h: 1.35, head: "Neden önce referans?",
    body: "PINN kaybının küçük olması çözümün doğru olduğunu göstermez. Doğruluğu ancak bağımsız bir çözüme karşı ölçebiliriz; bu referans sonraki adımlarda veri kaynağı da olacak." });
}
{
  const s = deck.content("Giriş", "Bu derste altı kavrama yaslanacağız", {
    notes: "Bu slayt bir sözlük. İçeriğe girmeden önce terimleri tanıtıyorum ki sonraki slaytlarda yeni bir kelimeyle ve yeni bir fikirle aynı anda uğraşmayalım. " +
      "Laplace denklemi kaynaksız kararlı iletim. Dirichlet değeri sabitler, Robin değer ile türevi birbirine bağlar. Biot sayısı iki direncin oranı. Sonlu farklar türevleri komşu düğümlerle yaklaşıklar." });
  const terms = [
    ["Laplace denklemi", "g_laplace", "Isı kaynağı olmayan kararlı iletim"],
    ["Dirichlet koşulu", "g_dirichlet", "Sınırda sıcaklık verilir"],
    ["Robin koşulu", "g_robin", "Sınırda iletim akısı konveksiyona eşit"],
    ["Biot sayısı", "g_biot", "İletim direnci / konveksiyon direnci"],
    ["Sonlu farklar (FDM)", "g_fd", "Türev, komşu düğüm değerleriyle"],
    ["Boyutsuzlaştırma", "g_nondim", "Sıcaklık 0 ile 1 arasına ölçeklenir"],
  ];
  const cw = (W - 2 * M - 0.6) / 3, ch = 2.15;
  terms.forEach(([h, m, b], i) => deck.card(s, { x: M + (i % 3) * (cw + 0.3), y: BODY_TOP + Math.floor(i / 3) * (ch + 0.25),
    w: cw, h: ch, head: h, math: m, body: b, headSize: 17, bodySize: 14 }));
}

// =========================================================== 1 · PROBLEMİ TANIMLA
const SEC1 = "1 · Problemi tanımla";
deck.section(SEC1, "01", "Problemi tanımla", "Geometri, malzeme, sınır koşulları ve su tarafındaki h", { roadmapSteps: STEPS.slice(0, 3), active: new Set([1]),
  notes: "Birinci bölüm: fiziği netleştiriyoruz. Geometri, malzeme, sınır koşulları ve en önemlisi su tarafındaki ısı taşınım katsayısı." });
{
  const s = deck.content(SEC1, "Üç kenarı 70 °C tutulan çelik plaka alttan suyla soğutuluyor", { step: "ADIM 1 · PROBLEM",
    notes: "Plaka 10 santimetre kare, çelik. Üç kenar 70 derecede sabit; bu Dirichlet koşulu. Alt kenar boyunca 20 derecede su 1 metre bölü saniye hızla akıyor; bu Robin koşulu. " +
      "Sorumuz: plakanın içindeki kararlı sıcaklık dağılımı ve alttan çekilen ısı. Kalınlık yönünü ihmal ediyoruz; problem iki boyutlu, ısı birim derinlik başına." });
  deck.image(s, "01_schematic.png", { x: M, y: BODY_TOP, w: 5.6, h: 4.75 });
  const rows = [
    ["Büyüklük", "Değer"],
    ["Plaka boyu L", "0.1 m (kare)"],
    ["Isı iletim katsayısı k", "49 W m⁻¹ K⁻¹ (çelik)"],
    ["Duvar sıcaklığı Tw", "70 °C · üst, sol, sağ"],
    ["Akışkan", "su · 1 m/s · 20 °C"],
    ["Alt kenar", "konveksiyon, h = ?"],
  ].map((r, i) => r.map((t) => ({ text: t, options: { bold: i === 0, color: i === 0 ? "FFFFFF" : hex("derin"),
    fill: { color: i === 0 ? hex("celik_mavisi") : (i % 2 ? "FFFFFF" : hex("krom")) } } })));
  s.addTable(rows, { x: 6.7, y: BODY_TOP + 0.2, w: 6.0, colW: [2.8, 3.2], fontSize: 15, fontFace: "Arial",
    rowH: 0.55, border: { type: "solid", pt: 0.5, color: hex("gumus") }, margin: [0.04, 0.12, 0.04, 0.12], valign: "middle", objectName: "given_table" });
  deck.caption(s, "Bilinmeyen tek fiziksel büyüklük h: su tarafının ısı taşınım katsayısı.", { x: 6.7, y: 5.75, w: 6.0, h: 0.5 });
}
{
  const s = deck.content(SEC1, "Su tarafındaki h'yi laminer düz levha korelasyonu verir", { step: "ADIM 1 · h",
    notes: `Önce Reynolds sayısı: U çarpı L bölü nü, yaklaşık ${fmt(cor.Re)}. Düz levhada geçiş 5 çarpı 10 üzeri 5 civarında, yani akış laminer. ` +
      `Laminer, izotermal düz levha için ortalama Nusselt: 0.664 Re üzeri yarım, Pr üzeri üçte bir. Bu ${cor.Nu} verir. h eşittir Nu çarpı akışkanın k'sı bölü L, yaklaşık ${fmt(cor.h_W_m2K)}. ` +
      "Varsayımları açıkça söyleyelim: yüzey izotermal kabul ediliyor ama bizim alt yüzeyimiz 37 ile 70 derece arasında değişiyor. Bu yüzden sabit h bir mühendislik yaklaşımı. Verilen 2000 değeriyle fark yüzde 20; korelasyonların belirsizliği zaten bu mertebede." });
  const y = BODY_TOP + 0.1, w = 3.7, bh = 2.55, gap = (W - 2 * M - 3 * w) / 2;
  const items = [
    ["re", fmt(cor.Re), "", "laminer: Re < 5×10⁵"],
    ["nu", String(cor.Nu), "", "izotermal düz levha"],
    ["h", fmt(cor.h_W_m2K), "W m⁻² K⁻¹", "su, 20 °C: ν, k_f, Pr"],
  ];
  items.forEach(([eq, v, u, l], i) => {
    const x = M + i * (w + gap);
    s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: bh, fill: { color: hex("krom") }, line: { type: "none" }, objectName: `hchain_bg_${i}` });
    deck.math(s, eq, { x: x + 0.3, y: y + 0.25, w: w - 0.6, h: 0.75, valign: "middle", scale: 0.95 });
    s.addText([{ text: v, options: { fontSize: 36, bold: true, color: C.accent1 } },
               { text: u ? ` ${u}` : "", options: { fontSize: 16, bold: true, color: C.accent1 } }],
      { x: x + 0.3, y: y + 1.12, w: w - 0.6, h: 0.75, margin: 0, valign: "middle", isTextBox: true, objectName: `hchain_v_${i}` });
    s.addText(l, { x: x + 0.3, y: y + 1.95, w: w - 0.6, h: 0.4, fontSize: 13, color: hex("panel"), margin: 0, isTextBox: true, objectName: `hchain_l_${i}` });
    if (i < 2) s.addText("→", { x: x + w, y: y + 1.0, w: gap, h: 0.6, fontSize: 28, color: hex("titanyum"), align: "center", margin: 0, isTextBox: true, objectName: `hchain_arr_${i}` });
  });
  deck.card(s, { x: M, y: 4.95, w: W - 2 * M, h: 1.35, head: "Varsayımları bilerek kullanıyoruz",
    body: "Korelasyon izotermal yüzey ister; alt yüzeyimiz 37–70 °C arasında değişiyor. Sabit h bir yaklaşım. Verilen h = 2000 ile fark %20, korelasyon belirsizliği (±%15–20) mertebesinde." });
}
{
  const s = deck.content(SEC1, `Bi ≈ ${cor.Bi.toFixed(1)}: plakanın içinde güçlü bir sıcaklık gradyanı oluşur`, { step: "ADIM 1 · Bi",
    notes: "Biot sayısı iki direncin oranı: plaka içindeki iletim direnci L bölü k, su tarafındaki konveksiyon direnci 1 bölü h. " +
      "Grafikte alt yüzey sıcaklığını dört farklı Bi için görüyorsunuz. Bi 0.006'da, yani alüminyum ve havada, plaka neredeyse izotermal; ısı plakada kolay dolaşıyor, darboğaz su tarafında. " +
      "Bi 4.9'da, bizim durumumuzda, alt yüzeyin ortası suya doğru belirgin biçimde soğuyor. Bi 50'de yüzey neredeyse su sıcaklığına iniyor. " +
      "PINN açısından önemi: Bi büyüdükçe köşelerdeki gradyan dikleşir ve ağın öğrenmesi zorlaşır. Bu yüzden 4.9 iyi bir test durumu." });
  deck.image(s, "02_bi_regimes.png", { x: M, y: BODY_TOP, w: 7.3, h: 4.75 }, "left");
  deck.mathBox(s, ["bi_num"], { x: 8.4, y: BODY_TOP + 0.1, w: 4.33, h: 1.2, scale: 0.95 });
  deck.card(s, { x: 8.4, y: 3.55, w: 4.3, h: 2.75, head: "Okuma kuralı",
    body: "Bi < 0.1: plaka neredeyse izotermal, toplu kapasite geçerli.\nBi ≫ 1: yüzey T∞'a yaklaşır, köşelerde dik gradyan.\nBizim durum: ikisinin arası, PINN için iyi bir sınav." });
}
deck.question(SEC1, "Plaka alüminyum (k = 237 W m⁻¹ K⁻¹) olsaydı Bi kaç olurdu ve alt yüzey profili nasıl değişirdi?", {
  hint: "İpucu: yalnızca k değişiyor; h ve L aynı.",
  notes: "Cevap: Bi = 2398 × 0.1 / 237 ≈ 1.0. Gradyan zayıflar; alt yüzeyin ortası bugünkü 36.5 derece yerine daha sıcak kalır, profil Bi = 0.5 ile 4.9 eğrileri arasına düşer. " +
    "Fiziksel yorum: daha iletken plaka ısıyı yan duvarlardan merkeze daha kolay taşır." });

// =========================================================== 2 · BOYUTSUZLAŞTIR
const SEC2 = "2 · Boyutsuzlaştır";
deck.section(SEC2, "02", "Boyutsuzlaştır", "Birimlerden arındır, parametreleri tek bir sayıya indir", { roadmapSteps: STEPS.slice(0, 3), active: new Set([2]),
  notes: "İkinci bölüm: problemi birimlerinden arındırıyoruz. Bunun iki faydası var: parametre sayısı bire iner ve sinir ağı her şeyi 0 ile 1 civarında görür." });
{
  const s = deck.content(SEC2, "θ ve ξ, η ile problem tek bir parametreye, Bi'ye iner", { step: "ADIM 2 · ÖLÇEKLEME",
    notes: "Sıcaklığı duvar ile su arasındaki farkla ölçekliyoruz: theta sıfır su sıcaklığı, theta bir duvar sıcaklığı. Uzunlukları L ile bölüyoruz. " +
      "Sonuç sağda: Laplace denklemi aynı kalıyor, üç kenarda theta bir, altta Robin koşulu yalnızca Bi içeriyor. L, k, h, 70 ve 20 ayrı ayrı yok oldu; hepsi Bi'nin içinde. " +
      "Boyutlu sonuca dönmek için T eşittir 20 artı 50 theta." });
  deck.mathBox(s, ["scales"], { x: M, y: BODY_TOP, w: 4.3, h: 2.75, label: "ÖLÇEKLER", scale: 0.9 });
  deck.mathBox(s, ["nd_problem"], { x: 5.6, y: BODY_TOP, w: W - M - 5.6, h: 2.75, label: "BOYUTSUZ PROBLEM", scale: 0.95 });
  s.addText("→", { x: 4.9, y: BODY_TOP + 1.1, w: 0.7, h: 0.6, fontSize: 30, color: hex("titanyum"), align: "center", margin: 0, isTextBox: true, objectName: "nd_arrow" });
  const ty = 5.2, tw = (W - 2 * M - 0.6) / 3;
  [["v_th1", "duvar, 70 °C"], ["v_th0", "su, 20 °C"], ["v_thm", `alt orta, ${fdm.T_mid_bottom_C.toFixed(1)} °C`]].forEach(([k, l], i) => {
    const m = deck.math(s, k, { x: M + i * (tw + 0.3), y: ty, scale: 0.9 });
    s.addText(l, { x: M + i * (tw + 0.3), y: m.y + m.h + 0.12, w: tw, h: 0.35, fontSize: 13, color: hex("titanyum"), margin: 0, isTextBox: true, objectName: `nd_lbl_${i}` });
  });
}
{
  const s = deck.content(SEC2, "Robin koşulu: alt yüzeyde iletimle gelen ısı konveksiyonla gider", { step: "ADIM 2 · ROBIN",
    notes: "Robin koşulunu bir enerji dengesinden türetelim. Alt yüzeyde, dışa dönük normal eksi y yönünde. Plakadan suya doğru iletim akısı k dT/dy; bu, konveksiyonla taşınan h çarpı T eksi T sonsuz'a eşit. " +
      "İkinci adımda T ve y'yi ölçekli değişkenlerle yazıyoruz; delta T her iki taraftan sadeleşiyor. Üçüncü adımda h L bölü k kalıyor, bu da Bi. " +
      "İşarete dikkat: normalin yönünü karıştırırsanız işaret ters döner ve ısı suya gitmek yerine sudan gelir. PINN kodunda en sık yapılan hatalardan biri bu." });
  const cw = (W - 2 * M - 0.6) / 3, y = BODY_TOP + 0.1, h = 3.1;
  const steps = [
    ["Enerji dengesi, η = 0", "rob1", "iletim akısı = konveksiyon akısı", null],
    ["Ölçekli değişkenler", "rob2", null, "rob2_sub"],
    ["Sadeleştir", "rob3", "ΔT sadeleşir, tek parametre kalır", null],
  ];
  steps.forEach(([hd, e, note, noteEq], i) => {
    const x = M + i * (cw + 0.3);
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: cw, h, fill: { color: hex("krom") }, line: { type: "none" }, objectName: `rob_bg_${i}` });
    s.addText(String(i + 1), { x: x + 0.25, y: y + 0.25, w: 0.5, h: 0.5, shape: pres.shapes.OVAL, fill: { color: C.accent3 },
      color: "FFFFFF", bold: true, fontSize: 16, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `rob_n_${i}` });
    s.addText(hd, { x: x + 0.95, y: y + 0.25, w: cw - 1.2, h: 0.5, fontSize: 17, bold: true, color: C.text1, valign: "middle", margin: 0, isTextBox: true, objectName: `rob_h_${i}` });
    deck.math(s, e, { x: x + 0.25, y: y + 1.0, w: cw - 0.5, h: 1.0, valign: "middle", scale: 0.95 });
    if (note) s.addText(note, { x: x + 0.25, y: y + 2.25, w: cw - 0.5, h: 0.6, fontSize: 14, color: hex("panel"), valign: "top", margin: 0, isTextBox: true, objectName: `rob_t_${i}` });
    if (noteEq) deck.math(s, noteEq, { x: x + 0.25, y: y + 2.3, scale: 0.95 });
  });
  deck.card(s, { x: M, y: 5.45, w: W - 2 * M, h: 0.95, head: "İşaret kontrolü: ",
    body: "dışa dönük normal −y yönünde. Normali ters alırsanız ısı sudan plakaya akar; PINN kodunda en sık yapılan hata." });
}
{
  const s = deck.content(SEC2, "Boyutsuz form PINN eğitimini dengeler", { step: "ADIM 2 · NEDEN", level: YL,
    notes: "Bu slayt yüksek lisans düzeyi ama lisans öğrencilerinin de sezgisini kurmasını istiyorum. " +
      "Birinci neden: tanh gibi aktivasyonlar girdisi 1 civarında olduğunda en duyarlı. Metre ve derece cinsinden girdiler ağı ya doygunluğa ya da düz bölgeye iter. " +
      "İkinci neden: kayıp birden fazla terimden oluşuyor. Biri Kelvin bölü metre kare, diğeri Kelvin bölü metre biriminde olursa büyüklükleri onlarca kat farklı olur ve optimizer büyük terime kilitlenir. " +
      "Üçüncü neden: tek parametre Bi, sekizinci adımdaki parametrik PINN'in doğal girdisi. Bir ağ, tüm malzeme ve akış koşulları için çözüm verebilir." });
  const cw = (W - 2 * M - 0.6) / 3;
  [["Girdiler O(1)", "tanh aktivasyonları doygunluğa girmez, gradyanlar sağlıklı kalır.", "domain"],
   ["Kayıp terimleri dengeli", "PDE ve Robin artıkları aynı ölçekte; optimizer tek bir terime kilitlenmez."],
   ["Tek parametre: Bi", "Adım 8'de (ξ, η, Bi) girdili tek ağ, her malzeme ve akış koşulu için çözüm verir."]]
    .forEach(([h, b, m], i) => deck.card(s, { x: M + i * (cw + 0.3), y: BODY_TOP + 0.1, w: cw, h: 2.5, head: h, body: b, num: i + 1, headSize: 17, bodySize: 15, math: m }));
  deck.mathBox(s, ["loss_w"], { x: M, y: 4.85, w: 6.4, h: 1.3, label: "KAYIP" });
  deck.caption(s, "Boyutsuz formda terimler aynı ölçekte olduğu için λ ≈ 1 ile başlamak makul; boyutlu formda λ'yı elle onlarca kat ayarlamak gerekir.",
    { x: M + 6.7, y: 5.0, w: W - 2 * M - 6.7, h: 1.1 });
}
deck.question(SEC2, "Boyutlu problemde kaç bağımsız parametre vardı, boyutsuzda kaç tane kaldı?", {
  hint: "İpucu: L, k, h, Tw ve T∞'ı sayın; sonra boyutsuz denklemlere bakın.",
  notes: "Boyutlu: L, k, h, Tw, T∞, yani beş parametre. Boyutsuz: yalnızca Bi. Buckingham Pi bakış açısıyla, sıcaklık ölçeği ve uzunluk ölçeği iki boyut kullanıyor ve geriye tek bağımsız grup kalıyor. " +
    "Bu, parametrik bir çalışmada beş boyutlu bir uzay yerine tek bir eksen taramak demek." });

// =========================================================== 3 · FDM VE DOĞRULAMA
const SEC3 = "3 · FDM ve doğrulama";
deck.section(SEC3, "03", "FDM referansı ve doğrulama", "Ayrıklaştır, çöz, analitik seri çözüme karşı sına", { roadmapSteps: STEPS.slice(0, 3), active: new Set([3]),
  notes: "Üçüncü bölüm: problemi sonlu farklarla çözüyoruz ve çözümün doğruluğunu analitik seri çözüme karşı ölçüyoruz." });
{
  const s = deck.content(SEC3, "Beş noktalı şablon Laplace denklemini ikinci mertebe doğrulukla ayrıklaştırır", { step: "ADIM 3 · ŞABLON",
    notes: "Solda iç düğüm. İkinci türevleri merkezi farkla yazınca, Delta kare ile çarptıktan sonra, dört komşunun toplamı eksi dört kere merkez sıfıra eşit. Kesme hatası Delta kare mertebesinde. " +
      "Sağda alt kenar. Yüzey düğümü i, 0 bir bilinmeyen; ama altında komşu yok. Plakanın dışında, suyun içinde, hayali bir düğüm tanımlıyoruz: i, eksi 1. " +
      "Robin koşulunu merkezi farkla yazınca hayalet düğümün değerini içerideki i, 1 cinsinden buluyoruz. Bunu şablona koyunca hayalet düğüm kayboluyor ve yüzey için tek bir denklem kalıyor. " +
      "Alt köşeler yan duvarlara ait; orada theta bir." });
  const img = deck.image(s, "03_stencil_ghost.png", { x: M, y: BODY_TOP - 0.15, w: W - 2 * M, h: 3.2 });
  const half = (W - 2 * M - 0.3) / 2, ey = 5.15;
  deck.mathBox(s, ["st_in"], { x: M, y: ey, w: half, h: 1.35, label: "İÇ DÜĞÜM", scale: 0.95 });
  deck.mathBox(s, ["st_ghost", "st_bot"], { x: M + half + 0.3, y: ey, w: half, h: 1.35, label: "ALT KENAR · HAYALET DÜĞÜM YOK EDİLİR", scale: 0.9, gap: 0.08 });
}
{
  const s = deck.content(SEC3, "Seri çözüm, FDM'yi ondan bağımsız bir yolla sınamamızı sağlar", { step: "ADIM 3 · ANALİTİK", level: YL,
    notes: "Değişkenlere ayırma. Theta'yı bir eksi phi olarak yazıyoruz; böylece phi yan duvarlarda ve üstte sıfır olur. Sinüs serisi yan duvarları, sinh terimi üst kenarı otomatik sağlıyor. " +
      "Geriye alt kenardaki Robin koşulu kalıyor; o da her modun katsayısı A n'yi belirliyor. Yalnızca tek n'ler var çünkü sabit bir fonksiyonun sinüs serisinde çift terimler sıfır. " +
      "Pratik not: cosh n pi büyük n'de taşar. Kodda oranı üstel fonksiyonlarla, taşmayacak biçimde yazdık. 4000 terim kullandık; alt köşelerde seri yavaş yakınsar." });
  deck.mathBox(s, ["series", "an"], { x: M, y: BODY_TOP, w: W - 2 * M, h: 2.25, gap: 0.25, scale: 0.92 });
  const cw = (W - 2 * M - 0.6) / 3;
  [["Homojenleştir", "phi", "φ yan duvarlarda ve üstte sıfır; sinüs serisi bunu sağlar.", 1],
   ["Robin katsayıları verir", "an_rob", "Yalnız tek n'ler kalır.", 1],
   ["Taşmasız hesap", "ratio", "4000 terim; köşelerde yavaş yakınsama.", 0.72]]
    .forEach(([h, m, b, sc], i) => deck.card(s, { x: M + i * (cw + 0.3), y: 4.45, w: cw, h: 2.0, head: h, math: m, mathScale: sc, body: b, headSize: 17, bodySize: 14 }));
}
{
  const s = deck.content(SEC3, `Plakanın en soğuk noktası alt yüzeyin ortası: ${fdm.T_mid_bottom_C.toFixed(1)} °C`, { step: "ADIM 3 · SONUÇ",
    notes: `Sıcaklık alanı. Üst bölge neredeyse 70 derece; ısı yan duvarlardan ve üstten gelip alt yüzeyden suya gidiyor. İzotermler alta doğru kubbe şeklinde. ` +
      `En soğuk nokta alt yüzeyin ortası, ${fdm.T_mid_bottom_C.toFixed(1)} derece. Su sıcaklığı 20 derece olduğu halde yüzey 36.5'e iniyor: aradaki fark konveksiyon direncinin payı. ` +
      `Mühendislik sonucu: alttan çekilen ısı, birim derinlik başına yaklaşık ${(fdm.Q_per_depth_W_m / 1000).toFixed(1)} kilovat bölü metre.` });
  deck.image(s, "04_field.png", { x: M, y: BODY_TOP - 0.1, w: 6.2, h: 4.85 }, "left");
  const x0 = 7.4, sw = W - M - x0;
  deck.stat(s, { x: x0, y: BODY_TOP, w: sw, value: fdm.T_mid_bottom_C.toFixed(1), unit: "°C", label: "en düşük sıcaklık, alt yüzey ortası" });
  deck.stat(s, { x: x0, y: BODY_TOP + 1.45, w: sw, value: (fdm.Q_per_depth_W_m / 1000).toFixed(2), unit: "kW/m", label: "alttan çekilen ısı Q′, birim derinlik" });
  deck.stat(s, { x: x0, y: BODY_TOP + 2.9, w: sw, value: fdm.int_theta_bottom.toFixed(3), unit: "", label: "boyutsuz alt yüzey integrali", color: C.accent3 });
  deck.math(s, "qprime", { x: x0, y: BODY_TOP + 3.95, scale: 1 });
}
{
  const s = deck.content(SEC3, "FDM ve seri çözüm alt yüzeyde üst üste düşer", { step: "ADIM 3 · DOĞRULAMA",
    notes: "En kritik yüzey, yani soğutulan alt yüzey üzerinde iki çözümü karşılaştırıyoruz. Çizgi FDM, halkalar seri çözüm. Gözle ayırt edilemiyorlar. " +
      `Sayısal olarak bağıl L2 hatası ${deck.sci(fdm.rel_L2)}. Ama göz ve tek bir sayı yetmez; hatanın nerede toplandığına bakmamız gerekiyor. Bir sonraki slayt bunu gösteriyor.` });
  deck.image(s, "05_bottom_profile.png", { x: M, y: BODY_TOP - 0.1, w: 8.6, h: 4.8 }, "left");
  deck.stat(s, { x: 9.6, y: BODY_TOP + 0.3, w: 3.2, value: deck.sci(fdm.rel_L2), unit: "", label: "bağıl L₂ hata, N = 101" });
  deck.stat(s, { x: 9.6, y: BODY_TOP + 1.9, w: 3.2, value: deck.sci(fdm.max_err), unit: "", label: "maksimum |hata|", color: C.accent2 });
  deck.caption(s, "Tek bir hata sayısı yetmez: hatanın nerede toplandığına bakmalıyız.", { x: 9.6, y: BODY_TOP + 3.4, w: 3.2, h: 1.0 });
}
{
  const s = deck.content(SEC3, "Hata alt köşelerde toplanır, çünkü orada iki sınır koşulu çatışır", { step: "ADIM 3 · HATA HARİTASI",
    notes: "Hatanın logaritmasının haritası. Koyu bölgeler büyük hata. Turuncu halkalar alt köşeler. Hata orada 10 üzeri eksi 2 ile 3 mertebesinde, plakanın geri kalanında 10 üzeri eksi 5 ile 7. " +
      "Neden? Köşede yan duvar theta bir istiyor; alt kenar ise soğumak istiyor. İki koşul köşede uyumsuz ve sıcaklık gradyanı orada logaritmik olarak ıraksıyor. Hiçbir sabit ağ bu tekilliği tam çözemez. " +
      "Ortadaki açık bant ayrı bir şey: hatanın işaret değiştirdiği yer, yani orada hata gerçekten sıfırdan geçiyor. " +
      "PINN için çıkarım: kolokasyon noktalarını köşelerde sıklaştırmak ve toplam kayıp yerine bu haritaya bakmak." });
  deck.image(s, "06_error_map.png", { x: M, y: BODY_TOP - 0.1, w: 6.2, h: 4.85 }, "left");
  deck.card(s, { x: 7.4, y: BODY_TOP, w: W - M - 7.4, h: 1.9, head: "Fizik: köşe tekilliği",
    body: "Yan duvar θ = 1 ister, alt kenar soğur. Köşede ∂θ/∂ξ logaritmik ıraksar; ağ ne kadar sıklaşsa da hata orada kalır." });
  deck.card(s, { x: 7.4, y: BODY_TOP + 2.15, w: W - M - 7.4, h: 1.9, head: "PINN için anlamı",
    body: "Kolokasyon noktalarını köşelerde sıklaştır; başarıyı toplam kayıpla değil, bu haritayla ve alt yüzey ısı akısıyla ölç." });
  deck.caption(s, "Ortadaki açık bant: hatanın işaret değiştirdiği yer, gerçek bir sıfır.", { x: 7.4, y: BODY_TOP + 4.3, w: W - M - 7.4, h: 0.5 });
}
{
  const s = deck.content(SEC3, "L₂ hatası ikinci mertebeyle, maksimum hata yalnızca birinci mertebeyle düşer", { step: "ADIM 3 · YAKINSAMA", level: YL,
    notes: `Ağı dört kez sıklaştırdık: 26, 51, 101, 201 düğüm. Log-log grafikte eğim yakınsama mertebesini veriyor. L2 hatası için eğim ${cv.order_L2}, ikiye yakın; şablonun teorik mertebesi. ` +
      `Maksimum hata için eğim ${cv.order_max}, yani birinci mertebe. Neden? Maksimum hata köşede ve köşede çözüm düzgün değil; Taylor açılımının varsayımı orada bozuluyor. L2 ise alan üzerinden ortalandığı için köşenin küçük alanından az etkileniyor. ` +
      "Yüksek lisans için ödev: Richardson ekstrapolasyonu ile Q'nün ağdan bağımsız değerini tahmin edin ve köşe yerel mertebesini ölçün." });
  deck.image(s, "07_convergence.png", { x: M, y: BODY_TOP - 0.1, w: 7.0, h: 4.85 }, "left");
  const rows = [["N", "bağıl L₂", "maks. |hata|"]].concat(cv.N.map((n, i) => [String(n), deck.sci(cv.rel_L2[i], 2), deck.sci(cv.max_err[i], 2)]))
    .concat([["eğim p", String(cv.order_L2), String(cv.order_max)]]);
  const tr = rows.map((r, i) => r.map((t) => ({ text: t, options: { bold: i === 0 || i === rows.length - 1,
    color: i === 0 ? "FFFFFF" : hex("derin"), fill: { color: i === 0 ? hex("celik_mavisi") : (i === rows.length - 1 ? hex("krom") : "FFFFFF") } } })));
  s.addTable(tr, { x: 8.2, y: BODY_TOP + 0.1, w: 4.5, colW: [1.1, 1.7, 1.7], fontSize: 14, fontFace: "Arial", rowH: 0.48,
    border: { type: "solid", pt: 0.5, color: hex("gumus") }, margin: [0.04, 0.1, 0.04, 0.1], valign: "middle", align: "center", objectName: "conv_table" });
  deck.caption(s, "Maksimum hata köşede; çözüm orada düzgün olmadığı için Taylor kesme hatası varsayımı bozulur.", { x: 8.2, y: 5.25, w: 4.5, h: 1.0 });
}
deck.question(SEC3, "N'yi 101'den 201'e çıkarırsak maksimum hata yaklaşık kaç kat azalır? L₂ hatası neden daha hızlı düşer?", {
  hint: "İpucu: Δ yarıya iner; iki eğimi kullanın.",
  notes: "Maksimum hata yaklaşık 2 kat azalır, çünkü birinci mertebe: 4.8e-3'ten 2.5e-3'e. L2 hatası yaklaşık 3.5 kat azalır, ikinci mertebeye yakın. " +
    "Fark köşe tekilliğinden geliyor; L2 alan ortalaması olduğu için köşenin küçük alanı L2'ye az katkı yapar." });

// =========================================================== KAPANIŞ
const SEC4 = "Kapanış";
pres.addSection({ title: SEC4 });
{
  const s = deck.content(SEC4, "Bu dersin üç çıkarımı", { dark: true,
    notes: "Özetleyelim. Bir: tek parametre Bi, fiziğin tamamını taşıyor. İki: referans çözümü kurduk ve bağımsız bir yolla doğruladık. Üç: zorluk köşelerde; PINN'i değerlendirirken oraya bakacağız." });
  const cw = (W - 2 * M - 0.6) / 3;
  [["Bi her şeyi taşır", `Boyutsuzlaştırma beş parametreyi tek sayıya indirdi: Bi ≈ ${cor.Bi.toFixed(1)}, güçlü gradyan.`],
   ["Referans doğrulandı", `FDM seri çözümle örtüşüyor: bağıl L₂ ${deck.sci(fdm.rel_L2)}, alt orta ${fdm.T_mid_bottom_C.toFixed(1)} °C.`],
   ["Zorluk köşelerde", "Tekillik maksimum hatayı birinci mertebede tutar; PINN'i orada ve ısı akısında sınayacağız."]]
    .forEach(([h, b], i) => deck.card(s, { x: M + i * (cw + 0.3), y: BODY_TOP + 0.2, w: cw, h: 2.7, head: h, body: b, num: i + 1, dark: true, headSize: 19, bodySize: 16 }));
  s.addText("Sıradaki adım: aynı problemi bir PINN ile çözmek ve bu referansla karşılaştırmak.", { x: M, y: 5.4, w: W - 2 * M, h: 0.5,
    fontSize: 16, color: hex("gumus"), margin: 0, isTextBox: true, objectName: "sum_next" });
}
{
  const s = deck.content(SEC4, "Uygulama: kodu çalıştırın, sonra soruları düzeyinize göre yanıtlayın", { step: "UYGULAMA",
    notes: "Kodu repodan klonlayın ve üç komutu çalıştırın. Lisans öğrencileri sol sütundaki üç görevi, yüksek lisans öğrencileri ayrıca sağ sütundakileri yapsın. " +
      "Teslim: bir sayfalık not ve ürettiğiniz grafikler." });
  s.addShape(pres.shapes.RECTANGLE, { x: M, y: BODY_TOP, w: 4.3, h: 4.35, fill: { color: hex("derin") }, line: { type: "none" }, objectName: "code_bg" });
  s.addText([
    { text: "cd cases/01-2d-heat-conduction", options: { breakLine: true } },
    { text: "pip install -r requirements.txt", options: { breakLine: true } },
    { text: "python fdm_solver.py", options: { breakLine: true } },
    { text: "python fdm_solver.py --Bi 4.08", options: { breakLine: true } },
    { text: "python plot_reference.py", options: {} },
  ], { x: M + 0.25, y: BODY_TOP + 0.25, w: 3.85, h: 3.85, fontFace: "Courier New", fontSize: 13, color: hex("krom"),
    valign: "top", margin: 0, paraSpaceAfter: 10, isTextBox: true, objectName: "code" });
  const cx = M + 4.6, cw = (W - M - cx - 0.3) / 2;
  deck.card(s, { x: cx, y: BODY_TOP, w: cw, h: 4.35, head: "Lisans",
    body: "1. h = 2000 (Bi = 4.08) ile çözün; alt orta sıcaklığı karşılaştırın.\n2. Alüminyum–hava için Bi'yi hesaplayın, alt yüzey profilini çizin.\n3. Q′'yü yamuk kuralıyla elle doğrulayın.", headSize: 18, bodySize: 14 });
  deck.card(s, { x: cx + cw + 0.3, y: BODY_TOP, w: cw, h: 4.35, head: "Yüksek lisans",
    body: "1. Richardson ekstrapolasyonu ile ağdan bağımsız Q′ tahmini.\n2. Köşe tekilliğinin yerel mertebesini log-log ile ölçün.\n3. Film sıcaklığı (35 °C) özellikleriyle Bi duyarlılığını tartışın.", headSize: 18, bodySize: 14 });
}
{
  const s = deck.content(SEC4, "Sıradaki ders: aynı problemi veri kullanmadan bir sinir ağıyla çözeceğiz", { step: "DERS 02 · ÖNİZLEME",
    notes: "Gelecek ders dördüncü adım. Girdi xi ve eta, çıktı theta olan küçük bir ağ kuracağız. Üç Dirichlet kenarını ağın yapısına gömeceğiz, böylece kayıpta yalnızca PDE ve Robin artıkları kalacak. " +
      "Türevleri otomatik türevle alacağız. Eğitimden sonra bugün kurduğumuz referansla, özellikle köşelerde ve alt yüzey ısı akısında karşılaştıracağız." });
  const y = BODY_TOP + 0.3, bh = 1.45;
  const boxes = [
    { m: "pv_in", l: "girdi", w: 1.6 },
    { t: "MLP · tanh", l: "4–5 katman × 50 nöron", w: 2.2 },
    { m: "pv_hard", l: "Dirichlet kenarları gömülü", w: 3.95, sc: 0.92 },
    { m: "pv_loss", l: "kayıp: PDE + Robin artığı", w: 3.55, sc: 0.92, fill: "plan" },
  ];
  const gap = (W - 2 * M - boxes.reduce((a, b) => a + b.w, 0)) / 3;
  let x = M;
  boxes.forEach((b, i) => {
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: b.w, h: bh, fill: { color: hex("krom") },
      line: b.fill ? { color: hex(b.fill), width: 2.5 } : { type: "none" }, objectName: `pinn_box_${i}` });
    if (b.m) deck.math(s, b.m, { x, y, w: b.w, h: bh, align: "center", valign: "middle", scale: b.sc || 1 });
    else s.addText(b.t, { x, y, w: b.w, h: bh, fontSize: 18, bold: true, color: C.text1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `pinn_t_${i}` });
    s.addText(b.l, { x, y: y + bh + 0.12, w: b.w, h: 0.4, fontSize: 13, color: hex("titanyum"), align: "center", margin: 0, isTextBox: true, objectName: `pinn_lbl_${i}` });
    if (i < 3) s.addText("→", { x: x + b.w, y: y + 0.42, w: gap, h: 0.6, fontSize: 24, color: hex("titanyum"), align: "center", margin: 0, isTextBox: true, objectName: `pinn_arr_${i}` });
    x += b.w + gap;
  });
  deck.card(s, { x: M, y: 4.75, w: W - 2 * M, h: 1.2, head: "Başarı ölçütü bugünkü referans",
    body: "Bağıl L₂ hata, köşe hata haritası ve alt yüzey ısı akısı Q′; kayıp eğrisi tek başına yeterli değil." });
}
{
  const s = deck.content(SEC4, "Kaynaklar ve ders tekniği", {
    notes: "Isı transferi kısmı için Incropera'nın kitabı, sonlu farklar için LeVeque, PINN için Raissi ve arkadaşlarının 2019 makalesi. " +
      "Slaytların yapısı iki araştırma çizgisine dayanıyor: Penn State'te Alley ve ekibinin iddia-kanıt yaklaşımı ve Mayer'in çoklu ortam öğrenme ilkeleri." });
  deck.card(s, { x: M, y: BODY_TOP, w: 6.0, h: 3.6, head: "Konu",
    body: "Bergman, Lavine, Incropera, DeWitt · Fundamentals of Heat and Mass Transfer, 7. baskı (Wiley) · düz levha korelasyonu, su özellikleri\n" +
      "R. J. LeVeque · Finite Difference Methods for ODEs and PDEs (SIAM, 2007)\n" +
      "M. Raissi, P. Perdikaris, G. E. Karniadakis · Physics-informed neural networks, J. Comput. Phys. 378 (2019)\n" +
      "Kod: github.com/mikbalarikan/kolay-pinn", headSize: 18, bodySize: 14 });
  deck.card(s, { x: M + 6.3, y: BODY_TOP, w: W - 2 * M - 6.3, h: 3.6, head: "Ders tekniği",
    body: "İddia-kanıt slaytları: tam cümle başlık + görsel kanıt (Garner ve ark., 2013; writing.engr.psu.edu)\n" +
      "Mayer'in çoklu ortam ilkeleri: bölümlere ayırma, ön eğitim, sinyal, fazlalıktan kaçınma\n" +
      "Yapı örneği: ETH Zürih AISE / DLSC dersleri", headSize: 18, bodySize: 14 });
}

const out = path.join(__dirname, "ders01_2d_isi_iletimi_referans.pptx");
deck.write(out).then((f) => console.log(f));
