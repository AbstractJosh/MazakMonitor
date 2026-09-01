# CSV tekrar-oynatma simülatörü ve yerel ölçüm veritabanı — tasarım

Tarih: 2026-08-11
Durum: onay bekliyor

## 1. Amaç

`verı.zip` ile gelen 262 Provis ölçüm CSV'sini **yerel bir veritabanına** yazan
ikinci bir simülatör kurulur ve `basla.bat`'a kendi modu eklenir.

Bugün projede **hiç tablo yok**: `0e4a34448ddb_baslangic.py` boştur, tüm canlı
durum `hub.py` içinde bellektedir. Yani bu iş iki şeyi birden getirir — ilk
gerçek şema ve onu dolduran ilk yazıcı.

Mevcut `promos3_sim.exe` ile karıştırılmamalıdır: o **tel biçimini** üretir
(UDP 1789 → `hub` → SSE → ekran), bu ise **ölçüm satırı** üretir (CSV → SQLite).
İki yol birbirine dokunmaz.

## 2. Kilitlenen kararlar

| Konu | Karar | Gerekçe |
|---|---|---|
| Veritabanı | SQLite dosyası, `veri/mazak.db` | Bu makinede PostgreSQL kurulu değil; sıfır kurulumla `.bat` çift tıklanabilir kalsın. SQLAlchemy + Alembic aynı kaldığı için Postgres'e geçiş ucuz |
| Sim davranışı | Döngüsel canlı tekrar oynatma | `basla.bat`'taki "mod" kavramının karşılığı budur; `promos3_sim.exe --stream`'in DB eşleniği |
| Zaman damgası | `recorded_at` = **şimdi**, `source_time` = CSV'nin kendi zamanı | Ekran hep taze veri görür, ikinci koşum çakışmaz, orijinal zaman da kaybolmaz |
| Kapsam | CSV → DB + salt okunur teşhis ucu | "Yazdım" demenin kanıtı aynı fazda üretilsin |
| Şema | 3 tablo (ölçüm / özellik / limit) | İki ünitenin özellik adları farklı; "her özelliğe bir kolon" tek tabloda toplanamaz |
| CSV konumu | Depoda `veri/<ünite>/`, zip silinir | `verı.zip` adındaki noktasız `ı` yol/kodlama tuzağı |

### Kapsam dışı (açıkça)

- **Frontend'e hiç dokunulmaz.** Tek satır React/CSS/token değişmez;
  `@alp/design-system` kullanımı ve tasarım dili aynen kalır. Teşhis ucu
  yalnızca bir JSON endpoint'idir, ekranı yoktur.
- `hub`/SSE yolu DB'ye bağlanmaz. `/api/stream`, `/api/live`, `/api/events`,
  `/api/alarms` bugünkü gibi bellekten çalışmaya devam eder.
- Alarm/olay kalıcılığı (`main.py`'deki "kalıcılık DB'ye yazan faz ile gelir"
  notları) bu fazın işi değildir.
- PostgreSQL'e geçiş, çoklu tezgah, tesis/tezgah kataloğunun DB'ye taşınması.

## 3. Doğrulanmış zemin

Aşağıdaki maddeler 262 dosyanın **tamamına** karşı ölçüldü, varsayım değildir:

- BOM **yok**, satır sonu **CRLF**, ayraç `;` (değerler boşlukla sarılı),
  veri satırında **41 kolon**.
- `Program = 0`, `Channel = 1`, `Cut = 0`, `File version = 1` — 262/262 sabit.
- `Start date == End date` — 262/262.
- Başlıktaki `Tool` değeri dosya adındaki sıra numarasına eşit — 262/262.
- Veri satırındaki saat dosya adındaki saate eşit — 262/262.
- **Limit 5–8 yuvaları 262/262 boş.** Dolu olan yalnız Limit 1–4.
- Tarih/Saat dışındaki her dolu hücre tam sayıdır (ondalık yok).
- İki ünitenin dosya adları birebir aynıdır; sıra 11–143, **54 ve 99 her iki
  ünitede de eksiktir** (ünite başına 131 dosya).
- `VIBRATION` sütunu (10665) 131/131 boştur.
- Ünite klasörleri Provis'in `LastMonDataFile-10660` / `-10665` kimlikleridir
  (`promos3-c/report_combined.md:179`), yani sırasıyla 10659 ve 10663 seri
  numaralı izleme üniteleri.

