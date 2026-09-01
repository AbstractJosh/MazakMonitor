# Mazak Monitor

Bir Mazak CNC tezgahındaki Prometec izleme ünitelerinin verisini görünür ve
sahip olunabilir kılan uygulama: FastAPI backend, Prometec gateway'inden
CAN-over-UDP okur (salt okuyucu) ve React arayüzüne canlı akış (SSE) verir.
Terimler için `CONTEXT.md`, mimari kararlar için `docs/adr/`.

## Kurulum ve çalıştırma

```bat
git clone <depo-adresi>
cd MazakMonitor
.\kur.bat       # bir kez: uv sync + npm ci (ALP vekil/TLS'ini kendisi çözer)
.\basla.bat     # backend + arayüz + simülatör; üç kaynağı birden açar
.\basla.bat dur # başlatılan her şeyi durdurur
```

**Kaynak menüsü YOKTUR** ve `provis` / `folly` / `sahte` / `veri` gibi kip
argümanları da yoktur; `.\basla.bat` tek bir şey yapar. `dur` dışında argüman
almaz.

### Tezgah → kaynak bağlaması

Üç kaynak AYNI ANDA koşar ve her biri AYRI bir tezgaha bağlıdır. Bağlamanın tek
doğruluk kaynağı `backend/app/machines.py`'dir; arayüz onu `GET /api/machines`
ucundan okur.

