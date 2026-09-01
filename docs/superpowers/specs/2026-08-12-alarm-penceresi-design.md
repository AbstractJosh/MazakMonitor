# Alarmlar gezinmeden çıkıyor, sağ alta yerleşik pencereye giriyor — tasarım

Tarih: 2026-08-12
Durum: onaylandı

## 1. Amaç

Sol gezinmedeki **Alarmlar** sekmesi kalkar; yerine ekranın **sağ altında**
duran, açılıp kapanan bir alarm penceresi gelir.

Alarmlara bugün **dört** ayrı kapı var ve biri zaten yüzen bir aktif-alarm
listesi:

| # | Kapı | Yer |
|---|---|---|
| 1 | Sol gezinme "Alarmlar" | `uygulama-kabugu.tsx:40` |
| 2 | KPI kutucuğu "Alarmlar ekranına git" | `canli-route.tsx:152-154` |
| 3 | Kırmızı bant "Alarmları gör" | `canli-route.tsx:208-209` |
| 4 | Üst bardaki zil + Popover | `uygulama-kabugu.tsx:270-316` |

Bu iş 1'i kaldırır, 4'ü pencereye dönüştürür, 2 ve 3'e dokunmaz.

## 2. Kilitlenen kararlar

| Konu | Karar | Gerekçe |
|---|---|---|
| Tam ekran ızgara | **KALIR** (`/alarmlar` rotası durur, yalnız gezinmeden çıkar) | 11 kolon + dışa aktarma + kolon seçici + sıralama + toplu onay bir köşe penceresine sığmaz. Sığdırmaya çalışmak çalışan bir ekranı bozardı |
| Pencerenin içeriği | Aktif alarmlar, satır başına tek dokunuş onay, altta "Tümünü gör →" | Pencere TRİYAJ değil FARKINDALIK aracıdır; triaj tam ekranda kalır |
| Üst bardaki zil | Popover'ı bırakır, pencerenin **açma/kapama düğmesi** olur | İki ayrı yüzen aktif-alarm listesi aynı şeyi iki biçimde gösterirdi |
| Nerede görünür | Kabukta — Canlı ve Olaylar ekranlarında | Alarm bir ekranın değil TEZGAHIN durumudur |
| Bileşenler | `Card` + `Accordion` + `ScrollArea` + `Badge` + `IconButton` | Paket dışı bileşen yazılmaz (CLAUDE.md). `OzellikKutucugu`'nun (`canli-route.tsx:350-419`) birebir aynı deseni |
| Animasyon | **Yeni CSS YOK** — mevcut `mzi-akordiyon` yaması kullanılır | HAREKET bloğuna dördüncü kural eklemek, zaten kapatılmış bir boşluğu ikinci kez yamamak olurdu |
| Yığın katmanı | `z-[var(--layer-nav)]` (40) | İçeriğin ve yapışkan tablo başlığının (10/20) ÜSTÜ, modal (100) / popover (150) / toast (200) ALTI. Ham sayı değil token |
| Boş durum | `baglantiBoslugu(live.link, live.source)` | Zincir kopukken "0 aktif alarm" bir GÜVENCE cümlesidir ve arkasında kanıt yoktur |

### Kapsam dışı (açıkça)

- `alarmlar-route.tsx` **hiç değişmez** — ızgara, kolonlar, dışa aktarma,
  filtre sekmeleri, boş durumları aynen kalır.
- Onay damgası yine istemcide ve bellekte (ADR-0004); tezgah değişince
  sıfırlanır (`key={machineId}`). Bu iş o davranışı değiştirmez.
- Olaylar ekranı ve `/olaylar` rotası.
- Pencerenin taşınabilir/yeniden boyutlandırılabilir olması. YAGNI: sabit
  köşe, iki hâl (açık/kapalı).

## 3. Tasarım

### 3.1 Yerleşim

Pencere `UygulamaKabugu` içinde, `<Outlet>`in yanında basılır: kabuk zaten
`alarms`, `active`, `onToggleAck`, `onAckAll` ve `live`i elinde tutuyor, yani
yeni bir veri yolu gerekmez.

Yeni dosya: `frontend/src/features/alarmlar/alarm-penceresi.tsx`.