## 4. Veri yerleşimi

`verı.zip` açılır ve depodan **silinir** (geçmişte kalır). Yerine:

```
veri/10660/000_01_00011_000_260810_112302.csv   … 131 dosya
veri/10665/000_01_00011_000_260810_112302.csv   … 131 dosya
```

Klasör adı ünite numarasıdır ve sim'in ünite kaynağı budur — dosya içinde
ünite bilgisi **yoktur**.

Dosya adı biçimi: `{program}_{kanal}_{takım}_{cut}_{YYMMDD}_{HHMMSS}.csv`

`.gitignore`'a eklenir:

```
veri/*.db
veri/*.db-wal
veri/*.db-shm
```

CSV'ler versiyonlanır (~210 KB düz metin, diff'lenebilir); veritabanı dosyası
versiyonlanmaz.

## 5. CSV biçimi ve ayrıştırma

Dosya 7 başlık satırı + boş satır + kolon satırı + **tek** veri satırıdır.

```
0  Program ; 0
1  Channel ; 1
2  Tool ; 11
3  Cut ; 0
4  Start date ; 2026-08-10 11:23:02.192
5  End date ; 2026-08-10 11:23:02.192
6  File version ; 1
7  (boş)
8  Time (s) ; Date ; Time ; Workpiece ID ; SPINDEL ; Work SPINDEL ; …
9  0 ; 10.08.2026 ; 11:23:02 ;  ; 115 ; 87 ; 89 ; 90 ; …
```

Veri satırı kolon dizilimi (0 tabanlı):

| İndeks | Alan |
|---|---|
| 0 | `Time (s)` |
| 1, 2 | `Date`, `Time` |
| 3 | `Workpiece ID` |
| 4–11 | 4 × (özellik değeri, `Work` değeri) |
| 12, 13 | `Alarm`, `Alarm limit` |
| 14–16 | `Teach-In`, `Setup`, `Rework` |
| 17–40 | 8 × (`Limit N`, `Limit type`, `Limit feature`) |

**Özellik adları kolon satırından okunur** (indeks 4, 6, 8, 10), koda gömülmez
— `config.py`'deki `promos3_feature_names` notunun aynı gerekçesi: adlar
kuruluma özeldir.

Ayrıştırıcı biçimi doğrular: kolon sayısı 41 değilse, `File version` 1
değilse ya da `Work <ad>` eşleşmesi tutmuyorsa dosya **atlanır ve loglanır**
— sessizce yanlış kolondan değer okumaktansa o anı hiç yazmamak yeğdir.

Boş hücre `None` olur, `0` **olmaz**. (Örn. `VIBRATION` boştur; `0` yazmak
"sensör 0 ölçtü" der ki yanlıştır.)

`source_time` başlıktaki `Start date`'ten alınır (milisaniye taşır);
veri satırındaki `Date`/`Time` ile tutarlılığı doğrulanır.

### Alınmayan kolonlar

`Teach-In`, `Setup`, `Rework` **şemaya girmez**: 262/262 boşturlar ve
CONTEXT.md sözlüğünde karşılıkları yoktur. Gerekçe `domain.py`'nin kendi
kuralıdır — *"hiçbir zaman dolmayacak bir alanı taşımak, ekranda kalıcı bir
'—' üretmekten başka işe yaramaz."*

`Workpiece ID` bu veride boş olmasına rağmen **tutulur**: CONTEXT.md'de
birinci sınıf kavramdır (*İş parçası*) ve gerçek veride dolar.

`Time (s)` de tutulmaz: tek satırlık dosyada değeri her zaman 0'dır ve
`source_time` zaten aynı bilgiyi taşır.

## 6. Şema

`backend/app/models.py` yeni dosya: `Base` (DeclarativeBase) + üç model.
`migrations/env.py`'de `target_metadata = None` satırı `Base.metadata`'ya
bağlanır — dosyanın kendi yorumu bu adımı zaten tarif ediyor.

Kolon adları İngilizcedir ve `domain.py` ile aynı sözcükleri kullanır
(`unit_no`, `channel_nr`, `feature_nr`, `lim_type`, `level`), böylece
CONTEXT.md'deki "Kod/kaynak" karşılıkları korunur.

### `measurement` — bir üniteden bir an

