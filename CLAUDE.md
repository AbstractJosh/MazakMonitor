# Proje Calisma Notlari

Bu dosya BU projenin stack'ini, calistirma/test komutlarini ve agent
yapilandirmasini tanimlar. Genel arac tercihleri (uv/pnpm) ve davranis
kurallari global CLAUDE.md'de; domain bilgisi CONTEXT.md'de (ilk /alp-hizala
ile dogar).

## Stack (bu proje icin sabit)
- Backend: FastAPI + PostgreSQL
- Frontend: Vite + React + TypeScript
- UI: **`@alp/design-system` ARTIK BIR BAGIMLILIK DEGIL.** Paket yalnizca ic
  Gitea registry'sinde (10.10.100.220:3000) durur, public npm'de YOKTUR
  (dogrulandi: 404) ve ALP agi disindaki bir makinede arayuz HICBIR BETIKLE
  kurulamiyordu. Karar kullanicinindir: bagimlilik kaldirildi, paketin
  KULLANILAN yuzeyi depo icine alindi.

  Yuzey `frontend/src/alp-local/` altindadir (index.tsx / charts.tsx /
  screens.tsx / styles.css / theme.css) ve `@alp/design-system` adiyla
  baglanir — takma adlar `vite.config.ts` (resolve.alias) ve
  `tsconfig.json` (paths) icinde. Bu yuzden EKRAN DOSYALARININ IMPORT
  SATIRLARI DEGISMEDI: hepsi hala `@alp/design-system`den okur ve 23
  kaynak dosyanin hicbirine dokunulmadi.

  **Yeni ekran/bilesen yazarken** once `src/alp-local/index.tsx` dosyasini oku:
  sozluk odur. Eksik bir bilesen gerekiyorsa oraya ekle, ekran dosyasina
  elle yazma — tek-nusha kurali korunuyor, yalnizca nushanin yeri degisti.

  Sozlesmeler app.css'e baglidir ve KIRILGANDIR: `data-slot` degerleri
  (app-shell-nav / page-shell / page-shell-content / floating-panel),
  `data-state="open|closed"` ve `--radix-accordion-content-height`
  degistirilirse HAREKET ve YERLESIM bloklari sessizce bozulur.

  Paket bir gun yeniden erisilebilir olursa geri donus ucuzdur:
  `src/alp-local/` ile o iki takma ad silinir, package.json'a bagimlilik
  geri eklenir. (eslint'teki antd yasagi olu kural: paket kurulu degil.
  `npm run lint` = eslint + `tsc --noEmit`.)
- Deploy: IIS (HttpPlatformHandler) standardi.
- Bu proje icinde Node + npm kullanilir; kilit dosyasi
  `frontend/package-lock.json`. **bun ARTIK KULLANILMIYOR** — bun'dan npm'e
  gecildi, eski "npm/node YASAK" kurali dusmustur; bun'u geri getirme.
  Ozel kayit (`@alp`) icin ek yapilandirma gerekmez: npm de `frontend/.npmrc`
  ile `~/.npmrc`'yi dogal okur (bunfig karsiligi aramaya cikma).

## Calistirma

