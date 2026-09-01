# Arayüzün @alp/design-system'e taşınması — tasarım

Tarih: 2026-08-10
Durum: onay bekliyor

## 1. Amaç

MazakMonitor arayüzünün tamamı `@alp/design-system` v11.1.0 üzerine yeniden
kurulur. antd ve `frontend/src/alp-ui-shim/index.tsx` silinir. **Davranış
korunur, işaretleme korunmaz.**

Veri katmanı (`domain/`) bu göçün dışındadır: SSE hook'u, tel sözleşmesi,
tipler, tesis kataloğu ve `initialLiveState()` **hiç değişmez**. Yalnız
`domain/format.ts` (ton sözlüğü + elle biçimleme) ve `domain/ConfidenceTag.tsx`
yeniden yazılır.

## 2. Kilitlenen kararlar

| Konu | Karar | Gerekçe |
|---|---|---|
| Kapsam | UI + kabuk + routing; veri akışına dokunulmaz | Çalışan SSE mantığını yeniden yazmak davranış farkı riski doğurur |
| Paket | `@alp/design-system@11.1.0` | `@alp/ui` **hiç yayınlanmadı**; registry'de yok |
| Ekran bağlamı | Yalnız masaüstü tarayıcı | DS varsayılanları geçerli: 1200px merkezli, normal yoğunluk, fare hedefleri |
| Ürün adı | `Mazak İzleme` | `mazak-izleme-frontend` ile tutarlı; ayrı bir üründür |
| Paket yöneticisi | bun kalır | Proje CLAUDE.md'si sabitliyor; kurulum doğrulandı |
| React | 18'de kalır | Peer `>=18`; sürüm yükseltmesi bu göçe karıştırılmaz |
| Grafik ekseni | DS'ten `yDomain` istenir, ara çözüm açık etiket | Bkz. §6.1 |
| Alarm dock | Sayfa üstü `Alert` + çan `Popover` | Bkz. §6.2 |

### Kapsam dışı (açıkça)

TanStack Query, orval, auth/`LoginScreen`, `list-params`, `serverSide`
DataGrid, React 19. Şablonun geri kalanı "tutarlılık olsun" diye
alınmayacak — sorgulanacak REST yüzeyi yok, akış SSE.

## 3. Doğrulanmış zemin

Şu maddeler kurulu tarball'a karşı bizzat doğrulandı, varsayım değil:

- `bun add @alp/design-system` iç registry'den çalışıyor. Üç koşul:
  `bunfig.toml` → `[install.scopes]` token'ı, `NODE_EXTRA_CA_CERTS` → süresi
  geçmemiş kök CA paketi, EPERM'de bir kez tekrar (üçü de `kur.bat`'ta zaten var).
- Paket şunları shipliyor: `dist/styles.css` (56,5 KB), `charts`, `screens`,
  `blocks`, `COMPONENTS.md`, `alp-setup` binary.
- Bileşenler mevcut: `AppShell` `PageShell` `Section` `Card` `KPIStrip`
  `KPICard` `DataGrid` `CompactList` `Accordion` `Alert` `Badge` `Toggle`
  `Combobox` `Select` `Field` `Input` `Popover` `Drawer` `Dialog` `Tabs`
  `Timeline` `KeyValue` `EmptyState` `Skeleton` `Tooltip` `IconButton`
  `ToasterProvider`/`useToast` `Sparkline` `BulletChart` `RadialProgress`.
- Prop'lar mevcut: `rowTone` `refreshing` `disabledReason` `persistKey`
  `themeControls` `banded` `pinnedLeft` `rowDetail` `getRowId` `emptyState`
  `onRowActivate` `referenceLine` `yTickFormatter` `maxHeight` `defaultHidden`.
- Yardımcılar: `formatNumber` `formatDate` `formatDateTime` `formatRelative`
  `thresholdTone`/`thresholdLevel`/`thresholdColor` `token` `IKON` `useFlash`
  `useCountUp` `trFoldIcerir` (`/fold` alt yolu).

**Doğrulamada düzeltilen iki nokta:** `ChartReferenceLine.tone` kapalı listesi
`'target' | 'warn' | 'crit'` (`'danger'` yok) ve `referenceLine` **tekildir,
dizi değildir**.

## 4. Mimari