| Kolon | Tip | Not |
|---|---|---|
| `id` | int PK | |
| `recorded_at` | datetime, **indeksli** | Sim'in yazdığı an. **UTC, naive.** |
| `source_time` | datetime | CSV `Start date` (yerel, naive) |
| `unit_no` | int, **indeksli** | 10660 / 10665 — klasör adından |
| `channel_nr` | int | başlık `Channel` |
| `tool_nr` | int | başlık `Tool` |
| `program_nr` | int | başlık `Program` |
| `cut_nr` | int | başlık `Cut` |
| `workpiece` | str \| null | `Workpiece ID` |
| `alarm` | int \| null | |
| `alarm_limit` | int \| null | |
| `source_file` | str | dosya adı — izlenebilirlik |

`(unit_no, recorded_at)` bileşik indeksi: teşhis ucunun tek sorgu şekli budur.

### `measurement_feature` — an başına 4 satır

| Kolon | Tip |
|---|---|
| `id` | int PK |
| `measurement_id` | int FK → `measurement.id`, `ON DELETE CASCADE`, indeksli |
| `slot` | int, 1–4 |
| `name` | str — `SPINDEL`, `M131 DEBI`, … |
| `value` | float \| null — ham sayım |
| `work_value` | float \| null — `Work <ad>` |

### `measurement_limit` — an başına 0–8 satır

| Kolon | Tip |
|---|---|
| `id` | int PK |
| `measurement_id` | int FK → `measurement.id`, `ON DELETE CASCADE`, indeksli |
| `limit_nr` | int, 1–8 |
| `level` | float |
| `lim_type` | int \| null |
| `feature_nr` | int \| null — hangi özellik yuvasına ait |

Boş limit yuvaları satır **üretmez** (bu veride 5–8 hiç yazılmaz).

Bir "an" = 2 `measurement` + 8 `measurement_feature` + 8 `measurement_limit`
= **18 satır**.

### Migration

`uv run alembic revision -m "olcum tablolari"` ile tek yeni revizyon;
`0e4a34448ddb`'nin ardılı. Boş başlangıç revizyonu **silinmez** (uygulanmış
olabilir).

## 7. Simülatör

`backend/app/sim/` yeni paket. İki dosya, iki sorumluluk:

### `csv_reader.py` — saf ayrıştırıcı

`Path → MeasurementRecord | None`. DB bilmez, zaman bilmez, döngü bilmez.
`MeasurementRecord` bir dataclass'tır: başlık alanları + `list[FeatureValue]`
+ `list[LimitValue]`. Bozuk dosyada `None` döner (ve neden loglanır).

Tanımlayıcılar İngilizce, yorumlar Türkçedir — `domain.py` ile aynı düzen.

Ayrıca `read_moments(root: Path) -> list[Moment]`: `veri/` altını tarar,
ünite klasörlerini bulur, **dosya adına göre** eşleştirir (iki ünitede aynı
addır) ve zaman sırasına dizer. Bir üniteden eksik olan an, diğer ünite için
yine de yazılır.

### `replay.py` — CLI girişi

`uv run python -m app.sim.replay`

| Bayrak | Varsayılan | Anlam |
|---|---|---|
| `--csv-dir` | `settings.sim_csv_dir` | `veri/` kökü |
| `--period-ms` | `settings.sim_period_ms` (1000) | anlar arası bekleme |
| `--retention-min` | `settings.sim_retention_minutes` (60) | budama eşiği |
| `--once` | kapalı | tek geçiş yapıp çıkar (test/teşhis) |

Döngü: her periyotta sıradaki anı yaz (bir işlemde 18 satır), 131'in sonunda
başa dön. Her tam turda budama çalışır: `recorded_at < now − retention`
satırları silinir, çocuklar FK cascade ile gider.

Açılışta ekrana ne yazdığını basar: kaç an bulundu, hangi üniteler, DB yolu,
periyot. Sessiz koşan bir simülatör bu projede daha önce pahalıya patladı
(`basla.bat` madde 6).

**Budama neden var:** 1 sn periyotta saniyede 18 satır düşer (~65 bin
satır/saat). Sınırsız büyüyen bir dosya, geceyi açık geçiren bir koşumda
gigabaytlara çıkar.

## 8. Ayarlar (`config.py`)