| Tezgah | Kaynak | Taşıma | Ne olduğu |
|--------|--------|--------|-----------|
| Tesis A / Tezgah 1 | `provis` | UDP 1789 | Gerçek Prometec gateway'i (Promos3 telgrafı) |
| Tesis A / Tezgah 2 | `promos3-sim` | UDP 1790 | `promos3_sim.exe --stream` — **her sayı SENTETİKTİR** |
| Tesis A / Tezgah 3 | `csv` | süreç içi | `veri\` altındaki 262 ölçüm CSV'sinin döngüsel tekrarı |
| Kalan 13 tezgah | — | — | Kaynaksız: ekran dürüstçe boş kalır |

Uygulama `/` adresindeki karşılama ekranıyla açılır; hangi tezgahın veri
gönderdiği orada yazar. Rozet dört hâli ayırır: "Kaynak yok", "Kaynak bağlı
değil", "Veri bekleniyor" (kaynak dinliyor ama akmıyor) ve "Canlı".

Betik `.\basla.bat` her koşumda `alembic upgrade head` çalıştırır (CSV adaptörü
süreç içidir ve her koşumda DB'ye yazar).

**Arayüz LAN IP'sinden açılır, loopback'ten değil.** Betik LAN adresini her
koşumda bulup banner'a yazar; nedeni (Chrome'un DLP eklentisi loopback'i
atlamıyor) `basla.bat` başlığındaki madde 8'de.

### Gerekli araçlar

Geliştirme makinesine yalnız şunlar kurulur; gerisini betikler halleder:

| Araç | Ne için | Kurulum |
|------|---------|---------|
| [Git](https://git-scm.com/) | depoyu almak | `winget install Git.Git` |
| [uv](https://docs.astral.sh/uv/) | backend (Python'u da uv indirir, ayrıca Python kurmayın) | `winget install astral-sh.uv` |
| [Node](https://nodejs.org/) 22+ (LTS; npm birlikte gelir) | arayüz (paket yöneticisi npm'dir) | `winget install OpenJS.NodeJS.LTS` |

> Taban neden 22: bağımlılıkların `engines` alanları kesişiminden çıkar, tahminden
> değil. eslint 9 `^18.18 \|\| ^20.9 \|\| >=21.1` ister, vite 6 ise
> `^18 \|\| ^20 \|\| >=22` — yani 20.0–20.8 ve tüm 21.x aralığını biri ya da öteki
> reddeder. 22 LTS boşluksuz tek taban, `OpenJS.NodeJS.LTS` de zaten onu kurar.

Depoda hazır gelen, ayrıca kurulmayan bağımlılıklar — `basla.bat` ikisini de
başlamadan önce arar ve yoksa ne yapılacağını söyleyerek durur:

- `promos3-c\done\promos3_sim.exe` — A/2 tezgahını besler. Yoksa derlenmesi
  gerekir (gcc/MinGW; komut hata metninde yazar).
- `veri\10660\*.csv` ve `veri\10665\*.csv` — A/3 tezgahını besler.

İsteğe bağlı:

- **PostgreSQL** — varsayılan veritabanı yerel SQLite'tır
  (`veri\mazak.db`, `Settings.db_url`). PostgreSQL'e geçmek için
  `backend/.env.example` → `.env` kopyalanıp `DATABASE_URL` yazılır.
- **gcc + make** — yalnız bağımsız C okuyucu `promos3-c/` derlenecekse
  (aşağıda); web uygulaması için GEREKMEZ.
- **Prometec gateway** (UDP 1789) — A/1'in gerçek kaynağı. Cihazsız denemede
  A/1 boş kalır; A/2 ve A/3 yine de veri gösterir.

Bu makinelerde `.\` öneki zorunludur (`basla.bat` başlığında nedeni yazar).
ALP ağı ayrıntıları (phantom-wcg vekili, TLS araya girme, sertifika paketi)
`kur.bat` başlığında belgelidir; ağ dışında da aynı betik çalışır.

Elle, betiksiz:

```bat
cd backend  && uv sync && uv run alembic upgrade head
cd backend  && uv run uvicorn app.main:app --reload --port 8001
cd frontend && npm install && npm run dev -- --host 0.0.0.0
```

> ALP ağındaysanız `npm install` satırından **önce** sertifika paketini kendi
> kabuğunuza tanıtın. `kur.bat` onu `setlocal` içinde kurar, yani betik bitince
> ayar sizin kabuğunuza GEÇMEZ; bu satır olmadan elle kurulum
> `UNABLE_TO_GET_ISSUER_CERT_LOCALLY` ile düşer:
>
> ```bat
> set "NODE_EXTRA_CA_CERTS=%USERPROFILE%\.alp-kok-ca.pem"
> ```
>
> Vekil muafiyeti için ayrıca bir şey yapmanız gerekmez: `frontend/.npmrc`
> içindeki `noproxy` satırı iç registry'yi phantom-wcg'den muaf tutar
> (`kur.bat` madde 5).

## Test / kontrol

```bat
cd backend  && uv run pytest      # backend testleri
cd frontend && npm run lint       # eslint + tsc
cd frontend && npm run build      # üretim çıktısı → frontend/dist
```

## Depo düzeni

```
backend/     FastAPI + Promos3 UDP adaptörü + CSV ingest (Python; uv yönetir)
frontend/    Vite + React arayüz (npm yönetir; kilit dosyası package-lock.json)
promos3-c/   Bağımsız C okuyucu + promos3_sim.exe (aşağıda)
veri/        262 ölçüm CSV'si (A/3 kaynağı) + yerel SQLite (mazak.db)
docs/        ADR'ler + agent yönergeleri
CONTEXT.md   Alan sözlüğü (tek doğruluk kaynağı)
```

## Arayüz paketi

Arayüz bileşenleri **yalnız `@alp/design-system`**'den import edilir; elle
bileşen yazmak yasaktır. Paket kurulu gelir (`frontend/package-lock.json`);
kılavuzları `frontend/node_modules/@alp/design-system/` altındadır
(`llms.txt`, `COMPONENTS.md`, `docs/design-language.md`, `blocks/`).

Eski `@alp/ui` adı ve `frontend/src/alp-ui-shim/` şimi 4a7eb77'de KALDIRILDI;
o paket kurulu bile değildir.

## Deploy (IIS)

`web.config` ALP standardını taşır: IIS, HttpPlatformHandler ile uvicorn'u tek
süreç başlatır; `npm run build` çıktısı `frontend/dist`'i backend servis eder
(`app/main.py` sonundaki koşullu mount).

---

# promos3-c — Prometec PROVIS3 monitoring reader (read-only, C)

Clean-room C reimplementation from the RE report (v2). Style: data-oriented +
pragmatic-functional — plain data (POD) types, pure `bytes -> value` parsers with
no globals or hidden state, I/O confined to the edges (sockets, file read/write,
printing). No external libraries.
Layout
```
src/
  span.h              # bounds-checked byte view + pure readers (the DOP core)
  promos3.h           # reader types/enums + transport/decode/print declarations
  promos3_proto.c     # pure tables: command names, confidence, enum -> string
  promos3_transport.c # 36-byte split, CAN-ID (BE), unit routing, reassembly
  promos3_decode.c    # header parse + body decoders + branch-complete printing
  promos3_config.h/.c # PMD export -> typed config records (pure parsers)
  promos3_state.h/.c  # reader state (POD): config + live snapshot, save/load
  xlsx.h/.c           # minimal Excel-2016 writer (stored ZIP + OOXML), no deps
  main.c              # UDP listener + wiring (config/state/xlsx/signals)
