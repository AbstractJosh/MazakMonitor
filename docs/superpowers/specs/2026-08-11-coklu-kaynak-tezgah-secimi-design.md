# Çoklu kaynak ve karşılama ekranı — tasarım

Tarih: 2026-08-11
Durum: onay bekliyor

## 1. Amaç

İki iş bir arada yapılır:

1. **Karşılama ekranı.** Uygulama artık doğrudan izlemeye düşmez; açılışta
   kullanıcı **tesis** ve ardından **tezgah** seçer (4 tesis × 4 tezgah).
2. **Üç kaynak aynı anda koşar.** `basla.bat`'ın kaynak seçici menüsü kalkar;
   PROVIS, `promos3_sim.exe` ve CSV tekrar-oynatma **ayrı tezgahlara** bağlanır:

   | Tezgah | Kaynak kimliği | Taşıma |
   |---|---|---|
   | `tesis-a/tezgah-1` | `provis` | Promos3 UDP 1789 — gerçek PROVIS ağ geçidi |
   | `tesis-a/tezgah-2` | `promos3-sim` | Promos3 UDP 1790 — `promos3_sim.exe --stream` |
   | `tesis-a/tezgah-3` | `csv` | `veri/` tekrar oynatma (süreç içi) |
   | kalan 13 tezgah | — | yok |

Bu bir **gösterim (demo) bağlamasıdır**: amaç dört tesisi de doldurmak değil,
üç farklı kaynağın aynı anda, birbirine karışmadan, ayrı tezgahlar altında
göründüğünü ortaya koymaktır.

## 2. Bugünkü durum (ölçüldü, varsayım değil)

- Katalog **zaten var**: `frontend/src/domain/facilities.ts` 4 tesis × 4 tezgah
  üretir, `LIVE_MACHINE_ID = "tesis-a/tezgah-1"` tek canlı tezgahtır.
- Seçim ekranı **zaten var**: `/tezgah` (iki `Select` + durum rozeti) ve seçim
  URL'de taşınır (`?tezgah=...`).
- **Karşılama kapısı YOKTUR.** `router.tsx` içinde `{ index: true, element:
  <Navigate to="/canli" /> }` vardır ve `?tezgah` verilmediğinde kabuk
  `DEFAULT_MACHINE_ID`'ye düşer — yani uygulama sormadan A/1'i izlemeye başlar.
  ADR-0006'nın "karşılama → tezgah seçimi → izleme" cümlesi kodda bu haliyle
  karşılanmıyor; bu tasarım o boşluğu kapatır.
- Backend'de **tek** `LiveHub` ve **tek** UDP dinleyicisi vardır; hangi
  kaynağın onu doldurduğunu `basla.bat` seçer.
- CSV sim **ayrı bir süreçtir** (`python -m app.sim.replay`), hub'a hiç
  dokunmaz; yalnız SQLite'a yazar ve `/api/measurements`'tan görülür.
- `frontend` içinde `wire` alanını **hiçbir ekran okumaz**; tek tüketici
  `uygulama-kabugu.tsx`'teki `dataLive` satırıdır (bkz. §7).

## 3. Kilitlenen kararlar

| Konu | Karar | Gerekçe |
|---|---|---|
| Katalog sahibi | **Backend** (`app/machines.py`) | Üç kaynakla birlikte tezgah→kaynak bağlaması zaten backend'de olmak zorunda; katalog frontend'de kalırsa bağlama iki yerde tutulur ve uyuşmazlıkları sessiz olur |
| Kart üstündeki nokta | **Gerçek** bağlantı durumu | Yapılandırılmış ama düşmüş bir kaynağı yeşil göstermek, `/tezgah`'ın yorumlarının tam da kaçınmayı emrettiği hata |
| CSV tezgahı | Hub'ı besler (ölçüm → `LiveState`) | Tek ekran sözlüğü: üç tezgah da aynı Canlı/Alarmlar/Olaylar ekranlarını kullanır |
| CSV sim'in yeri | **Süreç içi** asyncio görevi | Hub'ı beslemek başka türlü ikinci bir süreçten IPC gerektirirdi |
| CSV sim'in DB yazması | **Sürüyor** | `/api/measurements` ve `test_replay.py` bozulmaz |
| Kaynaksız tezgah | Akış hiç kurulmaz, ekran boş | ADR-0006 madde 3 aynen geçerli |
| `?tezgah` yoksa | `/`'a (karşılama) yönlendir | Sessiz varsayılan, "kullanıcı seçsin" isteğinin tam tersi |
| Seçici sayısı | **Bir** — `/tezgah` `/`'a yönlenir | İki ayrı seçim ekranı bakımı ikiye katlar |