- `database_url` **boşsa** SQLite varsayılanına düşülür:
  `sqlite+pysqlite:///<depo kökü>/veri/mazak.db` (yol `config.py`'den mutlak
  hesaplanır, çalışma dizinine bağlı değildir). `.env` verilirse o kazanır —
  `.env.example`'daki "gerçek değer .env'den gelir" niyeti bozulmaz.
  `pysqlite` stdlib'dir, **yeni bağımlılık yoktur**.
- `sim_csv_dir: str = ""` → boşsa `<depo kökü>/veri`
- `sim_period_ms: int = 1000`
- `sim_retention_minutes: int = 60`

`db.py` iki şey kazanır:

1. `settings.database_url` yerine yeni çözücüyü kullanır.
2. SQLite'a özel iki PRAGMA, bağlantı olayında:
   - `foreign_keys=ON` — **cascade budaması bunsuz sessizce çalışmaz**
     (SQLite varsayılanı kapalıdır).
   - `journal_mode=WAL` — sim yazarken teşhis ucu okuyabilsin. İki ayrı
     süreç aynı dosyayı açar; WAL olmadan okuma yazmayı kilitler.

## 9. Teşhis ucu

`GET /api/measurements`

| Parametre | Varsayılan | |
|---|---|---|
| `unit` | yok | 10660 / 10665 ile süz |
| `limit` | 50 | üst sınır 500 |

Cevap (camelCase, mevcut uçlarla tutarlı):

```json
{
  "total": 4712,
  "measurements": [
    {
      "id": 4712, "recordedAt": "...", "sourceTime": "...",
      "unitNo": 10665, "channelNr": 1, "toolNr": 143,
      "programNr": 0, "cutNr": 0, "workpiece": null,
      "alarm": null, "alarmLimit": null,
      "sourceFile": "000_01_00143_000_260810_123647.csv",
      "features": [{"slot": 1, "name": "VIBRATION", "value": null, "workValue": null}],
      "limits":   [{"limitNr": 1, "level": 170.0, "limType": 1, "featureNr": 1}]
    }
  ]
}
```

(Örnekte `features` ve `limits` dizileri kısaltılmıştır; gerçekte 4'er
elemanlıdır.)