tools/pmd.c           # offline config tool + self-test
test/1974.txt         # PMD fixture (ground truth for the self-test)
```
Build & run
```
make          # builds promos3_reader + promos3_pmd
make check    # PMD config self-test vs test/1974.txt (18 assertions)

./promos3_reader --raw                       # print every CAN frame (0 assumptions)
./promos3_reader --decode \                  # reassemble + decode + print
                 --config FILE.pmd \          #   feature names from config
                 --state  FILE \              #   load at start, save on Ctrl-C
                 --xlsx   FILE.xlsx           #   log decoded messages to Excel
./promos3_reader --config-unit 1=exVL2-1.txt --config-unit 2=exVL2-2.txt --decode
./promos3_reader --dump --state FILE          # inspect a saved state file
./promos3_pmd  [--check] FILE.pmd             # decode a PMD export (/ self-test)
```
Honesty rules baked into the output
Every command carries a confidence that gates what we print, so we never
`printf` a value whose byte layout we have not confirmed:
`confirmed`   -> decoded values shown (currently: MC_ SIGNALVERLAUF trace).
`provisional` -> name + raw hex only (layout guessed; e.g. KONFIG until Phase 0).
`named`       -> known name + raw hex.
`unknown`     -> id + raw hex.
unparsed header -> surfaced as `[UNPARSED HEADER]` + raw hex, never dropped.
Amplitude is raw 0-255, no scaling — the reader never prints engineering
units. Feature names come from the loaded config (SKanalRec), not hardcoded.
Status
```
[x] Offline config (`promos3_pmd`, `--config`, `--config-unit N=FILE`) —
device + channel + cycle limit thresholds; self-test is file-agnostic
(passes on both the SPINDEL/high-bit and Turkish/low-bit exports).
[x] RAW mode — correct now (no framing assumptions).
[x] DECODE mode plumbing + branch-complete, confidence-gated printing.
[x] State save/load (`--state`, `--dump`) — POD snapshot, magic/version guard.
[x] Excel-2016 logging (`--xlsx`) — validated as a real workbook.
[ ] Two `>>> CALIBRATE (PHASE 0) <<<` hooks (`reasm_expected_len`,
`parse_message_header`) await one capture; then DECODE goes live and
KONFIG/trace can be promoted to `confirmed`.
Notes / limits
xlsx buffers rows in memory and writes on close; rotate files for long runs.
State serialization is a raw POD snapshot (single-target device bridge). It is
rejected on load if magic/version/size differ; keep the struct stable or bump
STATE_VERSION.
`--config FILE` currently applies one device config to all units; per-unit
config (e.g. exVL2-1 / exVL2-2 for the two units) can be added.
```