### Kapsam dışı (açıkça)

- Tesis B/C/D ve A/4'e kaynak bağlamak. Katalogda dururlar, dürüstçe "kaynak
  yok" derler.
- Katalogun DB'ye taşınması. `app/machines.py` **kod içi yapılandırmadır**;
  DB'ye taşımak ayrı bir fazdır (ADR-0006'nın "sonra ne gelir" maddesi).
- Alarm/olay kalıcılığı, PostgreSQL'e geçiş.
- Kullanıcı/oturum, tezgah başına yetki.
- Seçimin `localStorage`'a yazılması. Seçim URL'de taşınır; kiosk ekranı
  doğrudan adreslenebilir kalır.

## 4. Backend

### 4.1 `app/machines.py` (yeni) — katalog + kaynak bağlaması

Tek doğruluk kaynağı. Tesis/tezgah **adları** burada durur ve telden gelmez —
Promos3 telgrafında tesis/tezgah kavramı yoktur (CONTEXT.md; ADR-0006 madde 1'in
gerekçesi aynen korunur, yalnız dosyanın yeri değişir).

```python
# Uc kaynak, uc ayri kimlik. "provis" ile "promos3-sim" ayni TASIMAYI
# (Promos3 CAN-over-UDP) kullanir ama ayni SEY DEGILDIR: biri tezgahtan
# gelir, oteki uydurur. Tek bir "promos3" kimligi bu ikisini ayirt
# edilemez kilardi ve karsilama ekrani sentetik veriyi gercek gibi
# etiketlerdi.
SourceKind = Literal["provis", "promos3-sim", "csv"]

@dataclass(frozen=True)
class SourceSpec:
    kind: SourceKind
    port: int | None      # yalniz promos3 tasimasi icin

@dataclass(frozen=True)
class MachineDef:
    id: str               # "tesis-a/tezgah-1"
    name: str             # "Tezgah 1"
    model: str | None
    source: SourceSpec | None

@dataclass(frozen=True)
class FacilityDef:
    id: str
    name: str
    machines: list[MachineDef]
```

Katalog `settings`'ten kurulur, böylece bağlama yapılandırmadır:

```python
def build_catalog(s: Settings) -> list[FacilityDef]: ...
```

### 4.2 `Settings` (yeni alanlar)

```
promos3_enabled      bool = True    # A/1 — gercek PROVIS
promos3_bind         str  = "0.0.0.0"
promos3_port         int  = 1789
promos3_sim_enabled  bool = True    # A/2 — promos3_sim.exe
promos3_sim_port     int  = 1790
csv_replay_enabled   bool = True    # A/3 — CSV tekrar oynatma
```

Ad seçimi: `sim_*` öneki **zaten CSV sim'indir** (`sim_csv_dir`,
`sim_period_ms`, `sim_retention_minutes`). Promos3 simülatörüne `sim_enabled`
demek bu ikisini karıştırırdı; `promos3_sim_*` ve `csv_replay_*` ayrımı
açıktır.

### 4.3 Hub başına tezgah

