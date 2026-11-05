/**
 * Kolay PINN · Türkişi ders destesi çatısı (pptxgenjs).
 *
 * Ders tekniği (docs/DERS_STILI.md):
 *   - İddia-kanıt: başlık tam bir cümledir; gövde o iddianın görsel kanıtıdır.
 *   - Bölümlere ayırma: her bölüm bir ara sayfa ile açılır, yol haritası mevcut adımı işaretler.
 *   - Ön eğitim: kavramlar içerikten önce tanıtılır.
 *   - Sinyal: slaytta tek vurgu (Fosfor Sarısı adım çipi, Plan Camgöbeği veri).
 *   - Fazlalıktan kaçınma: anlatım konuşmacı notlarındadır, slaytta değil.
 *   - Geri çağırma: her bölüm bir kontrol sorusuyla biter; cevap notlarda.
 *   - Düzey: yüksek lisans derinliğindeki slaytlar Lila "YÜKSEK LİSANS" rozeti taşır.
 *
 * Kullanım:  const D = require("../../../kolay_pinn/deck/turkisi_deck.js");
 *            const deck = D.createDeck({ course: "KOLAY PINN", lecture: "Ders 01", assets });
 */
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
// jszip ships with pptxgenjs; resolve it from there so no extra install is needed
const JSZip = require(require.resolve("jszip", { paths: [path.dirname(require.resolve("pptxgenjs")), __dirname] }));

const ROOT = path.resolve(__dirname, "..", "..");
const PAL = JSON.parse(fs.readFileSync(path.join(ROOT, "brand", "palette.json"), "utf8")).colors;
const hex = (k) => PAL[k].hex.replace("#", "");

// Theme: scheme colours map onto the Türkişi palette
const THEME = {
  name: "Turkisi Kolay PINN",
  headFontFace: "Arial",
  bodyFontFace: "Arial",
  colors: {
    dk1: hex("derin"), lt1: "FFFFFF", dk2: hex("zemin"), lt2: hex("krom"),
    accent1: hex("plan"), accent2: hex("lila"), accent3: hex("celik_mavisi"),
    accent4: hex("fosfor_sarisi"), accent5: hex("titanyum"), accent6: hex("kirmizi"),
    hlink: hex("elektrik"), folHlink: hex("lila"),
  },
};

const W = 13.333, H = 7.5, M = 0.6;           // LAYOUT_WIDE, margin
const TITLE = { x: M, y: 0.78, w: W - 2 * M, h: 1.05 };
const BODY_TOP = 2.05;                         // first y under a title
const FOOT_Y = 6.98;

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}