Ilk kurulum (bir kez): `.\kur.bat` — uv sync + npm ci; ALP vekil/TLS
ayrintilari betigin basliginda (ic registry'nin vekil muafiyeti dahil).

Gunluk: `.\basla.bat` (kip almaz, tek kip) / `.\basla.bat dur`

`.\basla.bat` backend + arayuz + `promos3_sim.exe --stream`i baslatir. Uc
kaynak AYNI ANDA kosar, ayri tezgahlara baglidir:

| Tezgah            | Kaynak        | Tasima                                       |
|-------------------|---------------|-----------------------------------------------|
| tesis-a/tezgah-1  | `provis`      | Promos3 UDP 1789 — gercek PROVIS ag gecidi     |
| tesis-a/tezgah-2  | `promos3-sim` | Promos3 UDP 1790 — `promos3_sim.exe --stream`  |
| tesis-a/tezgah-3  | `csv`         | CSV tekrar oynatma — SUREC ICI                 |
| kalan 13 tezgah   | —             | kaynak yok                                     |

Bu bag `backend/app/machines.py`'de durur ve `GET /api/machines`'ten gelir;
karsilama ekraninda gorunur. Kaynagi olmayan tezgahta ekran durustce bos
durur (ariza degil, yapilandirma).

CSV sim artik SUREC ICIDIR (ayri pencere degil): backend'in kendi asyncio
gorevi olarak `veri\` altindaki 262 olcum CSV'sini DONGUSEL okur, yerel
SQLite'a (`veri\mazak.db`) yazar VE hub'i besler. `promos3_sim.exe` ILE
KARISTIRILMAZ — o TEL bicimi uretir (Promos3 CAN-over-UDP -> A/2), bu OLCUM
SATIRI uretir (CSV -> hub -> A/3); artik ikisi de ekrani besler, yalniz
farkli tezgahlarda.

**Arayuz LAN IP'sinden acilir, loopback'ten degil.** Bu makinede Chrome trafigi
Websense/Forcepoint DLP eklentisinden geciyor ve loopback'i ATLAMIYOR:
`127.0.0.1:5173` tarayicida hata sayfasi verir ama ayni anda `curl` ile calisir
— yani sunucu saglamdir, engelleyen tarayicidir. Bu yuzden Vite `--host 0.0.0.0`
ile kosar ve betik LAN IP'sini her kosumda bulup banner'a yazar. Disari acilan
yalniz Vite'tir; backend `127.0.0.1:8001`'de kalir (LAN istemcisi `/api`'ye
Vite'in vekili uzerinden ulasir). Ayrintisi basla.bat basligindaki madde 8.

Backend (elle):

    cd backend
    uv sync
    uv run uvicorn app.main:app --reload --port 8001

Frontend (elle):

    cd frontend
    npm install
    npm run dev -- --host 0.0.0.0

## Hareket (animasyon)

Sure ve egri **token'dan** gelir (`--duration-*`, `--ease-*`); ham `ms` ya da
elle yazilmis bezier YASAK (tasarim dili, "Hareket ve durum"). Acilip kapanan
seyin egrisi `--ease-standard`tir — iki ucu da yavaslatan simetrik olan odur.
`prefers-reduced-motion` her animasyonlu kuralda karsilanir.

Uygulamaya ait animasyonlar TEK yerde durur: `frontend/src/app/app.css`
icindeki `HAREKET` blogu. Sinif onu `mzi-`; `alp-` paketin ad alanidir
(`alp-oto-izgara`, `alp-focus`), oraya yazma.

O bloktaki her kural paketin KAPATMADIGI bir bosluga yamadir ve paket kendi
gonderdiginde silinir — yeni yama eklerken hangi boslugu kapattigini da yaz.
Bugun uc tanesi var: Accordion yukseklik animasyonu, AppShell sol nav genislik
gecisi, Drawer cikis animasyonu.

Ayni dosyada bir de `YERLESIM` blogu var (HAREKET'ten ONCE gelir): bugun tek
kural, alarm penceresinin payini `[data-slot=page-shell-content]`in ALT
DOLGUSUNDAN veren `.mzi-pencere-payi`. Pay scroller'in ICINDEDIR; disarida
vermek (kabukta `pb-20`) scroller'i kisaltip sayfanin altinda tum genislikte
olu bir serit birakiyordu. Ayni kural gecerli: paket scroller'a kendi alt
payini gonderirse blok silinir.

Radix tuzagi: `Presence` sokumu YALNIZ CSS **animasyonu** icin erteler
(`animationend` bekler). Acilip kapanan Radix icerigini `transition` ile
animasyonlamaya calisma — icerik ilk karede sokulur ve kapanis hic gorunmez.
Ayrica kapanista yuksekligi Radix bir layout effect'te olcer: icerigi kendi
`{acik && ...}` kosulunla sokme, olculen deger yanlis cikar. Kapali Radix
icerigi zaten hic basilmaz (`isOpen && children`), o kosul gereksizdir.

## Test / kontrol

- Backend testleri: cd backend && uv run pytest
- Frontend tip kontrol: cd frontend && npm run lint
- DB migration uygula: cd backend && uv run alembic upgrade head
- Yeni migration olustur: cd backend && uv run alembic revision -m "aciklama"

## Agent skills

### Issue tracker
Local markdown under .scratch/. See docs/agents/issue-tracker.md.

### Triage labels
English canonical roles. See docs/agents/triage-labels.md.

### Domain docs
Single-context. CONTEXT.md artik VAR (depo kokunde) — ilk /alp-hizala ile
dogmustu. See docs/agents/domain.md.