`LiveHub` sınıfı **değişmez** (zaten `test_hub.py`'de tek başına test edilir).
`main.py` kaynağı olan her tezgah için bir örnek kurar:

```python
HUBS: dict[str, LiveHub] = {m.id: LiveHub(...) for m in machines_with_source()}
```

`lifespan` kaynak başına bir görev başlatır:

- A/1 → `run_promos3_ingest(HUBS["tesis-a/tezgah-1"], bind, promos3_port)`
- A/2 → `run_promos3_ingest(HUBS["tesis-a/tezgah-2"], bind, promos3_sim_port)`
- A/3 → `run_csv_ingest(HUBS["tesis-a/tezgah-3"], ...)`

Tek process/tek worker varsayımı (`main.py`'deki mevcut not) **güçlenir**:
`--workers N` artık worker başına üç dinleyici + üç CSV yazıcısı demektir. Not
buna göre güncellenir.

### 4.4 API

`/api/stream`, `/api/live`, `/api/events`, `/api/alarms` **zorunlu** `tezgah`
parametresi alır. Bilinmeyen ya da kaynaksız tezgah → **404** (gövdede ne
yapılacağı yazar; `measurements.py`'deki 503 kalıbının aynısı). Parametre adı
frontend URL'iyle aynı tutulur (`?tezgah=`), iki isim bakımı iki kat eder.

Yeni uç:

```
GET /api/machines
{
  "facilities": [
    { "id": "tesis-a", "name": "Tesis A", "machines": [
        { "id": "tesis-a/tezgah-1", "name": "Tezgah 1",
          "model": "Mazak Integrex", "source": "provis",
          "sourcePort": 1789, "connected": true },
        { "id": "tesis-a/tezgah-2", "name": "Tezgah 2",
          "model": null, "source": "promos3-sim",
          "sourcePort": 1790, "connected": true },
        { "id": "tesis-a/tezgah-3", "name": "Tezgah 3",
          "model": null, "source": "csv",
          "sourcePort": null, "connected": true },
        { "id": "tesis-a/tezgah-4", "name": "Tezgah 4",
          "model": null, "source": null,
          "sourcePort": null, "connected": false }
    ]}
  ]
}
```

`connected` o kaynağın **şu andaki** durumudur (`hub.upstream_connected`);
kaynağı olmayan tezgahta her zaman `false`'tur. camelCase, `CamelModel`
üzerinden — mevcut sözleşmeyle aynı.

**Backend ekran metni göndermez, kaynak KİMLİĞİ gönderir.**

Gerekçe **ASCII değildir**: bu depoda backend'in Türkçe etiket gönderdiği yer
vardır ve meşrudur — `promos3/rings.py` bir çeviri tablosudur (ToolStatus kodu
→ `statusLabel`, EventCode → `codeLabel`), yani telden çözülen bir kodun
okunur karşılığını **yalnız backend bilir**. Oradaki metnin backend'de olması
doğrudur.

Kaynak etiketi o sınıfa girmez. Çözülen bir şey değildir; sabit bir arayüz
metnidir ve frontend zaten `source` kimliğini **ayrıca** bilmek zorundadır —
rozet tonu, uyarı dili ve kartın vurgusu kimliğe göre değişir. Kimlik zaten
gidiyorsa etiketi de göndermek aynı bilgiyi iki biçimde taşımak olurdu, ve o
iki biçim zamanla ayrışır.

Bu yüzden `source` bir **kimliktir**; okunur karşılığı (`"Simülatör —
değerler sentetiktir"`, `"PROVIS ağ geçidi"`, `"CSV tekrar oynatma"`)
frontend'de tek bir haritada durur.

`/api/measurements` **değişmez**: hâlâ DB'yi okur, tezgah parametresi almaz.

### 4.5 `app/csv_live.py` (yeni) — saf eşleyici

`live.py` ile aynı kalıp: saatsiz, saf, tek başına test edilebilir.

```python
def apply_measurement(state: LiveState, rec: MeasurementRecord,
                      time_iso: str) -> LiveState: ...
```

Eşleme:

| CSV | `LiveState` |
|---|---|
| `unit_no` (10660 / 10665) | `UnitInfo(unit=..., serial_no=str(...), online=True)` |
| 4 özellik yuvası | `Feature(kind="series")`, kimlik `csv:{unit}:{slot}`, ad CSV başlığından |
| yuva değeri | `samples` kayan pencere (`live.WINDOW` = 120), `current`, `min_value`, `max_value` |
| `limits[]` | `FeatureLimit`; `feature_nr` eşleşen limit → `limit_level` → `pct` |
| `alarm` ≠ 0 | `Alarm` (`channel_nr`, `cycle_nr=cut_nr`, `alarm_limit` → `level`) |
| `cut_nr` | `cycle` |
| `workpiece` | **null kalır** — Workpiece ID kolonu 262/262 dosyada boştur |
| — | `wire` **null kalır** — CSV'nin teli yoktur |

`confidence`: `"confirmed"`. Değerler kalibre edilmemiş bir başlık
yerleşiminden değil, belgelenmiş bir Provis dışa aktarımından gelir ve
`csv_reader` kolon hizasını dosya başına doğrular.

Uydurulmayanlar açıkça boş bırakılır (`workpiece`, `plc_inputs`,
`plc_outputs`, `wire`, `g_type`/`firmware` gibi kimlik alanları). CSV'de
karşılıkları yoktur; doldurmak ekranda kaynağı olmayan bir değer üretirdi.

**Ünite numarası notu:** `10660`/`10665` klasör adlarıdır; CONTEXT.md ve
`domain.py` telde iki üniteyi 10659/10663 **seri numaralarıyla** anar.
İkisi aynı şey değildir, o yüzden klasör numarası hem `unit` hem `serial_no`
olarak olduğu gibi taşınır ve CAN türevi bir ünite indisiymiş gibi
gösterilmez.

### 4.6 `app/adapters/csv_replay.py` (yeni) — süreç içi ingest

`run_promos3_ingest` ile aynı sözleşme: sonsuz async görev, iptal edilebilir,
kendi içinde toparlanır.

Her an için sırayla:

1. CSV oku + satır yaz → `asyncio.to_thread` (SQLAlchemy senkrondur; olay
   döngüsü bloke edilmez)
2. `hub.apply_measurement(rec, now_iso)` → **olay döngüsünde** (hub kilitsizdir
   ve tek döngü varsayar; başka bir iş parçacığından yazmak o varsayımı bozar)
3. `sim_period_ms` kadar `await asyncio.sleep`

Budama (`prune`) tur sonunda, yine `to_thread` ile. `_with_lock_retry`'ın kilit
yeniden deneme davranışı aynen kullanılır.

`app/sim/replay.py` **kalır**: CLI'si (`--once`, `--csv-dir`, `--period-ms`) ve
`write_moment`/`prune`/`_with_lock_retry` yardımcıları hem testlerin hem yeni
adaptörün ortak zeminidir. Adaptör bu yardımcıları çağırır, kopyalamaz.

### 4.7 `frames` sayacı — "veri geliyor mu" sorusunun kaynaktan bağımsız cevabı

`LiveHub` bir `frames` sayacı tutar; her uygulanan yük (Promos3 mesajı ya da
CSV ölçümü) onu artırır. `state` olayının **zarfına** eklenir:

```json
{ "seq": 42, "frames": 17, "state": { ... } }
```

Zarfa konur, `LiveState`'e değil: `LiveState` frontend `types.ts` ile birebir
alan sözleşmesidir, bu ise akış meta verisidir — `seq` zaten oradadır. Ayrıca
`status` olayına konamaz, çünkü status yalnız **değişince** yayınlanır; her
karede status basmak tüm SSE istemcilerini boşuna uyandırırdı.

## 5. Frontend

### 5.1 Rotalar

```
/                  KarsilamaRoute      (tam ekran, AppShell YOK)
/tezgah            -> Navigate to "/"  (tek seçici kalsın)
/canli   ]
/alarmlar]         UygulamaKabugu altında (bugünkü gibi)
/olaylar ]
*                  -> Navigate to "/"
```

`?tezgah` **verilmezse** kabuk varsayılana düşmez, `/`'a yönlendirir.
`DEFAULT_MACHINE_ID` ve `LIVE_MACHINE_ID` kalkar — ikisi de "tek canlı tezgah"
varsayımının kalıntısıdır.

Kabuktaki **"Değiştir"** düğmesi `/?tezgah=<mevcut>`'a gider; karşılama ekranı
bu parametreyle açılışta doğru tesisi seçili gösterir ve bir **"Vazgeç"**
sunar (bugünkü `/tezgah`'ın davranışı korunur).

### 5.2 `domain/katalog.ts` (yeni) — katalog istemcisi

`facilities.ts` yerini alır: tipler ve yardımcılar (`findMachine`,
`machineTitle`) kalır, veri `/api/machines`'ten gelir.

- Modül düzeyinde önbellek + `useKatalog()` kancası.
- `connected` tazeliği için karşılama ekranı açıkken **5 sn**'de bir yeniden
  çekilir. İzleme ekranlarında yeniden çekilmez; oradaki bağlantı durumunu
  zaten SSE `status` olayı taşır.
- Backend kapalıyken karşılama ekranı hata durumu gösterir (paketin
  `DataState`/`four-states` kalıbı) — boş bir katalog "hiç tezgah yok" diye
  okunmamalıdır.
- Kabuk başlığı katalog gelene dek ham kimliği gösterir. Dürüst ve geçicidir;
  ad uydurmaz.

### 5.3 Karşılama ekranı

Tam ekran, uygulama kabuğu yok:

```
              Mazak İzleme
     İzlemek istediğiniz tezgahı seçin

  ┌────────┬────────┬────────┬────────┐
  │Tesis A │Tesis B │Tesis C │Tesis D │
  └━━━━━━━━┴────────┴────────┴────────┘

  ┌───────────────┐  ┌───────────────┐
  │ Tezgah 1      │  │ Tezgah 2      │
  │ ● Canlı       │  │ ● Canlı       │
  │ Mazak Integrex│  │ Simülatör     │
  └───────────────┘  └───────────────┘
  ┌───────────────┐  ┌───────────────┐
  │ Tezgah 3      │  │ Tezgah 4      │
  │ ● Canlı       │  │ ○ Kaynak yok  │
  │ CSV tekrar    │  │               │
  └───────────────┘  └───────────────┘
```

Kart durumları — üçü **ayrı** görünür, çünkü üçü ayrı şeydir:

| Durum | Gösterim | Anlamı |
|---|---|---|
| kaynak var, bağlı | dolu nokta, `success` | şu anda veri geliyor |
| kaynak var, bağlı değil | dolu nokta, `warning` | tanımlı ama düşmüş — seçilebilir, ekran boş durur |
| kaynak yok | boş nokta, `neutral` | bu tezgaha kaynak tanımlanmamış (arıza değil) |

Kaynağı olmayan kart **seçilebilir kalır** (ADR-0006 madde 3: boş ekran doğru
davranıştır ve kullanıcı bunu seçmeden önce okur), ama seçildiğinde ne olacağı
kartta yazar.

Kartın **üçüncü satırı her zaman kaynağın okunur adıdır**, model değil:

| `source` | Üçüncü satır |
|---|---|
| `provis` | PROVIS ağ geçidi |
| `promos3-sim` | Simülatör — değerler sentetiktir |
| `csv` | CSV tekrar oynatma |
| `null` | (boş) |

Model (`"Mazak Integrex"`) biliniyorsa **ayrıca** gösterilir, kaynağın yerine
değil. Yukarıdaki taslakta A/1'de model, A/2–A/3'te kaynak yazıyor olması bir
tutarsızlıktı: operatörün bilmesi gereken şey her kartta aynı yerde durmalı ve
"bu tezgahın verisi uydurmadır" uyarısı bir modelin arkasına saklanamaz.

**Bileşenler `@alp/design-system`'den gelir.** Kart/sekme/rozet karşılıkları
uygulama yazılmadan **önce** `COMPONENTS.md` ve `blocks/` okunarak seçilir
(CLAUDE.md kuralı). Yukarıdaki yerleşim kararlaştırılmıştır; bileşen adları
değildir. Elle bileşen yazılmaz.

### 5.4 Akış kancası

`useBackendLive(enabled: boolean)` → `useBackendLive(machineId: string | null)`;
`STREAM_URL` sabiti yerine `/api/stream?tezgah=<id>`. `machineId` değişince
`EventSource` kapanıp yeniden kurulur (mevcut `useEffect` bağımlılığı bunu
zaten yapar). `LiveConnection` bir `frames: number` alanı kazanır.

## 6. `basla.bat`

Tek kip. Menü, `provis|sim|csv|sahte|veri` argümanları ve kip banner'ları
kalkar; başlıktaki 1–11 numaralı maddeler bu tasarıma göre yeniden yazılır.

Başlatılanlar: **backend**, **Vite**, **`promos3_sim.exe --stream
127.0.0.1:1790`**. CSV artık süreç içidir, dördüncü pencere yoktur.

Korunanlar:

- LAN IP keşfi ve banner (madde 8) — makinedeki DLP gerçeği değişmedi.
- 8001/5173 port kontrolü.
- `alembic upgrade head` — artık **her koşumda**, çünkü CSV her koşumda yazar.
- Kaynak bayrakları **açıkça** yazılır (madde 2): üçü de `true`.
- Önceden koşan `promos3_sim` temizliği (`sahte_oldur`). Elle çift tıklanan bir
  simülatör hâlâ **varsayılan `--serve`** kipinde 1789'u bağlar ve **gerçek
  PROVIS'in** datagramlarını çalar (madde 6). Bu risk kalkmadı.
- `dur` içindeki `csv_sim_oldur`: `python -m app.sim.replay` CLI'si duruyor,
  elle başlatılmış bir kopya sağ kalabilir.

Kalkan: "simülatör açıksa **başlamayı reddet**" dalı. Simülatörün artık kendi
tezgahı ve kendi portu var; sentetik verinin gerçek sanılması bu bağlamada
mümkün değil — A/2 kartında ve topbar'da "Simülatör" yazar.

`kur.bat` ve `web.config` değişmez.

## 7. Bu tasarımın düzelttiği sessiz hata

`uygulama-kabugu.tsx`:

```ts
const dataLive = live.connected && (live.state.wire?.parsed ?? 0) > 0;
```

`wire` **Promos3 taşıma teşhisidir** (`domain.py`: datagram/CAN çerçeve
sayaçları). CSV tezgahının teli yoktur, yani `wire` null kalır ve bu satır
kusursuz akan bir tezgahta üst barda **"Veri Yok"** yazdırırdı — hem de
projenin en çok kaçındığı türden bir yalan.

Düzeltme: `dataLive = live.connected && live.frames > 0` (§4.7). `wire`
belgelendiği şey olarak, yalnız Promos3 teşhisi olarak kalır.

## 8. Testler

Yeni:

- `test_csv_live.py` — saf eşleyici: yuva → `Feature`, kayan pencere, limit →
  `pct`, alarm biti → `Alarm`, `workpiece`/`wire` null kalır.
- `test_machines.py` — katalog: 4×4, üç bağlama doğru, kalan 13 kaynaksız.
- `test_api.py` eklemeleri — `/api/machines` şekli; `/api/stream?tezgah=` ile
  doğru hub; bilinmeyen ve kaynaksız tezgahta 404.

Değişen:

- `test_api.py`'nin `/api/live` çağrıları `?tezgah=` alır.
- `conftest.py` **üç bayrağı birden** kapatır (`PROMOS3_ENABLED`,
  `PROMOS3_SIM_ENABLED`, `CSV_REPLAY_ENABLED`). Yalnız birincisini kapatmak
  testleri 1790'ı dinlemeye ve geçici DB'ye CSV yazmaya bırakırdı — mevcut
  yorumun gerekçesi artık üç yere birden uygulanır.

Bozulmayacağı doğrulanacaklar: `test_replay.py`, `test_csv_reader.py`,
`test_hub.py`, `test_promos3.py`, `test_live.py`.

Frontend: `bun run lint` (eslint + `tsc --noEmit`).

Elle doğrulama: `.\basla.bat`, karşılama ekranı, A/1–A/2–A/3 sırayla seçilip
üçünün de veri gösterdiği, A/4'ün dürüstçe boş durduğu görülür.

## 9. Belge güncellemeleri

- **ADR-0006** güncellenir. Kendi "sonra ne gelir" maddesi tam olarak bunu
  öngörüyor: *"Kaynak tezgah başına ayrıştığında `hasLiveSource` yerini tezgah
  başına kaynak tanımına bırakır."* Madde 1 (katalog frontend'de) ve madde 2
  (tek canlı kaynak) yerlerini yeni karara bırakır; madde 3 (kaynaksız tezgah
  dürüstçe boş) ve madde 4 (`key={machineId}`) aynen geçerlidir.
- **CLAUDE.md** — `basla.bat` kipleri anlatan bölüm yeniden yazılır.
- **CONTEXT.md** — sözlük değişmez; Tesis/Tezgah tanımları aynen geçerli.

## 10. Uygulama sırası

1. Backend katalog + `Settings` + `/api/machines`
2. Hub başına tezgah + uçlara `tezgah` parametresi + `frames` sayacı
3. `csv_live.py` eşleyici (+ testleri)
4. `csv_replay.py` adaptörü, `lifespan` bağlanması
5. Frontend `katalog.ts` + akış kancası + `dataLive` düzeltmesi
6. Karşılama ekranı (önce `COMPONENTS.md` + `blocks/` okunur)
7. `basla.bat` tek kip
8. ADR-0006 + CLAUDE.md

1–4 tek başına test edilebilir ve `curl` ile doğrulanabilir; 5–6 ondan sonra
gerçek veriye bakar.

## 11. Bilinen riskler

- **Üç kaynak tek olay döngüsünde.** CSV adaptörü DB işini `to_thread`'e
  atmazsa iki UDP dinleyicisini de geciktirir. §4.6 bunu şart koşar; gözden
  kaçarsa belirtisi "sim tezgahında kare düşmesi" olur.
- **1790 portu meşgul olabilir.** `promos3_sim.exe --serve` elle açılmışsa
  1789'u bağlar; 1790 çakışması ise başka bir uygulamadan gelebilir. Adaptör
  bağlanamazsa o tezgah `connected: false` görünür — kartta okunur, sessiz
  kalmaz.
- **`veri/mazak.db` her koşumda yazılır.** Bugün de öyleydi (CSV kipi), ama
  artık *her* koşum CSV kipidir; `sim_retention_minutes` (60 dk) budaması bu
  yüzden daha önemli hale gelir.