```
src/
  main.tsx                     StrictMode > ToasterProvider > RouterProvider
  app/
    app.css                    @import tailwindcss + @alp/design-system/theme.css
    router.tsx                 rotalar, lazy feature yükleme
    uygulama-kabugu.tsx        AppShell + SSE hook + <Outlet/>
  features/
    tezgah/routes/tezgah-route.tsx
    canli/routes/canli-route.tsx
    alarmlar/routes/alarmlar-route.tsx
    olaylar/routes/olaylar-route.tsx
  domain/                      DEĞİŞMEZ (format.ts + ConfidenceTag.tsx hariç)
```

Rotalar: `/canli` (varsayılan) · `/alarmlar` · `/olaylar` · `/tezgah`.
Seçili tezgah URL'de taşınır (`/canli?tezgah=tesis-a/tezgah-1`) — yenileme ve
geri tuşu çalışır, kiosk deep-link'lenebilir olur.

**Karşılama ekranı kalkar (operatörün göreceği değişiklik).** Kimlik doğrulama
olmadığı için panodan önceki zorunlu tık, işi olmayan bir adımdır. Yerine:
lazy rota çözülürken `SplashScreen` (paketten, çatallanmadan), kayıtlı tezgahla
doğrudan `/canli`, tezgah seçilmemişse `/tezgah`'a yönlendirme. Tema anahtarı
da böylece kabuğa taşınmış olur — bugün üç ayrı çağrı yerinde duruyor.
*Bu madde ayrıca onay ister; kiosk açılış ekranı ürün kararıysa korunabilir.*

**Akış kabukta yaşar.** `useLive` `uygulama-kabugu.tsx` içinde, `<Outlet/>`
üstünde durur; ekran değiştirmek bağlantıyı da biriken olayları da düşürmez.

## 5. İşlevsel sözleşme (kabul ölçütü)

Şim silinmeden önce her madde gösterilebilir olmalı.

### 5.1 Veri ve bağlantı — regresyon yasak
- Tek `EventSource`, `/api/stream`. REST yok, polling yok, simülasyon yok.
- Olaylar: `state` → `liveStateFromWire`, `status` → link durumu, `ping` yok sayılır.
- Yeniden bağlanma yalnız `readyState === CLOSED` iken, 5 sn sonra.
- Link türetimi: `!esOpen → stream-down` · `status.connected → ok` · aksi
  `source-down` · kaynaksız tezgah → `no-source`.
- `dataLive = connected && (wire.parsed ?? 0) > 0` — açık soket tek başına
  "veri akıyor" demez.
- Duraklat bağlantıyı kapatır **ve son kare ekranda kalır**; olay geçmişi de durur.
- Tezgah değişimi: onaylar, grafik adları, açık grafikler ve duraklatma sıfırlanır.
- Kaynaksız tezgah modül seviyesinde boş durum gösterir — başka tezgahın verisi
  asla başka bir ad altında görünmez.

### 5.2 Gezinme
- Üç içerik ekranı tek gezinmeden erişilir: Canlı İzleme · Alarmlar · Olaylar.
  Varsayılan Canlı İzleme.
- Tezgah seçimi her an kabuktan erişilebilir ("Değiştir").
- Tezgah seçilmemiş ilk açılış boş panoya değil, seçim ekranına düşer.

### 5.3 Canlı İzleme
- Altı ölçüm: Çevrim · İş Parçası · Bağlı Ünite (`online/total`) · PLC Girişleri
  · PLC Çıkışları · Aktif Alarm.
- PLC değerleri ikili ve onaltılık yan yana (`0110 (0x6)`); **bit sırası
  doğrulanmadı** notu kalır.
- Grafik sayısı ve adları tamamen telden gelir; önceden tanımlı grafik yok.
- Grafikler varsayılan kapalı, tek tek açılır; açılınca içerik aşağı iter,
  üstüne binmez.
- "Tümünü aç" / "Tümünü kapat", uçlarda `disabledReason` ile pasif.
- Pahalı örnek→nokta dönüşümü **yalnız açık grafikler** için koşar.
- Grafik yeniden adlandırma: `maxLength 40`, boş kayıt `Grafik N`'e döner,
  Escape iptal eder, aynı anda tek düzenleyici, tezgah başına.
- Limit çizgisi **yalnız gerçek `limitLevel` varken** çizilir. Yüzde yalnız
  `pct` varken görünür.
