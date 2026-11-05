/**
 * Ders 04 · Ters problem: Bi'yi iç sıcaklıklardan geri bulmak (Adım 7)
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
  eqDir: path.join(ASSETS, "eq"), title: "Kolay PINN · Ders 04 · Ters problem: Bi'yi iç sıcaklıklardan geri bulmak" });
const { pres, C, W, M, BODY_TOP, hex } = deck;
const YL = "YÜKSEK LİSANS";
const BI = S.Bi_true, G = S.groups, NZ = S.noise, V = S.verdict, B10 = S.start_bi10;
const p1 = (v) => `%${(100 * v).toFixed(1)}`;
const p2 = (v) => `%${(100 * v).toFixed(2)}`;
const f3 = (v) => v.toFixed(3);
const g = (k) => G[k];
const base = g("temel 20 düzgün"), nosk = g("köşe dışlama yok"), top = g("üst yarı"), bot = g("alt şerit");
const n5 = g("5 sensör"), n80 = g("80 sensör"), mu1 = g("μ = 1");
const bis = (grp) => grp.runs.map((r) => r.Bi_hat.toFixed(2)).join(" · ");
const lss = (grp) => grp.runs.map((r) => r.fdm_ls_Bi.toFixed(2)).join(" · ");
const SENS = CL.sensitivity;
const tPINN = Math.round(V.pinn_time_s_median), tLS = V.fdm_ls_time_s_median;

const STEPS = [
  { n: 1, t: "Problemi tanımla" }, { n: 2, t: "Boyutsuzlaştır" }, { n: 3, t: "FDM referansı" },
  { n: 4, t: "Forward PINN" }, { n: 5, t: "Doğrula" }, { n: 6, t: "Hibrit PINN" },
  { n: 7, t: "Ters problem" }, { n: 8, t: "Parametrik PINN" }, { n: 9, t: "Framework" },
];
const LOCAL = ["Bi'yi parametre yap", "Ne kadar bilgi var?", "Tuzaklar ve maliyet"].map((t, i) => ({ n: i + 1, t }));

// =========================================================== GİRİŞ
pres.addSection({ title: "Giriş" });
{
  const s = pres.addSlide({ masterName: "KAPAK", sectionTitle: "Giriş" });
  deck.chip(s, "KOLAY PINN · DERS 04", M, 1.7);
  s.addText("Ters problem:\nBi'yi iç sıcaklıklardan\ngeri bulmak", { x: M, y: 2.1, w: 8.6, h: 2.4, fontSize: 40, bold: true,
    color: C.background2, margin: 0, valign: "top", isTextBox: true, objectName: "cover_title" });
  s.addText("Bi'yi öğrenilen parametre yapmak · duyarlılık ve Cramér–Rao sınırı · köşe yanlılığı · klasik yöntemle karşılaştırma",
    { x: M, y: 4.65, w: 8.6, h: 0.9, fontSize: 17, color: hex("gumus"), margin: 0, valign: "top", isTextBox: true, objectName: "cover_sub" });
  s.addText("Lisans ve yüksek lisans · Adım 7 · yaklaşık 50 dakika", { x: M, y: 6.2, w: 8, h: 0.4, fontSize: 13,
    color: hex("titanyum"), margin: 0, isTextBox: true, objectName: "cover_meta" });
  s.addImage({ path: deck.A("maskot_mutlu.png"), x: 9.4, y: 1.6, w: 3.4, h: 3.4, objectName: "cover_mascot" });
  s.addNotes("Geçen ders şunu gördük: kayıptaki Biot sayısı yanlışsa ölçümler hatayı ancak iki kat düşürebiliyor, çünkü yanlış Robin terimi ile veri birbiriyle çekişiyor. " +
    "Bugün çekişmeyi kaldırıyoruz: Bi'yi sabit değil, öğrenilecek bir sayı yapıyoruz. Ağ ağırlıklarıyla birlikte, plakanın içindeki birkaç gürültülü sıcaklık ölçümünden Bi'yi geri buluyoruz. " +
    "Bu, ısı transferinde gerçek bir mühendislik problemi: taşınım katsayısını doğrudan ölçemezsiniz, ama gövdeye termokupl koyabilirsiniz.");
}
{
  const s = deck.content("Giriş", "Bu dersin sonunda dört şeyi yapabileceksiniz", {
    notes: "Birinci hedef kod: bir fiziksel parametreyi torch parametresi yapıp pozitif kalmasını garanti etmek. " +
      "İkincisi en önemli olanı: deney yapmadan, ölçümlerin Bi hakkında ne kadar bilgi taşıdığını hesaplamak. Duyarlılık ve Cramér–Rao sınırı. " +
      "Üçüncüsü bu probleme özgü bir tuzak: köşe çelişkisinin Bi tahminini yanlı yapması. Dördüncüsü dürüstlük: PINN'i aynı verilerle klasik bir yöntemle karşılaştırmak." });
  const objs = [
    ["Bi'yi öğrenilen parametre yapmak", "Bi = eˢ ile pozitifliği garanti etmek; s için ayrı öğrenme oranı seçmek."],
    ["Bilgiyi önceden hesaplamak", "Duyarlılık ∂θ/∂Bi ve Cramér–Rao sınırıyla sensör yerleşimini değerlendirmek."],
    ["Yanlılığı tanımak", "Köşe çelişkisinin Bi'yi aşağı çektiğini görmek ve gidermek."],
    ["Klasik yöntemle karşılaştırmak", "Aynı sensörlerle FDM + en küçük kareler: doğruluk ve maliyet."],
  ];
  const cw = (W - 2 * M - 0.3) / 2, ch = 2.05;
  objs.forEach(([h, b], i) => deck.card(s, { x: M + (i % 2) * (cw + 0.3), y: BODY_TOP + Math.floor(i / 2) * (ch + 0.3),
    w: cw, h: ch, head: h, body: b, num: i + 1, headSize: 18, bodySize: 15 }));
}
{
  const s = deck.content("Giriş", "Bugün bilinmeyen sayı Bi; ölçümler Ders 03 ile aynı sanal sensörler", {
    notes: "Yol haritasında yedinci adımdayız. Ders 03'ten sensör üretecini aynen alıyoruz: FDM N 201 iç düğümleri, sigma 0.01 yani yarım derece gürültü. " +
      `Gerçek Bi ${f3(BI)}; eğitim Bi sıfır = 1'den, yani yaklaşık beş kat yanlış bir tahminden başlıyor. ` +
      "Ağ, kolokasyon ve eğitim takvimi Ders 02 ile aynı. Tek fark: kayıptaki Bi artık bir parametre." });
  deck.roadmap(s, STEPS, new Set([7]), { y: 2.6 });
  deck.card(s, { x: M, y: 4.6, w: 5.9, h: 1.6, head: "Ders 03'ten gelen soru",
    body: "Yanlış Bi ile veri hatayı yalnız 2 kat düşürdü. Bi'yi öğrenirsek çekişme kalkar mı?" });
  deck.card(s, { x: M + 6.2, y: 4.6, w: W - 2 * M - 6.2, h: 1.6, head: "Temel ayar",
    body: `Bi₀ = 1 · 20 düzgün sensör · σ = 0.01 (0.5 °C) · μ = 100 · gerçek Bi = ${f3(BI)}` });
}
{
  const s = deck.content("Giriş", "Bu derste altı kavrama yaslanacağız", {
    notes: "Sözlük. Logaritmik parametre: Bi eksi olamaz, o yüzden s'yi öğrenip Bi'yi e üzeri s yapıyoruz. " +
      "Duyarlılık: Bi biraz değişince her noktadaki sıcaklık ne kadar değişir. Sıfıra yakınsa o noktadaki ölçüm Bi'yi görmez; tanımlanabilirlik bu. " +
      "Cramér–Rao sınırı: hiçbir yansız tahmincinin bu gürültüyle bu sensörlerden daha iyisini yapamayacağı alt sınır. " +
      "Klasik taban: FDM çözücüyü bir en küçük kareler döngüsüne koymak. Köşe artığı: köşede Robin artığının eksi Bi olması; üçüncü bölümün konusu." });
  const terms = [
    ["Logaritmik parametre", "g_param", "Bi her zaman pozitif", 1],
    ["Duyarlılık", "g_sens", "Bi değişince θ ne kadar değişir", 1],
    ["Tanımlanabilirlik", "g_ident", "Ölçüm, S büyük olan yerde", 0.85],
    ["Cramér–Rao sınırı", "g_crb", "Gürültünün izin verdiği en iyi", 1],
    ["Klasik taban", "g_ls", "FDM + en küçük kareler", 0.8],
    ["Köşe artığı", "g_corner", "Robin köşede Bi'yi aşağı iter", 1],
  ];
  const cw = (W - 2 * M - 0.6) / 3, ch = 2.15;
  terms.forEach(([h, m, b, sc], i) => deck.card(s, { x: M + (i % 3) * (cw + 0.3), y: BODY_TOP + Math.floor(i / 3) * (ch + 0.25),
    w: cw, h: ch, head: h, math: m, mathScale: sc, body: b, headSize: 17, bodySize: 14 }));
}

// =========================================================== 1 · Bi'Yİ PARAMETRE YAP
const SEC1 = "1 · Bi'yi parametre yap";
deck.section(SEC1, "01", "Bi'yi parametre yap", "Kayıp, parametreleme ve öğrenme oranı",
  { roadmapSteps: LOCAL, active: new Set([1]), notes: "Birinci bölüm: Bi'yi kayba nasıl soktuğumuz ve eğitim boyunca nasıl hareket ettiği." });
{
  const s = deck.content(SEC1, "Ters kayıp Ders 03 ile aynı; tek fark Robin terimindeki Bi'nin öğrenilmesi", { step: "ADIM 7 · KAYIP",
    notes: "Kayıp terim terim Ders 03 ile aynı: Laplace artığı, Robin artığı, veri terimi. Değişen tek şey Robin teriminde sabit Bi yerine e üzeri s. " +
      "Neden logaritma? Bi negatif olursa Robin koşulu fiziksel anlamını kaybeder, ısı soğuk sudan plakaya akıyormuş gibi olur. e üzeri s her s için pozitif. " +
      "İkinci kazanç: s üzerindeki gradyan Bi çarpı Bi üzerindeki gradyan. Adım göreli oluyor: Bi 1'de de 10'da da benzer yüzdelik adımlar atıyoruz. " +
      "Kodda s bir torch Parameter; Adam'a ayrı bir parametre grubu olarak, ağdan on kat büyük öğrenme oranıyla veriyoruz. L-BFGS'de ağ ağırlıklarıyla birlikte tek vektör." });
  deck.mathBox(s, ["inverse"], { x: M, y: BODY_TOP, w: W - 2 * M, h: 1.55 });
  deck.mathBox(s, ["grad_s"], { x: M, y: BODY_TOP + 1.8, w: 7.6, h: 1.25, scale: 0.9 });
  s.addShape(pres.shapes.RECTANGLE, { x: M + 7.9, y: BODY_TOP + 1.8, w: W - 2 * M - 7.9, h: 2.5, fill: { color: hex("derin") }, line: { type: "none" }, objectName: "code_bg1" });
  s.addText([
    { text: "s = nn.Parameter(log(bi0))", options: { breakLine: true } },
    { text: "Bi = s.exp()", options: { breakLine: true } },
    { text: "Adam([{params: ağ},", options: { breakLine: true } },
    { text: "      {params: [s], lr: 1e-2}],", options: { breakLine: true } },
    { text: "     lr=1e-3)", options: {} },
  ], { x: M + 8.1, y: BODY_TOP + 1.95, w: W - 2 * M - 8.3, h: 2.2, fontFace: "Courier New", fontSize: 12.5, color: hex("krom"),
    valign: "top", margin: 0, paraSpaceAfter: 6, isTextBox: true, objectName: "code1" });
  deck.caption(s, "Ağ, katı kısıt, 4096 + 256 Sobol noktası ve Adam 6000 + L-BFGS ≤ 2000 aynen Ders 02. Köşeden δ = 0.02 içindeki Robin noktaları dışlanır (bölüm 3).",
    { x: M, y: BODY_TOP + 3.3, w: 7.6, h: 1.0 });
}
{
  const s = deck.content(SEC1, "Bi Adam'da yavaşça yükselir, son yaklaşmayı L-BFGS yapar; Bi₀ = 10'dan da aynı değere iner", { step: "ADIM 7 · EĞİTİM",
    notes: "Eğitim boyunca Bi tahmini. Mavi çizgiler temel ayar, üç tohum. İlk yüz adımda Bi biraz düşüyor: ağ henüz rastgele ve Robin terimi her şeyi küçük Bi'ye itiyor. " +
      "Ağ fiziği öğrendikçe ölçümler devreye giriyor ve Bi yükselmeye başlıyor. Adam'ın sonunda yaklaşık 4'te, L-BFGS'nin ilk birkaç yüz adımında gerçek değere oturuyor. " +
      (B10 ? `Bi sıfır = 10'dan, yani iki kat yukarıdan başlayınca da ${B10.Bi_hat.toFixed(3)}'e iniyor; aynı tohumun Bi sıfır = 1 sonucu ${B10.same_as_bi0_1_seed0.toFixed(3)}. Başlangıç noktası sonucu belirlemiyor. ` : "") +
      (mu1 ? `Yeşil, mu = 1: veri terimi zayıf, Bi ${bis(mu1)} oluyor. Ders 03'teki ölçek kuralı burada da geçerli. ` : "") +
      "Pratik ders: ters PINN'de Adam tek başına yetmiyor; ikinci dereceye yakın bir optimizer parametreyi kilitliyor." });
  deck.image(s, "02_trajectory.png", { x: M, y: BODY_TOP - 0.1, w: 8.2, h: 4.5 }, "left");
  const x0 = 9.2, sw = W - M - x0;
  deck.stat(s, { x: x0, y: BODY_TOP, w: sw, value: bis(base), unit: "", label: "temel, 3 tohum · Bi tahmini", valueSize: 22 });
  if (B10) deck.stat(s, { x: x0, y: BODY_TOP + 1.5, w: sw, value: B10.Bi_hat.toFixed(2), unit: "", label: "Bi₀ = 10'dan (tohum 0)", color: hex("celik_mavisi") });
  if (mu1) deck.stat(s, { x: x0, y: BODY_TOP + 3.0, w: sw, value: bis(mu1), unit: "", label: "μ = 1 · 3 tohum", color: hex("gecti"), valueSize: 22 });
}
deck.question(SEC1, "Bi'yi doğrudan (log'suz) öğrenseydik, Bi₀ = 10'dan başlayan bir koşuda Adam'ın ilk adımları neden sorun çıkarabilirdi?", {
  hint: "İpucu: Adam'ın adım büyüklüğü öğrenme oranı mertebesindedir; 1e-2 lr ile Bi = 0.01'e kaç adımda inilir?",
  notes: "Adam her parametreyi kabaca öğrenme oranı kadar oynatır, gradyanın büyüklüğünden bağımsız. Doğrudan Bi öğrenirsek adım mutlak: Bi 10'dayken 0.01'lik adım binde bir, Bi 0.05'teyken yüzde yirmi. " +
    "Robin terimi başta Bi'yi aşağı ittiği için küçük Bi bölgesinde adımlar göreli olarak dev olur ve Bi sıfırın altına geçebilir. Logaritmik parametrede adım göreli ve pozitiflik garanti." });

// =========================================================== 2 · NE KADAR BİLGİ VAR?
const SEC2 = "2 · Ne kadar bilgi var?";
deck.section(SEC2, "02", "Ne kadar bilgi var?", "Duyarlılık, Cramér–Rao sınırı ve sensör yerleşimi",
  { roadmapSteps: LOCAL, active: new Set([2]), notes: "İkinci bölüm: deney yapmadan, ölçümlerin Bi hakkında ne kadar bilgi taşıdığını hesaplıyoruz." });
{
  const s = deck.content(SEC2, "Bi yalnız soğutulan yüzeyin yakınını değiştirir: üst yarıdaki sensörler onu neredeyse görmez", { step: "ADIM 7 · DUYARLILIK",
    notes: "Renk, Bi'yi biraz değiştirince her noktada sıcaklığın ne kadar değiştiği. FDM'i Bi artı eksi binde birle iki kez çözüp merkezi farkla hesapladık; bir saniyelik iş. " +
      `En büyük duyarlılık alt yüzeyin ortasında, ${SENS.max.toFixed(3)}. Merkezde ${Math.abs(SENS.center).toFixed(4)}, dört kat küçük. Üst yarıda en çok ${SENS.top_half_max.toFixed(3)}. ` +
      "Fiziksel okuma: Bi alt yüzeydeki ısı akısını belirliyor; Dirichlet duvarlarına yakın her nokta duvar sıcaklığına kilitli ve Bi'yi duymuyor. " +
      "Üç yerleşim: düzgün, üst yarı ve alt şerit, her biri 20 sensör. Başlıklardaki sayı Cramér–Rao alt sınırı; bir sonraki slaytta tanımlıyoruz." });
  deck.image(s, "01_sensitivity.png", { x: M, y: BODY_TOP - 0.1, w: W - 2 * M, h: 4.55 });
  const cw = (W - 2 * M - 0.6) / 3;
  [[`alt yüzey ortası: |S| = ${SENS.max.toFixed(3)}`], [`merkez: |S| = ${Math.abs(SENS.center).toFixed(4)}`], [`üst yarı: |S| ≤ ${SENS.top_half_max.toFixed(3)}`]]
    .forEach(([h], i) => deck.card(s, { x: M + i * (cw + 0.3), y: 6.05, w: cw, h: 0.68, head: h, headSize: 13 }));
}
{
  const s = deck.content(SEC2, "Cramér–Rao sınırı, deneyden önce en iyi olası Bi belirsizliğini verir", { step: "ADIM 7 · BİLGİ", level: YL,
    notes: "Ölçüm modeli: her sensörde theta artı Gauss gürültüsü. Bi küçük değişince ölçümlerin beklenen değeri S çarpı delta Bi kadar değişir. " +
      "Fisher bilgisi, bu değişimlerin karelerinin toplamı bölü sigma kare. Cramér–Rao eşitsizliği: hiçbir yansız tahmincinin standart sapması I üzeri eksi yarımdan küçük olamaz. " +
      `Sayılar: sigma 0.01, 20 düzgün sensör: yüzde ${(100 * base.crb_rel).toFixed(1)}. Alt şerit yüzde ${(100 * bot.crb_rel).toFixed(1)}, üst yarı yüzde ${(100 * top.crb_rel).toFixed(1)}. ` +
      "Kök N_d ölçeklenmesi: sensör sayısını dört katına çıkarmak belirsizliği yarıya indirir; sensörü duyarlılığı dört kat büyük yere koymak da aynı işi yapar. Yerleşim, sayı kadar güçlü bir kaldıraç. " +
      "Bu bir alt sınır ve doğrusallaştırmaya dayanıyor; bu kadar küçük gürültüde doğrusallaştırma iyi çalışıyor." });
  deck.mathBox(s, ["fisher"], { x: M, y: BODY_TOP, w: W - 2 * M, h: 1.45 });
  deck.mathBox(s, ["crb_scale"], { x: M, y: BODY_TOP + 1.7, w: 4.6, h: 1.25, scale: 0.9 });
  const cw = (W - 2 * M - 4.9 - 0.6) / 3, x0 = M + 4.9;
  [[base, "20 düzgün", hex("plan")], [bot, "20 alt şerit", hex("lila")], [top, "20 üst yarı", hex("parca_mandalina")]]
    .forEach(([v, l, col], i) => deck.stat(s, { x: x0 + i * (cw + 0.3), y: BODY_TOP + 1.7, w: cw, value: p1(v.crb_rel), unit: "", label: `CRB σ_Bi/Bi · ${l}`, color: col }));
  deck.card(s, { x: M, y: BODY_TOP + 3.25, w: W - 2 * M, h: 1.35, head: "Deney tasarımı kuralı",
    body: "Sensörü duyarlılığın büyük olduğu yere koy: 20 sensörü alt şeride almak, düzgün dağılımı 4–5 kat sensörle eşleştirir. Üst yarıya koymak 4 kat kötüleştirir." });
}
{
  const s = deck.content(SEC2, "PINN'in Bi hatası her yerleşim ve sayıda Cramér–Rao sınırı mertebesinde; aynı sensörlerle FDM + en küçük kareler de öyle", { step: "ADIM 7 · SONUÇLAR",
    notes: "Her sütun bir deney, üç tohum. Dolu daire PINN, boş daire aynı sensörler ve aynı gürültüyle klasik yöntem: FDM N 101'i bir en küçük kareler döngüsüne koyup log Bi'yi optimize ediyoruz. Çizgi Cramér–Rao sınırı. " +
      `Temel: PINN ${bis(base)}, klasik ${lss(base)}. ` +
      `Alt şerit en iyisi: PINN ortalama hata ${p1(bot.pinn_rel_err_mean)}. Üst yarı en kötüsü: ${p1(top.pinn_rel_err_mean)}; bir tohumda Bi ${top.runs[0].Bi_hat.toFixed(2)}, klasik yöntem de ${top.runs[0].fdm_ls_Bi.toFixed(2)} buluyor. ` +
      (n5 && n80 ? `Sayı: 5 sensörde ${p1(n5.pinn_rel_err_mean)}, 80 sensörde ${p1(n80.pinn_rel_err_mean)}. ` : "") +
      "Üç tohumla standart sapmayı iyi tahmin edemeyiz; ama hata sınır mertebesinde dağılıyor, sistematik olarak üstünde değil. Yani PINN'in tahmini gürültü sınırlı: yöntemden değil, ölçümden gelen bir belirsizlik." });
  deck.image(s, "03_error_crb.png", { x: M, y: BODY_TOP - 0.1, w: W - 2 * M, h: 4.55 });
  const cw = (W - 2 * M - 0.6) / 3;
  [[`alt şerit: PINN ${p1(bot.pinn_rel_err_mean)} · CRB ${p1(bot.crb_rel)}`], [`temel: PINN ${p1(base.pinn_rel_err_mean)} · CRB ${p1(base.crb_rel)}`],
   [`üst yarı: PINN ${p1(top.pinn_rel_err_mean)} · CRB ${p1(top.crb_rel)}`]]
    .forEach(([h], i) => deck.card(s, { x: M + i * (cw + 0.3), y: 6.05, w: cw, h: 0.68, head: h, headSize: 13 }));
}
{
  const s = deck.content(SEC2, "Aynı veriden PINN ve klasik yöntem aynı Bi'yi bulur; kalan fark gürültü değil, tohum farkı", { step: "ADIM 7 · KARŞILAŞTIRMA",
    notes: "Her nokta bir sensör kümesi. Yatay eksen klasik yöntemin, dikey eksen PINN'in tahmini. Köşegen üzerindeyse iki yöntem aynı veriden aynı cevabı buluyor. " +
      `Köşe dışlamalı koşularda PINN ile klasik arasındaki fark, Bi'nin yüzdesi olarak ortanca ${p2(V.pinn_vs_fdm_ls_abs_diff_rel_median_skip)}. ` +
      "Bu çok önemli bir okuma: tahmindeki hatanın kaynağı yöntem değil, o tohumdaki gürültü gerçekleşmesi. Klasik yöntem de aynı yöne aynı miktarda kayıyor. " +
      "Kırmızı noktalar köşegenin altında: köşe dışlanmazsa PINN sistematik olarak düşük Bi buluyor. Üçüncü bölümün konusu." });
  deck.image(s, "04_parity.png", { x: M, y: BODY_TOP - 0.1, w: 5.4, h: 4.8 }, "left");
  const x0 = M + 5.8, sw = W - M - x0;
  deck.stat(s, { x: x0, y: BODY_TOP, w: sw, value: p2(V.pinn_vs_fdm_ls_abs_diff_rel_median_skip), unit: "", label: "|PINN − klasik| / Bi · ortanca (köşe dışlamalı)" });
  deck.stat(s, { x: x0, y: BODY_TOP + 1.5, w: sw, value: (V.noskip_bias_mean >= 0 ? "+" : "") + V.noskip_bias_mean.toFixed(2), unit: "", label: "köşe dışlanmazsa PINN − klasik (ortalama Bi farkı)", color: hex("hata") });
  deck.card(s, { x: x0, y: BODY_TOP + 3.05, w: sw, h: 1.6, head: "Okuma",
    body: "Hata ölçümden geliyor, yöntemden değil. PINN'den daha iyi Bi beklemek için daha çok ya da daha iyi yerleştirilmiş sensör gerekir." });
}
deck.question(SEC2, "Bütçeniz 10 termokupl. Bi'yi en iyi kestirmek için nereye koyarsınız ve neden tümünü tam alt yüzey ortasına koymazsınız?", {
  hint: "İpucu: Cramér–Rao bağımsız gürültü varsayar. Gerçek bir termokuplda gürültü dışında ne vardır?",
  notes: "Saf Cramér–Rao hesabı hepsini duyarlılığın en büyük olduğu yere, alt yüzey ortasına koymayı söyler. Pratikte üç sebeple yaymak gerekir. " +
    "Bir, sistematik hata: konum belirsizliği, temas direnci, kalibrasyon kayması; aynı noktadaki ölçümler bunları ortalayamaz. " +
    "İki, model hatası: gerçek h alt yüzey boyunca sabit olmayabilir; yayılmış sensörler bunu fark eder. Üç, sayısal model köşelerde zayıf; köşelerden uzak durun. Makul cevap: alt şeritte, köşelerden uzak, yatay olarak yayılmış." });

// =========================================================== 3 · TUZAKLAR VE MALİYET
const SEC3 = "3 · Tuzaklar ve maliyet";
deck.section(SEC3, "03", "Tuzaklar ve maliyet", "Köşe yanlılığı, gürültü ve hesap süresi",
  { roadmapSteps: LOCAL, active: new Set([3]), notes: "Üçüncü bölüm: bu problemde PINN'i yanıltan şey ve PINN'in klasik yönteme göre maliyeti." });
{
  const s = deck.content(SEC3, `Köşe çelişkisi Robin kaybını küçük Bi'ye iter: dışlanmazsa Bi ortalama ${Math.abs(V.noskip_bias_mean).toFixed(2)} düşük çıkar`, { step: "ADIM 7 · KÖŞE YANLILIĞI",
    notes: "Ders 02'den hatırlayın: alt köşelerde yan duvar theta = 1 dayatıyor, eğim sıfır. Robin koşulu ise eğimin Bi çarpı theta olmasını istiyor. Köşede ikisi birden sağlanamaz. " +
      "Forward problemde bu yalnız kaybın tabanını yükseltiyordu. Ters problemde daha sinsi: köşede artık eksi Bi, karesi Bi kare. Kaybı azaltmanın en kolay yolu Bi'yi küçültmek. " +
      `Sonuç: aynı sensörlerle köşe noktaları dahilken PINN ${bis(nosk)}; dışlayınca ${bis(base)}; klasik yöntem ${lss(base)}. ` +
      "Çözüm basit: köşeden delta 0.02 içindeki Robin kolokasyon noktalarını kayıptan çıkarmak. Genel ders: fiziksel modeldeki bir tekillik, ters problemde parametre yanlılığına dönüşür. Ölçümler bunu kendiliğinden düzeltmez." });
  deck.mathBox(s, ["corner"], { x: M, y: BODY_TOP, w: W - 2 * M, h: 1.2, scale: 0.95 });
  deck.image(s, "05_corner.png", { x: M, y: BODY_TOP + 1.35, w: 6.4, h: 3.35 }, "left");
  const x0 = M + 6.8, sw = W - M - x0;
  deck.card(s, { x: x0, y: BODY_TOP + 1.35, w: sw, h: 1.55, head: "δ = 0 (köşe dahil)", body: `PINN Bi: ${bis(nosk)}` });
  deck.card(s, { x: x0, y: BODY_TOP + 3.1, w: sw, h: 1.55, head: "δ = 0.02 (köşe dışlanmış)", body: `PINN Bi: ${bis(base)} · klasik: ${lss(base)}` });
}
{
  const s = deck.content(SEC3, "Gürültü düzeyi Bi hatasını doğrudan belirler; gürültüsüz ölçümle PINN Bi'yi binde birin altında bulur", { step: "ADIM 7 · GÜRÜLTÜ",
    notes: "Aynı 20 sensör, tohum 0, üç gürültü düzeyi. " +
      (NZ["0.0"] ? `Gürültüsüz ölçümle PINN Bi'yi ${p2(NZ["0.0"].Bi_rel_err)} hatayla buluyor; klasik ${p2(NZ["0.0"].fdm_ls_rel_err)}. Bu taban, PINN'in kendi sayısal hatasından geliyor. ` : "") +
      `Sigma 0.01'de ${p1(NZ["0.01"].Bi_rel_err)}, sınır ${p1(NZ["0.01"].crb_rel)}. ` +
      (NZ["0.05"] ? `Sigma 0.05'te, iki buçuk derece gürültüde ${p1(NZ["0.05"].Bi_rel_err)}, sınır ${p1(NZ["0.05"].crb_rel)}. ` : "") +
      "Etiketler alt yüzeydeki ısı akısının hatası: Bi yüzde birkaç yanlış olsa da ısı akısı daha az etkileniyor, çünkü sıcaklık alanı da Bi ile birlikte uyum sağlıyor." });
  deck.image(s, "06_noise.png", { x: M, y: BODY_TOP - 0.1, w: 6.8, h: 4.6 }, "left");
  const x0 = M + 7.2, sw = W - M - x0;
  if (NZ["0.0"]) deck.stat(s, { x: x0, y: BODY_TOP, w: sw, value: p2(NZ["0.0"].Bi_rel_err), unit: "", label: "σ = 0 · PINN Bi hatası (sayısal taban)" });
  deck.stat(s, { x: x0, y: BODY_TOP + 1.5, w: sw, value: p1(NZ["0.01"].Bi_rel_err), unit: "", label: `σ = 0.01 · CRB ${p1(NZ["0.01"].crb_rel)}`, color: hex("titanyum") });
  if (NZ["0.05"]) deck.stat(s, { x: x0, y: BODY_TOP + 3.0, w: sw, value: p1(NZ["0.05"].Bi_rel_err), unit: "", label: `σ = 0.05 · CRB ${p1(NZ["0.05"].crb_rel)}`, color: hex("lila") });
}
{
  const s = deck.content(SEC3, `Bu problemde klasik yöntem aynı doğruluğu ${Math.round(tPINN / tLS)} kat daha hızlı verir; PINN'in avantajı başka yerde`, { step: "ADIM 7 · MALİYET",
    notes: `Dürüst karşılaştırma. Bir PINN ters koşusu iki çekirdekte yaklaşık ${tPINN} saniye. Klasik yöntem, FDM N 101 ile en küçük kareler, yaklaşık ${tLS.toFixed(1)} saniye. ` +
      "Doğruluk aynı, çünkü ikisi de gürültü sınırında. Bu iki boyutlu, tek parametreli ve hızlı bir çözücüsü olan problemde klasik yöntem açık ara kazanıyor. " +
      "PINN ne zaman anlamlı olur? Birincisi, çözücü pahalı ve türevlenemez olduğunda: her en küçük kareler adımı bir CFD koşusuysa. İkincisi, bilinmeyen bir sayı değil bir alan olduğunda, örneğin h'nin yüzey boyunca dağılımı: klasik yöntemde parametre sayısı patlar, PINN'de bir ağ daha. " +
      "Üçüncüsü, aynı ağın her Bi için çözüm vermesi: parametrik PINN, gelecek ders. Orada ters problem bir eğitim değil, bir arama olur." });
  const cw = (W - 2 * M - 0.3) / 2;
  deck.stat(s, { x: M, y: BODY_TOP, w: cw, value: `${tPINN}`, unit: "s", label: "PINN ters koşu (Adam 6000 + L-BFGS, 2 CPU)", color: hex("plan") });
  deck.stat(s, { x: M + cw + 0.3, y: BODY_TOP, w: cw, value: tLS.toFixed(1), unit: "s", label: "FDM (N = 101) + en küçük kareler", color: hex("titanyum") });
  const c3 = (W - 2 * M - 0.6) / 3;
  [["Pahalı çözücü", "Her en küçük kareler adımı bir CFD koşusuysa PINN tek eğitimde ters problemi çözer."],
   ["Alan bilinmeyen", "h(ξ) gibi dağılım: klasik yöntemde parametre sayısı artar; PINN'de bir ağ daha."],
   ["Parametrik ağ", "θ̂(ξ, η; Bi) bir kez eğitilir; ters problem saniyede bir aramaya dönüşür (Ders 05)."]]
    .forEach(([h, b], i) => deck.card(s, { x: M + i * (c3 + 0.3), y: BODY_TOP + 1.65, w: c3, h: 2.9, head: h, body: b, num: i + 1, headSize: 17, bodySize: 14 }));
}
deck.question(SEC3, "Köşe dışlama δ'yı 0.02 yerine 0.2 yapsaydık Bi tahmini ne olurdu? Hangi bilgi kaybolur?", {
  hint: "İpucu: duyarlılık haritasında alt yüzeyin hangi kısmı Bi hakkında en çok bilgi taşıyor?",
  notes: "Delta 0.2 olursa alt yüzeyin yüzde kırkında Robin koşulu kayıptan çıkar. Ağ o bölgede eğimi istediği gibi seçebilir, Bi'nin belirlenmesi tamamen ölçümlere ve PDE'ye kalır. " +
    "Bi hâlâ orta bölgedeki Robin noktalarıyla bağlı olduğu için tahmin büyük ölçüde korunur, ama köşelere yakın sıcaklık alanı serbestleşir ve bu sensörlerle çekişmeye girebilir. Bir alıştırma olarak deneyin: delta 0, 0.02, 0.05, 0.1, 0.2." });

// =========================================================== KAPANIŞ
const SEC4 = "Kapanış";
pres.addSection({ title: SEC4 });
{
  const s = deck.content(SEC4, "Bu dersin üç çıkarımı", { dark: true,
    notes: "Bir: Bi'yi logaritmik bir parametre yapmak tek satır; PINN onu ağırlıklarla birlikte, gürültünün izin verdiği doğrulukta buluyor. " +
      "İki: ne kadar doğru bulabileceğinizi deneyden önce hesaplayın. Duyarlılık haritası ve Cramér–Rao sınırı sensör yerleşimini belirler. " +
      "Üç: modeldeki tekillik ters problemde yanlılık olur; ve her zaman aynı veriyle klasik bir tabanla karşılaştırın." });
  const cw = (W - 2 * M - 0.6) / 3;
  [["Bi = eˢ, birlikte öğren", `Bi₀ = 1'den ${bis(base)} (gerçek ${BI.toFixed(2)}). Hata gürültü sınırında; aynı veriyle klasik yöntem aynı sonucu buluyor.`],
   ["Bilgiyi önce hesapla", `20 sensör: alt şerit CRB ${p1(bot.crb_rel)}, düzgün ${p1(base.crb_rel)}, üst yarı ${p1(top.crb_rel)}. Yerleşim, sayı kadar etkili.`],
   ["Tekillik → yanlılık", `Köşe Robin noktaları dahilken Bi ortalama ${Math.abs(V.noskip_bias_mean).toFixed(2)} düşük. Dışla ve klasik tabanla karşılaştır.`]]
    .forEach(([h, b], i) => deck.card(s, { x: M + i * (cw + 0.3), y: BODY_TOP + 0.2, w: cw, h: 2.7, head: h, body: b, num: i + 1, dark: true, headSize: 19, bodySize: 16 }));
  s.addText("Sıradaki adım: Bi'yi ağın girdisi yapmak (parametrik PINN).", { x: M, y: 5.4, w: W - 2 * M, h: 0.5,
    fontSize: 16, color: hex("gumus"), margin: 0, isTextBox: true, objectName: "sum_next" });
}
{
  const s = deck.content(SEC4, "Uygulama: kodu çalıştırın, sonra deneyleri düzeyinize göre yapın", { step: "UYGULAMA",
    notes: "Her ters koşu iki çekirdekte yaklaşık sekiz dakika; klasik taban bir saniye. Lisans öğrencileri sol sütunu, yüksek lisans öğrencileri ayrıca sağ sütunu yapsın. Her sonucu Cramér–Rao sınırı ve klasik tabanla birlikte raporlayın." });
  s.addShape(pres.shapes.RECTANGLE, { x: M, y: BODY_TOP, w: 4.5, h: 4.35, fill: { color: hex("derin") }, line: { type: "none" }, objectName: "code_bg2" });
  s.addText([
    { text: "python inverse_classical.py", options: { breakLine: true } },
    { text: "python pinn_inverse.py \\", options: { breakLine: true } },
    { text: "  --bi0 1 --n-data 20 \\", options: { breakLine: true } },
    { text: "  --where bottom \\", options: { breakLine: true } },
    { text: "  --tag deneme", options: { breakLine: true } },
    { text: "python inverse_summary.py", options: {} },
  ], { x: M + 0.25, y: BODY_TOP + 0.25, w: 4.05, h: 3.85, fontFace: "Courier New", fontSize: 13, color: hex("krom"),
    valign: "top", margin: 0, paraSpaceAfter: 8, isTextBox: true, objectName: "code2" });
  const cx = M + 4.8, cw = (W - M - cx - 0.3) / 2;
  deck.card(s, { x: cx, y: BODY_TOP, w: cw, h: 4.35, head: "Lisans",
    body: "1. 10 sensörü alt şeride koyun: CRB'yi hesaplayın, sonra PINN ile deneyin.\n2. Bi₀ = 0.2 ve 25'ten başlatın: aynı değere yakınsıyor mu?\n3. δ = 0, 0.02, 0.05, 0.1 taraması.", headSize: 18, bodySize: 14 });
  deck.card(s, { x: cx + cw + 0.3, y: BODY_TOP, w: cw, h: 4.35, head: "Yüksek lisans",
    body: "1. 20 tohumla PINN Bi dağılımının standart sapmasını CRB ile karşılaştırın.\n2. h(ξ) = Bi·(1 + a ξ(1−ξ)) yapın; a'yı da öğrenin.\n3. Sensör konumlarına ±1 mm hata ekleyin: yanlılık ne kadar?", headSize: 18, bodySize: 14 });
}
{
  const s = deck.content(SEC4, "Sıradaki ders: Bi'yi ağın girdisi yapacağız", { step: "DERS 05 · ÖNİZLEME",
    notes: "Gelecek ders sekizinci adım, parametrik PINN. Bi'yi kayıptaki bir sabit ya da öğrenilen bir sayı değil, ağın üçüncü girdisi yapıyoruz. " +
      "Bir kez, Bi aralığı boyunca eğitip her Bi için çözümü saniyenin altında veren bir yedek model elde ediyoruz. Bugünkü ters problem orada eğitim gerektirmeyen bir aramaya dönüşüyor." });
  deck.mathBox(s, ["pv_param"], { x: M, y: BODY_TOP, w: W - 2 * M, h: 1.5 });
  const cw = (W - 2 * M - 0.6) / 3;
  [["Girdi", "(ξ, η, Bi): Bi aralığı boyunca tek eğitim"], ["Soru", "Aralık genişledikçe doğruluk ne kadar düşer?"], ["Bağlantı", "Ters problem: eğitim değil, saniyelik arama"]]
    .forEach(([h, b], i) => deck.card(s, { x: M + i * (cw + 0.3), y: 3.9, w: cw, h: 1.6, head: h, body: b, headSize: 18, bodySize: 14 }));
}
{
  const s = deck.content(SEC4, "Kaynaklar", {
    notes: "Raissi ve arkadaşları ters PINN'i tanıtıyor. Beck ve Arnold, ısı transferinde parametre kestiriminin klasik kitabı; duyarlılık ve Fisher bilgisi buradan. Kay, kestirim kuramı ve Cramér–Rao sınırı için standart başvuru." });
  deck.card(s, { x: M, y: BODY_TOP, w: W - 2 * M, h: 2.7, head: "Okuma listesi",
    body: "M. Raissi, P. Perdikaris, G. E. Karniadakis · Physics-informed neural networks, J. Comput. Phys. 378 (2019) 686–707\n" +
      "J. V. Beck, K. J. Arnold · Parameter Estimation in Engineering and Science, Wiley (1977)\n" +
      "S. M. Kay · Fundamentals of Statistical Signal Processing, Vol. I: Estimation Theory, Prentice Hall (1993)\n" +
      "Kod: github.com/mikbalarikan/kolay-pinn · cases/01-2d-heat-conduction/pinn_inverse.py, inverse_classical.py", headSize: 18, bodySize: 14 });
}

const out = path.join(__dirname, "ders04_ters_problem.pptx");
deck.write(out).then((f) => console.log(f));
