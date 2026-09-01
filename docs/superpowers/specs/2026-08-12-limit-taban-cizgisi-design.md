# CSV tezgahında limit bandı: taban ortalaması + kullanıcı sapmaları — tasarım

Tarih: 2026-08-12
Durum: onaylandı (alt sınır aynı gün eklendi — bkz. §6)

## 1. Amaç

CSV kaynaklı tezgahta (`tesis-a/tezgah-3`) grafiklerin limit çizgisi bugün
**verinin kendisiyle ilgisiz** bir yerde duruyor. Çizgi, ölçüm satırının kendi
`Limit 1..8` kolonlarından geliyor (`csv_reader.py:191-203` okur,
`csv_live.py:54-60` özelliğe bağlar) — yani uydurma değil, ama **10665
ünitesinde kullanılamaz**:

| Ünite | Özellik | CSV limiti | Gerçek ortalama | Ekrandaki % |
|---|---|---|---|---|
| 10660 | SPINDEL | 110–150 | 113,4 | ~%103 |
| 10660 | X/Y/Z AXIS | 110–168 | 107–124 | ~%100 |
| **10665** | **M131 DEBI** | **50** | **212,9** | **~%426** |
| **10665** | **M131BASINC** | **35** | **101,5** | **~%290** |
| **10665** | **M08 DEBI** | **50** | **224,1** | **~%448** |

10665'te iz, limit çizgisinin **dört katı** yükseklikte akıyor. Çizgi grafiğin
tabanına yapışıyor, yüzde rozeti kalıcı olarak kırmızı ve %400'ün üstünde
duruyor. Bu hâliyle ikisi de bilgi taşımıyor.

Bu iş, CSV tezgahında eşiği **verinin kendisinden** türetir: her grafiğin
**tüm CSV değerlerinin ortalaması** alınır ve eşik onun **%N üstüne** konur.
N varsayılan %10'dur ve **karşılama ekranından değiştirilebilir**.

## 2. Kilitlenen kararlar

| Konu | Karar | Gerekçe |
|---|---|---|
| Ortalamanın kapsamı | Her (ünite, yuva) için **262 dosyanın tamamı**, açılışta bir kez | "O grafiğin tüm değerleri" birebir bu demek. Sabit taban: tekrar döngüsü başa sardığında çizgi yerinden oynamaz |
| Nerede hesaplanır | Backend, CSV ingest görevi başlarken | Dosyalar zaten backend'in elinde; `read_moments` aynı listeyi zaten geziyor |
| Wire alanı | Yeni `Feature.baseline` — **ham ortalama** | Backend OLGUYU yollar; eşik bir gösterim politikasıdır |
| CSV özelliğinde `limitLevel`/`pct` | **Boş bırakılır** | O ikisi Promos3 tel kavramıdır (`domain.py:97-102`, "rapor Part 5"). Aynı alana kaynağa göre iki ayrı anlam yüklemek, tel tarafını da bulanıklaştırır |
| Ham CSV limitleri | `limits[]` içinde **olduğu gibi kalır** | Veridir; silmek için sebep yok |
| Sapma yüzdesi nerede durur | İstemci tercihi — **adres çubuğunda** (`?sapma=`), varsayılan %10 | Hub tek durumu HERKESE yayınlar; sunucuda global bir sayı olsaydı bir kullanıcının seçimi diğerlerinin ekranını değiştirirdi. Taşıyıcı olarak adres seçildi (`localStorage` değil): `tezgah` zaten öyle taşınıyor ve kabuk sorguyu ekranlar arasında koruyor (`uygulama-kabugu.tsx`, `git`) |
| Sapma denetimi | Karşılama ekranı, sekmelerin ÜSTÜ | Her tezgah için geçerli — tesis panelinin içine girerse kapsamı yanlış okunur |
| Denetim bileşeni | `NumberInput` (`Field` içinde, `unit="%"`) | COMPONENTS.md bunu "tolerans, eşik" için adlandırır; TR klavye virgül tuzağını ve "boş = `null`, 0 DEĞİL" kuralını kendi taşır |

### Kapsam dışı (açıkça)