function createDeck({ course, lecture, assets, title, eqDir }) {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.author = "Türkişi Engineering";
  pres.company = "Türkişi Engineering";
  pres.title = title || `${course} · ${lecture}`;
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;
  const A = (f) => path.join(assets, f);
  const EQ = eqDir ? JSON.parse(fs.readFileSync(path.join(eqDir, "index.json"), "utf8")) : {};
  const eqUsed = {};
  const footer = `${course} · ${lecture}`;

  // ---------- layouts ----------
  pres.defineSlideMaster({
    title: "KAPAK",
    background: { color: hex("zemin") },
    objects: [
      { image: { x: M, y: 0.55, w: 0.62, h: 0.53, path: A("ti_light.png") } },
      { text: { text: "TÜRKİŞİ ENGINEERING", options: { x: M + 0.75, y: 0.6, w: 5, h: 0.42, fontSize: 13, color: hex("krom"), charSpacing: 4, fontFace: "Courier New", bold: true, margin: 0, valign: "middle" } } },
    ],
  });
  pres.defineSlideMaster({
    title: "BOLUM",
    background: { color: hex("zemin") },
    objects: [
      { image: { x: M, y: FOOT_Y - 0.06, w: 0.36, h: 0.31, path: A("ti_light.png") } },
      { text: { text: footer, options: { x: M + 0.48, y: FOOT_Y, w: 6, h: 0.25, fontSize: 10, color: hex("titanyum"), margin: 0 } } },
    ],
    slideNumber: { x: W - M - 0.6, y: FOOT_Y, w: 0.6, h: 0.25, fontSize: 10, color: hex("titanyum"), align: "right" },
  });
  pres.defineSlideMaster({
    title: "ICERIK",
    background: { color: "FFFFFF" },
    objects: [
      { image: { x: M, y: FOOT_Y - 0.06, w: 0.36, h: 0.31, path: A("ti_dark.png") } },
      { text: { text: footer, options: { x: M + 0.48, y: FOOT_Y, w: 6, h: 0.25, fontSize: 10, color: hex("titanyum"), margin: 0 } } },
      { placeholder: { options: { name: "title", type: "title", ...TITLE, fontSize: 28, bold: true, color: C.text1, valign: "top", align: "left", margin: 0 }, text: "" } },
    ],
    slideNumber: { x: W - M - 0.6, y: FOOT_Y, w: 0.6, h: 0.25, fontSize: 10, color: hex("titanyum"), align: "right" },
  });
  pres.defineSlideMaster({
    title: "KOYU_ICERIK",
    background: { color: hex("zemin") },
    objects: [
      { image: { x: M, y: FOOT_Y - 0.06, w: 0.36, h: 0.31, path: A("ti_light.png") } },
      { text: { text: footer, options: { x: M + 0.48, y: FOOT_Y, w: 6, h: 0.25, fontSize: 10, color: hex("titanyum"), margin: 0 } } },
      { placeholder: { options: { name: "title", type: "title", ...TITLE, fontSize: 28, bold: true, color: C.background2, valign: "top", align: "left", margin: 0 }, text: "" } },
    ],
    slideNumber: { x: W - M - 0.6, y: FOOT_Y, w: 0.6, h: 0.25, fontSize: 10, color: hex("titanyum"), align: "right" },
  });

  // ---------- components ----------
  let n = 0;
  const id = (p) => `${p}_${++n}`;

  const deck = {
    pres, C, W, H, M, BODY_TOP, THEME, hex, A,

    content(section, title, opts = {}) {
      const s = pres.addSlide({ masterName: opts.dark ? "KOYU_ICERIK" : "ICERIK", sectionTitle: section });
      s.addText(title, { placeholder: "title" });
      if (opts.step) deck.chip(s, opts.step, M, 0.38);
      if (opts.level) deck.levelBadge(s, opts.level);
      if (opts.notes) s.addNotes(opts.notes);
      return s;
    },

    chip(s, text, x, y) {          // Fosfor Sarısı step chip (the one accent)
      const w = 0.32 + 0.105 * text.length;
      s.addText(text, { x, y, w, h: 0.32, shape: pres.shapes.RECTANGLE, fill: { color: C.accent4 },
        color: C.text1, fontFace: "Courier New", bold: true, fontSize: 11, charSpacing: 1, margin: [0, 8, 0, 8],
        valign: "middle", isTextBox: true, objectName: id("chip") });
    },

    levelBadge(s, text) {          // YÜKSEK LİSANS depth marker
      const w = 0.3 + 0.1 * text.length;
      s.addText(text, { x: W - M - w, y: 0.38, w, h: 0.32, shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.08,
        fill: { color: C.accent2 }, color: "FFFFFF", bold: true, fontSize: 11, charSpacing: 1, align: "center",
        valign: "middle", margin: 0, isTextBox: true, objectName: id("level") });
    },

    image(s, file, box, align = "center") {   // fit inside box, keep aspect
      const { w: pw, h: ph } = pngSize(A(file));
      const r = Math.min(box.w / pw, box.h / ph);
      const w = pw * r, h = ph * r;
      const x = align === "left" ? box.x : box.x + (box.w - w) / 2;
      s.addImage({ path: A(file), x, y: box.y + (box.h - h) / 2, w, h, objectName: id("fig") });
      return { x, y: box.y + (box.h - h) / 2, w, h };
    },

    card(s, { x, y, w, h, head, body, num, dark, headSize = 16, bodySize = 14, math, mathScale = 1 }) {
      s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: dark ? hex("panel") : hex("krom") }, line: { type: "none" }, objectName: id("card") });
      let tx = x + 0.25;
      if (num !== undefined) {
        s.addText(String(num), { x: x + 0.25, y: y + 0.25, w: 0.5, h: 0.5, shape: pres.shapes.OVAL,
          fill: { color: C.accent3 }, color: "FFFFFF", bold: true, fontSize: 16, align: "center", valign: "middle",
          margin: 0, isTextBox: true, objectName: id("num") });
        tx = x + 0.95;
      }
      const tw = x + w - 0.25 - tx;
      const fg = dark ? C.background2 : C.text1;
      const runs = [];
      if (math) {
        // head, then the equation, then body underneath
        s.addText(head, { x: tx, y: y + 0.22, w: tw, h: 0.4, fontSize: headSize, bold: true, color: fg, margin: 0,
          valign: "top", isTextBox: true, objectName: id("cardhead") });
        const m = deck.math(s, math, { x: tx, y: y + 0.75, scale: mathScale });
        if (body) s.addText(body, { x: tx, y: m.y + m.h + 0.18, w: tw, h: y + h - 0.2 - (m.y + m.h + 0.18),
          fontSize: bodySize, color: dark ? hex("gumus") : hex("panel"), margin: 0, valign: "top", isTextBox: true,
          objectName: id("cardbody") });
        return;
      }
      if (head) runs.push({ text: head, options: { bold: true, fontSize: headSize, color: fg, breakLine: !!body } });
      if (body) runs.push({ text: body, options: { fontSize: bodySize, color: dark ? hex("gumus") : hex("panel") } });
      s.addText(runs, { x: tx, y: y + 0.22, w: tw, h: h - 0.44, valign: "top", margin: 0, paraSpaceAfter: 4,
        isTextBox: true, objectName: id("cardtext") });
    },

    // ---- matematik: LaTeX ile dizilir; PowerPoint'te düzenlenebilir denklem (OMML), diğerlerinde LaTeX görseli
    math(s, key, { x, y, scale = 1, align = "left", w: boxW, h: boxH, valign = "top" }) {
      const e = EQ[key];
      if (!e) throw new Error(`denklem yok: ${key} (önce equations.py çalıştırın)`);
      const w = e.w * scale, h = e.h * scale;
      const px = align === "center" && boxW ? x + (boxW - w) / 2 : align === "right" && boxW ? x + boxW - w : x;
      const py = valign === "middle" && boxH ? y + (boxH - h) / 2 : y;
      eqUsed[key] = e;
      s.addImage({ path: path.join(eqDir, e.png), x: px, y: py, w, h,
        altText: e.tex, objectName: `eq:${key}:${align === "center" ? "c" : "l"}:${scale}` });
      return { x: px, y: py, w, h };
    },

    mathSize(key, scale = 1) { const e = EQ[key]; return { w: e.w * scale, h: e.h * scale }; },

    // krom zeminli denklem bloğu; keys alt alta, sola yaslı, dikeyde ortalı
    mathBox(s, keys, { x, y, w, h, label, gap = 0.22, scale = 1, align = "left" }) {
      s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: hex("krom") }, line: { type: "none" }, objectName: id("eqbg") });
      let top = y + 0.2;
      if (label) {
        s.addText(label, { x: x + 0.3, y: y + 0.18, w: w - 0.6, h: 0.3, fontSize: 12, bold: true, color: hex("titanyum"),
          charSpacing: 1, margin: 0, isTextBox: true, objectName: id("eqlabel") });
        top = y + 0.55;
      }
      const hs = keys.map((k) => deck.mathSize(k, scale).h);
      const total = hs.reduce((a, b) => a + b, 0) + gap * (keys.length - 1);
      let cy = top + Math.max(0, (y + h - 0.2 - top - total) / 2);
      keys.forEach((k, i) => {
        deck.math(s, k, { x: x + 0.3, y: cy, scale, align, w: w - 0.6 });
        cy += hs[i] + gap;
      });
    },

    stat(s, { x, y, w, value, unit, label, color, dark, valueSize }) {
      s.addText([
        { text: value, options: { fontSize: valueSize || 40, bold: true, color: color || C.accent1 } },
        { text: unit ? ` ${unit}` : "", options: { fontSize: 18, bold: true, color: color || C.accent1, breakLine: true } },
        { text: label, options: { fontSize: 13, color: dark ? hex("gumus") : hex("titanyum") } },
      ], { x, y, w, h: 1.25, valign: "top", margin: 0, isTextBox: true, objectName: id("stat") });
    },

    caption(s, text, box) {
      s.addText(text, { ...box, fontSize: 12, color: hex("titanyum"), margin: 0, valign: "top", isTextBox: true, objectName: id("cap") });
    },

    roadmap(s, steps, active, { y = 3.0, dark = false, labels = true } = {}) {
      // steps: [{n, t}], active: Set of n highlighted
      const n = steps.length, gap = (W - 2 * M) / n, r = 0.62;
      s.addShape(pres.shapes.LINE, { x: M + gap / 2, y: y + r / 2, w: gap * (n - 1), h: 0,
        line: { color: dark ? hex("gunmetal") : hex("gumus"), width: 2 }, objectName: id("rail") });
      steps.forEach((st, i) => {
        const cx = M + gap * i + gap / 2, on = active.has(st.n);
        s.addText(String(st.n), { x: cx - r / 2, y, w: r, h: r, shape: pres.shapes.OVAL,
          fill: { color: on ? hex("fosfor_sarisi") : (dark ? hex("panel") : hex("krom")) },
          line: { color: on ? hex("fosfor_sarisi") : (dark ? hex("gunmetal") : hex("gumus")), width: 1.5 },
          color: on ? hex("derin") : (dark ? hex("gumus") : hex("titanyum")), bold: true, fontSize: 18,
          align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: id("step") });
        if (labels) s.addText(st.t, { x: cx - gap / 2 + 0.05, y: y + r + 0.15, w: gap - 0.1, h: 0.9, fontSize: 12,
          align: "center", valign: "top", margin: 0, bold: on,
          color: dark ? (on ? hex("krom") : hex("titanyum")) : (on ? hex("derin") : hex("titanyum")),
          isTextBox: true, objectName: id("steplbl") });
      });
    },

    question(section, q, { hint, notes, step }) {   // retrieval-practice slide (dark)
      const s = pres.addSlide({ masterName: "BOLUM", sectionTitle: section });
      deck.chip(s, step || "KONTROL SORUSU", M, 0.6);
      s.addText(q, { x: M, y: 1.4, w: 8.6, h: 3.4, fontSize: 30, bold: true, color: C.background2, valign: "top",
        margin: 0, isTextBox: true, objectName: id("q") });
      if (hint) s.addText(hint, { x: M, y: 5.0, w: 8.6, h: 1.2, fontSize: 16, color: hex("gumus"), valign: "top",
        margin: 0, isTextBox: true, objectName: id("hint") });
      s.addImage({ path: A("maskot_normal.png"), x: 9.9, y: 1.6, w: 2.8, h: 2.8, objectName: id("mascot") });
      s.addText("2 dakika düşünün, sonra cevabı birlikte kuralım.", { x: 9.4, y: 4.6, w: 3.4, h: 0.8, fontSize: 13,
        color: hex("titanyum"), align: "center", margin: 0, isTextBox: true, objectName: id("think") });
      if (notes) s.addNotes(notes);
      return s;
    },

    section(name, num, title, what, { roadmapSteps, active, notes } = {}) {
      pres.addSection({ title: name });
      const s = pres.addSlide({ masterName: "BOLUM", sectionTitle: name });
      s.addText(num, { x: M, y: 0.9, w: 3, h: 1.4, fontSize: 80, bold: true, color: C.accent4, margin: 0,
        fontFace: "Arial", isTextBox: true, objectName: id("secnum") });
      s.addText(title, { x: M, y: 2.35, w: 9, h: 1.0, fontSize: 40, bold: true, color: C.background2, margin: 0,
        valign: "top", isTextBox: true, objectName: id("sectitle") });
      s.addText(what, { x: M, y: 3.35, w: 9.5, h: 1.0, fontSize: 18, color: hex("gumus"), margin: 0, valign: "top",
        isTextBox: true, objectName: id("secwhat") });
      if (roadmapSteps) deck.roadmap(s, roadmapSteps, active, { y: 4.9, dark: true });
      if (notes) s.addNotes(notes);
      return s;
    },

    sci(v, d = 1) {               // 1.08e-4 -> "1.1×10⁻⁴"
      const [m, e] = Number(v).toExponential(d).split("e");
      const sup = { "-": "⁻", "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹" };
      return `${m}×10${String(Number(e)).split("").map((c) => sup[c]).join("")}`;
    },

    async write(file) {
      await pres.writeFile({ fileName: file });
      await applyTheme(file, THEME);
      if (eqDir) await nativeEquations(file, EQ, eqDir);
      return file;
    },
  };
  return deck;
}