- `truncated` izler görünür "kırpık iz" uyarısı taşır.
- Ünite şeridi: her alan yalnız varsa basılır; hiç ünite yoksa **hiçbir şey**
  basılmaz.
- Boş özellik listesi → açık boş durum; toplu çubuk ve ızgara basılmaz.

### 5.4 Alarmlar
- Aktif / Tümü / Onaylanmış; **varsayılan Aktif**.
- Kolonlar: Zaman · Durum · Cihaz · Olay · Kanal · Çevrim · Özellik · Limit ·
  Aşım · İşlem.
- Satır başına onayla **ve onayı geri al**; tek dokunuş, geri alınabilir,
  **onay diyaloğu yok**.
- Onaylanan kayıt asla silinmez.
- Aşım ham sayım basar (`204 / 170 ham`), ölçeklenmiş değer değil.

### 5.5 Olaylar
- Olay başlığı + iş parçası üzerinde serbest metin arama.
- Olay kodu ve ünite filtreleri **akışta görülen değerlerden türetilir**.
- Canlı sonuç sayısı filtrelerin yanında.
- Kolonlar: Zaman · Olay · Ünite · Kanal · Olay No · İş Parçası. Hex kod yalnız
  `code` ve `codeLabel` birlikte varsa.

### 5.6 Kesişen dürüstlük kuralları
- `no-source` duraklatma etiketinden **önce** duyurulur — arıza değil, yapılandırma.
- Eksik değer `—` basar, asla tahmin etmez.
- `confirmed` olmayan her şey güven uyarısı taşır; `confirmed` işaret taşımaz.
- Üç ayrı yokluk sözlüğü ayrı kalır: boş durum · hiçbir şey · `—`.
- Onaylama istemci tarafı "görüldü" damgasıdır; donanıma yazılmaz, yıkıcı değildir.
- Tek dil Türkçe; sayı `1.234,5`, tarih `GG.AA.YYYY SS:dd`, 24 saat.
- Her ikon-only kontrolün erişilebilir adı vardır.

## 6. Çatışmalar ve çözümleri

### 6.1 LineChart'ta y-ekseni alanı yok (en yüksek sonuçlu madde)

**Durum:** `LineChartProps` sekiz prop taşır; `yDomain`/`yAxis`/`domain` yok.
`referenceLine` tekildir ve limit çizgisine ayrılmıştır. Bugün ham sayım izleri
sabit 0–255 ekseninde çiziliyor ve bu bir **emniyet** özelliği: 128±2'de düz
duran bir iz, otomatik ölçekte tam skala salınım gibi görünür.

**Karar:**
1. Tasarım sistemine `yDomain` + `referenceLine[]` isteği açılır (doktrinin
   kendi kuralı: bu bir ihlal değil, eksik bileşen bildirimidir).
2. Ara çözüm: ham izler otomatik ölçekte çizilir **ama** grafik başlığı açıkça
   "otomatik ölçek" der ve o anki eksen aralığı okunur biçimde basılır. Yalan
   söylemeyen, geçici olduğu belli bir durum.
3. Kabul testi: 128±2 düz bir iz beslenip ekranda düz göründüğü — ya da
   ölçeğin açıkça etiketlendiği — elle doğrulanır.

**Kabul edilen ikinci fark:** şim sonlu olmayan noktalar arasında çizgiyi
birleştiriyor (boşlukları köprülüyor); recharts çizgiyi varsayılan olarak
kırıyor. Bu bir dürüstlük **iyileşmesidir**, kabul edilir, sürüm notunda söylenir.

### 6.2 Sabit alarm dock'unun yeri yok

**Durum:** `position:fixed` + `z-index:900` + 50vh + localStorage'lı panel DS
deseni değil; katman ölçeğiyle ve "kabuk tek yerde yaşar" kuralıyla çatışıyor.

**Karar:** Canlı İzleme'nin üstünde `Alert` — aktif alarm varsa
`tone="danger"` (`"3 aktif alarm"` + "Alarmları gör"), yoksa `tone="success"`
(`"Aktif alarm yok"`). Hızlı onay listesi üst bardaki çan `Popover`'ında kalır.
localStorage açık/kapalı anahtarı dock'la birlikte gider.
**Bu operatörün gördüğü bir değişikliktir ve onaylandı.**

### 6.3 `Section` ad çakışması