`MENU`den `alarmlar` girdisi çıkar. **Rota `router.tsx`'te kalır** ve bir
detay sayfasına dönüşür: pencerenin altındaki bağlantıdan, KPI kutucuğundan
ve kırmızı banttan varılır.

Konumlama: `fixed left-4 right-4 bottom-[calc(var(--touch-target)+var(--space-4))]
kabuk:left-auto kabuk:bottom-4 kabuk:w-96`.

**Kırılım `kabuk`tur, `sm` DEĞİL.** Uygulama sırasında ölçüldü: paket
Tailwind'in `sm..2xl` ölçeğini SİLER (`theme-olcek.css:84`,
`--breakpoint-*: initial`) ve tek kırılım bırakır — `kabuk: 860px`, sol
gezinmenin alt tab bar'a döndüğü yer (ADR-0006). `sm:` yazmak hata vermez,
sessizce HİÇBİR kural üretmez; pencere tam genişlikte kaldı.

Aynı kırılımın ikinci sonucu: 860px altında alt kenar **alt tab bar'ındır**
(AppShell onu kendiliğinden basar, `min-h-[var(--touch-target)]`). Pencere o
yükseklik kadar yukarı çekilir, yoksa gezinmenin üstüne oturur.

Sol ve sağ AYRI verilir (`inset-x-*` kısayolu değil): kısayol ile `right-4`
aynı özelliği farklı yollardan yazar ve hangisinin kazandığı üretilen CSS
sırasına kalırdı.

Outlet sarmalayıcısı alt dolgu alır ki kapalı şerit son grafik kartının
üstüne oturmasın.

### 3.4 `/alarmlar`da pencere de zil de BASILMAZ

Uygulama sırasında ölçüldü: tam ekran ızgaranın üstünde duran pencere sağ
kolonları — Özellik, Limit, Aşım ve **İşlem** sütununu, yani onay
düğmelerinin durduğu yeri — örtüyordu. Zaten listenin TAMAMINA bakılan
ekranda aynı listenin yüzen bir özetini üstüne koymak hem tekrar hem engel.

Zil de aynı yerde basılmaz: `aria-controls` DOM'da olmayan bir öğeyi işaret
eder ve düğme hiçbir şey açmazdı.

### 3.2 Pencerenin söyledikleri

**Kapalı:** uyarı ikonu + "Alarmlar" + sayı rozeti.
**Açık:** aktif alarmlar (en yenisi başta), satır başına tek dokunuş onay,
altta `Tümünü gör →`.

Liste `ScrollArea maxHeight` ile kaydırılır — `maxHeight` verilmezse içerik
kutuyu büyütür ve kaydırma hiç olmaz (COMPONENTS.md uyarısı).

Zincir kopukken pencere **kendi olumlu cümlesini kurmaz**: `baglantiBoslugu`
ne diyorsa o basılır ve "Bu pencere alarm olmadığını SÖYLEMİYOR" eklenir.
Sayı rozeti de sayı yerine "?" gösterir. Gerekçe `baglanti-bosluk.ts`
başlığında: sıfır ile bilinmeyen ayrı iddialardır ve bu pencere her ekranda
sürekli durduğu için o farkı yutmanın en pahalı olduğu yerdir.

### 3.3 Zil

`Popover`/`PopoverTrigger`/`PopoverContent` bloğu (~46 satır) silinir.
`IconButton` kalır ve pencereyi açıp kapatır: `aria-expanded` +
`aria-controls` pencereyi işaret eder, erişilebilir adı aktif sayıyı taşımayı
sürdürür.

## 4. Bilinen sonuçlar

- `/alarmlar`'dayken gezinmede **hiçbir öğe seçili görünmez** (`MENU`de
  karşılığı yok). Detay sayfaları için olağandır; sayfa yine de biraz çıplak
  durur.
- Pencere sayfanın sağ alt köşesini kaplar. Kapalı hâli tek şerit olduğu ve
  outlet alt dolgu aldığı için içeriğin üstüne binmez.

## 5. Doğrulama

- `cd frontend && bun run lint` (eslint + `tsc --noEmit`).
- Gözle (LAN IP'sinden): sekme yok; pencere sağ altta; zil açıp kapatıyor;
  onay listeyi kısaltıyor; "Tümünü gör" `?tezgah`/`?sapma` koruyarak tam
  ekrana gidiyor; kaynaksız tezgahta (Tezgah 4) pencere "0" DEMİYOR.