// Replace each LaTeX picture named "eq:<key>:<align>:<scale>" with
//   mc:AlternateContent  ->  Choice(a14): text box holding the editable OMML equation
//                            Fallback  : the original LaTeX picture
// PowerPoint 2010+ shows the editable equation; other viewers show the LaTeX render.
async function nativeEquations(file, EQ, eqDir) {
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const NS_M = "http://schemas.openxmlformats.org/officeDocument/2006/math";
  const NS_A14 = "http://schemas.microsoft.com/office/drawing/2010/main";
  const NS_MC = "http://schemas.openxmlformats.org/markup-compatibility/2006";
  const omml = {};
  const runProps = (sz, col) => `<a:rPr lang="tr-TR" sz="${sz}"><a:solidFill><a:srgbClr val="${col}"/></a:solidFill>` +
    `<a:latin typeface="Cambria Math" panose="02040503050406030204" pitchFamily="18" charset="0"/></a:rPr>`;
  for (const name of Object.keys(zip.files).filter((f) => /^ppt\/slides\/slide\d+\.xml$/.test(f))) {
    let xml = await zip.file(name).async("string");
    let changed = false;
    xml = xml.replace(/<p:pic>([\s\S]*?)<\/p:pic>/g, (pic, inner) => {
      const m = inner.match(/<p:cNvPr id="(\d+)" name="eq:([^:"]+):([lc]):([\d.]+)"/);
      if (!m) return pic;
      const [, cid, key, al, scale] = m;
      const e = EQ[key];
      const xfrm = inner.match(/<a:xfrm[^>]*>[\s\S]*?<\/a:xfrm>/)[0];
      const sz = Math.round(e.size * Number(scale) * 100);
      if (!omml[key]) omml[key] = fs.readFileSync(path.join(eqDir, e.omml), "utf8");
      const body = omml[key].replace(/<m:r>(<m:rPr>[\s\S]*?<\/m:rPr>)?/g, (_, rp) => `<m:r>${rp || ""}${runProps(sz, e.color)}`);
      const jc = al === "c" ? "center" : "left";
      const sp = `<p:sp><p:nvSpPr><p:cNvPr id="${cid}" name="Denklem ${key}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>` +
        `<p:spPr>${xfrm}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>` +
        `<p:txBody><a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" anchor="ctr"><a:noAutofit/></a:bodyPr><a:lstStyle/>` +
        `<a:p><a:pPr algn="${al === "c" ? "ctr" : "l"}"/><a14:m><m:oMathPara xmlns:m="${NS_M}"><m:oMathParaPr><m:jc m:val="${jc}"/></m:oMathParaPr>` +
        `${body}</m:oMathPara></a14:m><a:endParaRPr lang="tr-TR" sz="${sz}"/></a:p></p:txBody></p:sp>`;
      changed = true;
      return `<mc:AlternateContent xmlns:mc="${NS_MC}"><mc:Choice xmlns:a14="${NS_A14}" Requires="a14">${sp}</mc:Choice>` +
        `<mc:Fallback>${pic}</mc:Fallback></mc:AlternateContent>`;
    });
    if (changed) zip.file(name, xml);
  }
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