Şim `Section` = antd `Card` (yüzey). DS `Section` = kenarlıksız başlıklı
gruplama. Mekanik değiştir-bul, lint'ten geçen ama bozuk görünen kenarlıksız
"kartlar" üretir. **Önlem:** yedi çağrı yeri paket kurulmadan **önce** `Card`
olarak yeniden adlandırılır.

### 6.4 Ton sözlüğü kırılması

Şim tonları `success|error|warning|processing|default` → Badge tonları
`neutral|navy|sky|success|warning|danger`. `format.ts` içinde eşlenir:
`error→danger`, `processing→sky`, `default→neutral`. Dışa aktarılan tip
`Tone → BadgeTone` olarak yeniden adlandırılır ki yanlış değer çalışma anında
nötr rozet değil, **tip hatası** olsun. `dot` her zaman verilir — renk tek
başına anlam taşımaz.

### 6.5 Opaklık kalıcı hiyerarşi kurmaz (ADR-0039)

Onaylanmış alarm satırlarındaki `opacity: 0.5` → `rowTone={a => a.state ===
'acknowledged' ? 'muted' : undefined}`.

### 6.6 Ham px/hex ve elle biçimleme

`ALARM_DOCK_*`, `TILE_CHART_HEIGHT`, `maxWidth: 460`, `borderRadius: 999`,
`transition: "opacity 0.3s ease"` ve benzerleri token'a döner ya da bileşenin
içinde kaybolur. **Tuzak:** sayısal inline stil (`width: 320`) string-literal
lint'inden kaçar ama doktrini yine ihlal eder.

`pctText`/`peakText` `formatNumber` üstüne yazılır. **`dayjs` bağımlılıktan
çıkar** (`dayjs.locale('tr')` global mutasyonu da onunla gider). `time` alanları
**an**'dır — `formatCalendarDay` bu alanda kullanılmaz.

### 6.7 Gerekçesiz `disabled` (ADR-0082)

"Tümünü aç" / "Tümünü kapat" / "İzlemeye başla" → `disabledReason`.

### 6.8 Tailwind tema köprüsü sessizce başarısız olur

Köprü kurulmazsa hata da uyarı da yok: `navy`/`steel`/`surface` utility'leri
hiç üretilmez, `sky` Tailwind'in varsayılan mavisine düşer. **Doğrulama adımı
zorunlu:** derlenmiş CSS `.bg-sky-600{background-color:var(--sky-600)}`
içermeli.

### 6.9 `<html lang="tr">` kozmetik değil

Olmazsa her büyük harf mikro-etiket "LISTESIZ" basar. Font hatası gibi görünür,
locale hatasıdır.

### 6.10 Yol boyu düzeltilecek gerçek hata

`deviceTitle` `serialNo` arıyor ama `Alarm` `deviceSerial` taşıyor — alarm
satırlarında `SNr …` **hiç görünmemiş**. Görünür çıktıyı değiştirdiği için
sürüm notunda söylenir, sessizce geçilmez.

## 7. Altyapı

