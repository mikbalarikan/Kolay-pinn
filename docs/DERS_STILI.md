# Ders stili · Kolay PINN

Bu repo bir kursa dönüşecek (lisans + yüksek lisans). Her case bir derse karşılık gelir ve üç çıktı üretir:
**ders destesi (.pptx)**, **teknik rapor (PDF)** ve **çalışan kod**. Bu belge destelerin nasıl kurulduğunu tanımlar.

## Dayandığımız ilkeler

| İlke | Kaynak | Destede nasıl uygulanır |
|---|---|---|
| İddia-kanıt | Alley ve ark., Penn State; Garner ve ark. 2013 (anlama farkı p < .01) | Başlık tam bir cümle, bir iddia. Gövde o iddianın görsel kanıtı: figür, denklem, tablo. Madde işareti duvarı yok. |
| Bölümlere ayırma | Mayer, çoklu ortam ilkeleri | Ders 3–4 bölüme bölünür; her bölüm koyu bir ara sayfayla açılır, yol haritası mevcut adımı Fosfor Sarısı ile işaretler. |
| Ön eğitim | Mayer | Giriş bölümünde kavram sözlüğü slaytı; yeni terim ile yeni fikir aynı slaytta gelmez. |
| Sinyal | Mayer | Slaytta tek vurgu: adım çipi (Fosfor Sarısı) ve veri rengi (Plan Camgöbeği). |
| Tutarlılık / fazlalık | Mayer | Anlatım slaytta değil, konuşmacı notlarında. Notlar video kursun seslendirme metnidir. |
| Uzamsal bitişiklik | Mayer | Denklem ait olduğu şeklin hemen altında; açıklama kartı figürün yanında. |
| Geri çağırma | test etkisi | Her bölüm bir kontrol sorusuyla biter (koyu slayt, maskot). Cevap notlarda. |
| Düzey | — | Yüksek lisans derinliğindeki slaytlar sağ üstte Lila **YÜKSEK LİSANS** rozeti taşır. Ödev slaytı iki sütun: Lisans / Yüksek lisans. |

Yapı örneği olarak ETH Zürih *AI in the Sciences and Engineering* ve *Deep Learning in Scientific Computing*
derslerinin bölüm/yol haritası düzeni incelendi.

## Bir dersin iskeleti

1. **Kapak** (koyu) · 2. **Öğrenme hedefleri** (3–4, eylem fiiliyle) · 3. **Kurs yol haritası** · 4. **Kavram sözlüğü**
5. Her bölüm: **ara sayfa** → 2–5 iddia-kanıt slaytı → **kontrol sorusu**
6. **Özet** (koyu, üç çıkarım) · **Uygulama / ödev** (Lisans + Yüksek lisans) · **Sıradaki ders** · **Kaynaklar**

Hedef süre: slayt başına 1.5–2 dakika; 25 slaytlık ders ≈ 50 dakika.

## Görsel kurallar

- 16:9 (13.33″ × 7.5″), kenar boşluğu 0.6″, Arial (PowerPoint'te her yerde var, LibreOffice'te metrik uyumlu).
- Başlık 28 pt kalın, sola yaslı, en fazla iki satır. Gövde ≥ 14 pt, açıklama 12 pt Titanyum.
- Denklemler Cambria ile, Krom zeminli blokta.
- İçerik slaytları beyaz; kapak, bölüm, kontrol sorusu ve özet Lacivert Çelik (`#141F2B`).
- Ti işareti ve ders adı her slaytın altında; kimlik kırmızısı yalnız Ti noktasında.
- Slayt figürleri `use_slide_style()` ile (14–16 pt); makale figürleri `use_style()` ile (5–7 pt, Nature). Aynı figürü iki yerde kullanmayın.
- Kenar şeridi, başlık altı çizgisi, gradyan yok.

## Yeni bir ders eklemek

```bash
# 1) slayt figürleri: cases/NN-<ad>/lecture/make_slide_figures.py  -> lecture/assets/*.png
# 2) içerik:          cases/NN-<ad>/lecture/build_lecture.js        (kolay_pinn/deck/turkisi_deck.js'i kullanır)
npm install                     # pptxgenjs + jszip
python cases/NN-<ad>/lecture/make_slide_figures.py
node   cases/NN-<ad>/lecture/build_lecture.js
```

`turkisi_deck.js` bileşenleri: `content` (iddia-kanıt slaytı, `step` çipi, `level` rozeti, `notes`), `section`
(ara sayfa + yol haritası), `question` (kontrol sorusu), `card`, `eq`, `stat`, `image` (oranı koruyarak sığdırır),
`roadmap`, `caption`, `sci` (1.1×10⁻⁴ biçimi). Tema renkleri palet v5'ten gelir ve dosyaya yazılır; PowerPoint'te
tema renkleri değiştirilerek bütün deste yeniden renklendirilebilir.