// Write THEME colours + fonts into ppt/theme/theme*.xml (pptxgenjs cannot).
async function applyTheme(file, theme) {
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const esc = (t) => t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  const order = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink"];
  const scheme = order.map((k) => `<a:${k}><a:srgbClr val="${theme.colors[k]}"/></a:${k}>`).join("");
  for (const name of Object.keys(zip.files).filter((f) => /^ppt\/theme\/theme\d+\.xml$/.test(f))) {
    let xml = await zip.file(name).async("string");
    xml = xml.replace(/<a:clrScheme name="[^"]*">[\s\S]*?<\/a:clrScheme>/, `<a:clrScheme name="${esc(theme.name)}">${scheme}</a:clrScheme>`);
    xml = xml.replace(/<a:theme ([^>]*?)name="[^"]*"/, `<a:theme $1name="${esc(theme.name)}"`);
    xml = xml.replace(/(<a:majorFont>\s*<a:latin typeface=")[^"]*"/, `$1${esc(theme.headFontFace)}"`);
    xml = xml.replace(/(<a:minorFont>\s*<a:latin typeface=")[^"]*"/, `$1${esc(theme.bodyFontFace)}"`);
    zip.file(name, xml);
  }
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

module.exports = { createDeck, applyTheme, nativeEquations, THEME, PAL };