`total` süzgece uyan **tüm** satır sayısıdır (`limit`'ten etkilenmez) —
"veri geliyor mu" sorusunun cevabı odur.

Sıralama `recorded_at DESC, id DESC`. Salt okunur; yazma ucu yoktur.

Kod yeri: `backend/app/measurements.py` (sorgu + cevap modelleri), `main.py`
yalnızca yolu bağlar. `domain.py`'ye dokunulmaz — o dosya frontend'in
`types.ts`'iyle birebir sözleşmedir ve bu fazda frontend değişmiyor.
Ortak `CamelModel` taban sınıfı `domain.py`'den içe aktarılır.

## 10. `basla.bat` yeni modu

```
.\basla.bat csv       (alias: veri)        menüde [3]
```

Menü üçe çıkar; 10 sn zaman aşımı varsayılanı **PROVIS olarak kalır**
(`choice /C 123 /D 1`).

Bu mod dört adım koşar:

1. `uv run alembic upgrade head` — **senkron**, backend'den önce. Tablolar
   yoksa sim ilk yazışta patlar.
2. `start "ALP Backend"` — teşhis ucu için.
3. `start "ALP Frontend"` — Vite.
4. `start "ALP CSV Sim" /D "%CD%\backend" cmd /k uv run python -m app.sim.replay`

Ortam: `PROMOS3_ENABLED=false`. Bu modda UDP dinleyicisi **hiç kurulmaz**;
izleme ekranları dürüstçe boş durur ve sentetik UDP verisiyle karışmaz.
`KAYNAK_AD` = `CSV SIM - veri klasoru, SQLite` (madde 7: içinde `>` geçmez).

**Vite neden açılıyor:** backend `127.0.0.1`'de kalır ve bu makinede Chrome
loopback'i göremez (madde 8, DLP eklentisi). Vite'ın vekili üzerinden
`http://<LANIP>:5173/api/measurements` tarayıcıda **açılır**. Banner doğrudan
o adresi açar, uygulama köküne değil — bu fazda ekranda gösterilecek yeni bir
şey yok, kökü açmak "çalışıyor" izlenimi verirdi.

Yeni hata etiketi `:yok_veri` — `veri\10660` yoksa açık mesajla durur.

`:durdur` bölümüne eklenir:

```
taskkill /FI "WINDOWTITLE eq ALP CSV Sim*" /T /F
```

Backend ve Vite gibi pencere başlığından öldürülür (ikisi de ada göre
öldürülemez: `python.exe` / `bun.exe`). PID dosyası tutulmaz: madde 4'teki
tuzak burada zararsızdır — kaçak bir CSV sim yalnız DB'ye yazar, ekranda
"gerçek sanılan" bir sayı üretmez.

PROVIS modundaki "simülatör açıkken başlama" kilidi CSV sim'i **kapsamaz**:
o kilit UDP 1789 çakışması içindir, CSV sim sokete dokunmaz.

Dosya CRLF satır sonlarıyla yazılır (mevcut `basla.bat` gibi).

## 11. Hata yönetimi

| Durum | Davranış |
|---|---|
| Bozuk/eksik CSV | Logla, o dosyayı atla, sim yaşamaya devam eder |
| `veri/` ya da ünite klasörü yok | Açık hata, sim çıkar; `basla.bat` da başlamadan önce kontrol eder |
| Tablolar yok | `alembic upgrade head` modun 1. adımıdır; yine de sim açılışta tabloyu yoklar ve eksikse ne yapılacağını söyler |
| SQLite `database is locked` | Kısa geri çekilme + yeniden dene (3 deneme), sonra o anı atla ve logla |
| Bir üniteden an eksik (54, 99) | Diğer ünite için satır yazılır; eksik olan sessizce atlanmaz, sayacı loglanır |

Sim asla ölmez; ölürse pencere kapanır ve kullanıcı sebebi göremez —
`basla.bat` madde 10'un aynı dersi.

## 12. Test

| Dosya | Kapsam |
|---|---|
| `tests/test_csv_reader.py` | Gerçek `veri/` dosyası → tüm alanlar; boş hücre `None`; `VIBRATION` `None`; limit 5–8 satır üretmez; bozuk dosya (yeni fixture `tests/data/csv/bozuk.csv`) `None` döner |
| `tests/test_replay.py` | Geçici SQLite'a `--once` bir geçiş → 131 an × 18 satır; budama eşiği aşan satırları siler ve çocukları da gider (FK pragma kanıtı) |
| `tests/test_api.py` | `/api/measurements` — boş DB'de `total: 0`; `unit` süzgeci; `limit` üst sınırı; iç içe `features`/`limits` |

`conftest.py` `DATABASE_URL`'i geçici bir dosyaya sabitler (`app.config` içe
aktarılmadan **önce**, `PROMOS3_ENABLED` ile aynı yerde). Testler
`veri/mazak.db`'ye asla yazmaz.

## 13. Kabul ölçütleri

1. `.\basla.bat csv` → üç pencere açılır (`ALP Backend`, `ALP Frontend`,
   `ALP CSV Sim`; 1. adım olan `alembic upgrade head` başlatıcı penceresinde
   senkron koşar, kendi penceresi yoktur) ve tarayıcı
   `http://<LANIP>:5173/api/measurements` adresini gösterir ve `total` her
   yenilemede artar.
2. `veri/mazak.db` oluşur; 131 an sonra sayaç başa döner, satır yazımı durmaz.
3. `.\basla.bat dur` → CSV sim penceresi de kapanır; `total` artmayı durdurur.
4. `cd backend && uv run pytest` — tamamı geçer.
5. `cd frontend && bun run lint` — **değişmediği için** geçmeye devam eder
   (frontend'e dokunulmadığının kanıtı).
6. `git status` → `frontend/` altında hiçbir değişiklik yok.

## 14. Sonra ne gelir

- Ölçümlerin ekranda gösterilmesi (bu faz **değil**): `hub`/SSE yolu mu
  kullanılacak yoksa ayrı bir REST/sayfa mı — ayrı bir tasarım kararı.
- Alarm ve olay kalıcılığı aynı şemaya bağlanır.
- PostgreSQL'e geçiş: `DATABASE_URL` verildiği anda kod yolu aynıdır; yalnız
  migration'ın SQLite'a özel bir şey içermediğinin doğrulanması gerekir.
- Gerçek Provis'ten sürekli CSV alımı (klasör izleme) — sim'in yerini alır.