- **Promos3 tezgahlarına dokunulmaz.** `tesis-a/tezgah-1` (provis) ve
  `tezgah-2` (promos3-sim) telden GERÇEK eşik alır; onlar `limitLevel`
  yolunda kalır ve bu değişiklikten hiç etkilenmez.
- Şema/migration yok: `baseline` türetilmiş bir sayıdır, diske yazılmaz.
- Alarm üretimi değişmez. CSV'nin alarm biti (`rec.alarm`) ne ise odur;
  yeni eşik alarm TETİKLEMEZ, yalnız çizilir ve yüzdeye payda olur.

## 3. Doğrulanmış zemin

262 dosyanın tamamına karşı ölçüldü, varsayım değildir:

- Ortalamalar: SPINDEL 113,4 · X AXIS 123,6 · Y AXIS 107,4 · Z AXIS 107,4 ·
  M131 DEBI 212,9 · M131BASINC 101,5 · M08 DEBI 224,1 (her biri n=131).
- 10665'in `VIBRATION` kolonu **131/131 boştur**. Limit yuvası (170) dolu
  olsa bile tek bir değeri yoktur — taban hesabı bu yuvaya **giriş üretmez**,
  `csv_live.py:44`'ün özelliği hiç kurmaması ile aynı kural.
- `WINDOW = 120`, ünite başına 131 an var: çizilen pencere veri kümesinin
  tamamı DEĞİL. Ortalamayı pencereden almak ile dosyalardan almak bu yüzden
  aynı şey değildir — karar dosyalardır.

## 4. Tasarım

### 4.1 Backend — tabanı bir kez hesapla

Yeni saf modül `backend/app/sim/baselines.py`:

```python
def compute_baselines(moments: list[Moment]) -> dict[tuple[int, int], float]:
    """(ünite no, özellik yuvası) -> o yuvanın TÜM CSV değerlerinin ortalaması."""
```

Değeri olmayan yuva **giriş üretmez** (boş sözlük anahtarı yok). `csv_replay`
ingest görevi başlarken bir kez çağrılır — 262 küçük dosya, açılışta ~0,5 sn.
Sonuç `hub.apply_measurement` üzerinden `csv_live.apply_measurement`'a geçer.

### 4.2 Wire

`Feature` yeni alan alır:

```python
baseline: float | None = None   # camelCase: baseline
```

CSV özelliğinde `limit_level` ve `pct` **boş** kalır; `limits[]` ham CSV
limitlerini taşımaya devam eder. Promos3 yolunda hiçbir şey değişmez.

### 4.3 Frontend — eşiği tek yer hesaplar

Yeni `frontend/src/domain/esik.ts`:

```ts
export const SAPMA_VARSAYILAN = 10;
esik(f, sapmaPct)   // baseline != null ? baseline * (1 + sapma/100) : limitLevel
yuzde(f, sapmaPct)  // current / esik * 100
```

Hem referans çizgisi hem yüzde rozeti buradan okur. `baseline` yoksa
(Promos3) doğrudan `limitLevel`e düşer.

Sapma **adres çubuğunda** taşınır (`?sapma=`), kabuk onu `IzlemeBaglami` ile
ekranlara verir. Canlı/Alarmlar/Olaylar arasında gezinirken korunur çünkü
kabuğun `git`i sorguyu olduğu gibi taşır; "Değiştir" de aynı sorguyla
karşılamaya döner, yani seçilen yüzde alana geri yüklenir.

### 4.4 Dürüstlük

Türetilmiş çizginin etiketi **`Limit (ort. +%10)`** olur; telden gelen gerçek
eşikte düz `Limit` kalır. Bunu yazmadan bırakmak, hesaplanmış bir çizgiyi
üreticinin koyduğu eşik gibi okutur — karşılama ekranındaki dört durumlu
rozetin izlediği kuralın aynısı.

Karşılama ekranındaki alanın ipucu da kapsamı söyler: sapmanın **yalnız CSV
kaynaklı tezgahları** etkilediği yazılır.