**package.json** — ekle: `@alp/design-system@^11.1.0`, `lucide-react`,
`recharts@^2` (v3 DEĞİL — paket 2.x'e karşı derlenip test edilmiş),
`react-router-dom@^7.1`, `tailwindcss@^4`, `@tailwindcss/vite@^4`, eslint
takımı. Çıkar: `antd`, `@ant-design/icons`, `dayjs`.

**Registry** — `frontend/.npmrc` (token'sız, commit'lenir) zaten doğru.
Token `bunfig.toml` `[install.scopes]` içinde, **commit edilmez**. `kur.bat`'a
eklenir.

**vite.config.ts** — `@alp/ui` alias'ı **silinir**, `@/*` alias'ı gelir,
`tailwindcss()` plugin'i eklenir. `/api` proxy'si aynen kalır. `vitest.config.ts`
ayrı dosya kalır (aksi halde `vite build` vitest'e bağlanır ve IIS deploy'unda
budanmış devDependency'lerle kırılır).

**tsconfig.json** — `@alp/ui` path'i silinir, `moduleResolution: "bundler"`
zorunlu (paket subpath export'ları shipliyor).

**CSS sırası yük taşır** — `main.tsx` içinde önce
`@alp/design-system/styles.css`, sonra `./app/app.css`.

**Fontlar** — Inter + IBM Plex Mono `styles.css` içinde geliyor. `index.html`'e
font linki **konmaz**, `@font-face` yazılmaz.

**ESLint iki dosya** — `eslint.config.mjs` (error) + `eslint.adherence.mjs`
(warn). Tek koşuda iki severity taşınamıyor. Kural metinleri paketten import
edilir, kopyalanmaz. Error katmanı antd/@ant-design/@radix-ui/styled-components
importunu, ham `<input>/<select>/<textarea>/<form>/<dialog>`'u ve ham
hex/px/arbitrary Tailwind'i keser. **Şim bu katman olmadan silinirse antd geri
sızar.** CI yok; zorlama `husky` pre-push ile yerel.

**CLAUDE.md güncellenir** — `@alp/ui` → `@alp/design-system`; kılavuz işaretçisi
`frontend/node_modules/@alp/ui/AI-KULLANIM.md` → `.claude/skills/alp-design-system/SKILL.md`
+ `COMPONENTS.md`; `/arayuz` komutunun hedefi; `bun run lint` artık `tsc` değil.

**Silinen/bölünen dosyalar**

| Yol | Akıbet |
|---|---|
| `src/alp-ui-shim/index.tsx` | silinir (809 satır) |
| `src/App.tsx` | bölünür → `app/main.tsx`, `app/router.tsx`, `app/uygulama-kabugu.tsx` |
| `src/screens/*.tsx` | → `features/<ad>/routes/<ad>-route.tsx` |
| `src/domain/{types,live,backend,useLive,useBackendLive,facilities}.ts` | **değişmez** |
| `src/domain/format.ts` | ton eşlemesi · `formatNumber` · `deviceTitle` düzeltmesi |
| `src/domain/ConfidenceTag.tsx` | `Badge` üstüne yeniden yazılır |

**Başlamadan önce:** `App.tsx`'teki commit'lenmemiş fark
(`"Veri Akıyor"` → `"Veri Akışı Aktif"`) commit'lenir ya da atılır — göç o
dosyayı zaten yeniden yazıyor.

## 8. Riskler

| # | Risk | Önlem |
|---|---|---|
| 1 | Ham izler sessizce otomatik ölçekleniyor (§6.1) | Açık "otomatik ölçek" etiketi + DS isteği + düz-iz kabul testi |
| 2 | Push akışı altında DataGrid çalkantısı: backend her karede tam anlık görüntü yayınlıyor; naif bağlama her tikte satırları yeniden kurar, operatörün okuduğu satır parmağının altından kayar | Kararlı `getRowId`; `rows` tam girdilere memoize; **`refreshing`, asla `loading`**; çalkantı sürerse yeni satırlar "N yeni kayıt" arkasında tamponlanır. Gerçek tezgahla test edilir, fixture'la değil |
| 3 | Tema köprüsü eksik → sessizce marka dışı | Derlenmiş CSS grep'i DoD maddesi |
| 4 | Türkçe sayı/tarih regresyonu | `format.ts` önce test edilir: `1234.5 → "1.234,5"`, `null → "—"` |
| 5 | Ton eşlemesi ciddiyet anlamını kaybeder | `BadgeTone` tip adı + 16 `statusCode` değerinin tablo testi |
| 6 | Lint meşru sabitlerde göçü tıkar | Token süpürmesi **ilk ve ayrı commit**; her disable yazılı gerekçe taşır; **aynı gerekçenin üçüncüsü** eksik bileşen bildirimidir |
| 7 | Kiosk tıklama alanı küçülür | `AccordionTrigger` kart genişliğini kaplar; hedef dolguyla büyütülür, glif büyütülmez |
| 8 | `recharts` yanlış sürüm | `^2` pinlenir; recharts'sız bileşenler (`Sparkline`, `BulletChart`, `RadialProgress`) ana girişten alınır |
| 9 | Güven açıklaması yalnız hover'da kalır | Kolon `hint`'i + satır `Drawer`/`KeyValue` |
| 10 | Zorlama yalnız yerel (CI yok) | `bun run verify` pre-push'ta **ve** CLAUDE.md'de belgeli merge öncesi adım |

## 9. Doğrulama

`bun run verify` = `lint` (eslint + adherence) → `typecheck` → `test` →
`check:dx` (`bunx alp-setup --check`) → `build`.

Ek elle kontroller: derlenmiş CSS token grep'i · `<html lang="tr">` ·
düz ham iz görünümü · gerçek tezgahla DataGrid çalkantısı · koyu tema.