**Eşik sayıyla da yazılır** — §6'dan sonra bu yazı BANDI gösterir
(`Bant 179,2 – 246,5 · ortalama 224,1 −%20 / +%10`).
Uygulama sırasında ölçüldü: paketin `LineChart`ında `yDomain` prop'u
yok (dosya başındaki EKSEN NOTU) ve Recharts, otomatik ölçeklenen alanın
DIŞINDA kalan referans çizgisini sessizce atar. M08 DEBI'de %10 sapmada çizgi
duruyor (246,5), %40'ta kayboluyor (313,7) — iz 222–228 aralığında akarken
eksen 240'ta bitiyor. Kaybolan çizgi "limit yok" diye okunurdu; sayı orada
durdukça o yanlış okuma olmaz.

## 5. Doğrulama

- `cd backend && uv run pytest` — yeni `test_baselines.py`, genişletilmiş
  `test_csv_live.py`.
- `cd frontend && bun run lint` (eslint + `tsc --noEmit`).
- Gözle: `.\basla.bat`, LAN IP'sinden `tesis-a/tezgah-3` → M131 DEBI çizgisi
  50'den 234,1'e çıkar, rozet ortalamada ~%91 okur.

## 6. Alt sınır (aynı gün eklendi)

Tek eşik BANDA dönüştü. Hesap mantığı aynı, ikinci bir sapmayla:

    üst = ortalama × (1 + sapma/100)      varsayılan %10  → ort. × 1,10
    alt = ortalama × (1 − altSapma/100)   varsayılan %20  → ort. × 0,80

**Backend'e hiç dokunulmadı.** `baseline` zaten ham ortalamadır ve iki sınır da
ondan türer; değişen yalnız ekrandır.

| Konu | Karar | Gerekçe |
|---|---|---|
| Alt sınır kimde var | **Yalnız CSV** (tabanı olan özellik) | Promos3'te limit ALT+ÜST bandı DEĞİL, tipli TEK eşiktir (`domain.py`, Limits tablosu). Tek sayıdan alt sınır türetmek telin söylemediğini söylemek olurdu |
| Adres anahtarı | `sapma` (üst) korunur, `altSapma` eklenir | `ustSapma`/`altSapma` simetriği daha okunur olurdu ama aynı gün yayınlanmış adresleri kozmetik bir sebeple kırardı |
| Yüzde rozeti | ÜST sınıra göre kalır | Alt sınırın gelmesi "%"in anlamını değiştirmez |
| İhlal gösterimi | Ayrı rozet: "üst limit üstünde" / "alt limit altında" | Tek başına kırmızı bir "%75" okunamazdı; renk tek başına bilgi taşımaz |
| Sınıra değmek | İhlaldir (`>=` üst, `<=` alt) | Eski davranış `pct >= 100` idi; alt uç simetrik olmalı |

### Alt çizgi NEDEN ÇİZİLMİYOR

Paketin `LineChart`'ı **tek** referans çizgisi alır:

```ts
referenceLine?: ChartReferenceLine   // dizi DEĞİL
```

Üst ve alt aynı anda çizilemez. Üst çizilir, alt grafiğin altındaki **bant
yazısında** yaşar: `Bant 179,2 – 246,5 · ortalama 224,1 −%20 / +%10`.

Bu, EKSEN NOTU'nda tasarım sistemine açılan isteğin (`yDomain` +
`referenceLine[]`) ikinci yarısıdır. Kurulu sürüm **11.1.0**, yayınlanmış son
sürüm **12.4.1** — 12.x'in bunu getirip getirmediği DOĞRULANMADI; bir ana sürüm
yükseltmesi her ekranı ilgilendirir ve kendi işidir.

### Doğrulama (ölçüldü)

- Alt ihlal: `altSapma=0` ile X AXIS 76 → `%55,9` + "alt limit altında";
  SPINDEL 114 (ortalama 113,4) rozet ALMAZ — sınır doğru yerde.
- Üst ihlal: `sapma=0` ile SPINDEL 114 → `%100,5` + "üst limit üstünde",
  X AXIS 145 → `%117,3`; aynı anda Y AXIS 97 rozet almaz (`altSapma=100`,
  alt sınır 0) — yanlış yönde ihlal üretilmiyor.
