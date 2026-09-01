import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.adapters.csv_replay import run_csv_ingest
from app.adapters.promos3_udp import run_promos3_ingest
from app.config import settings
from app.db import get_db
from app.domain import Alarm, EventRow
from app.hub import LiveHub
from app.kosum import KosumOut, build_kosum
from app.machines import (
    CatalogOut,
    build_catalog,
    catalog_wire,
    find_machine,
    machines_with_source,
)
from app.measurements import MeasurementPage, read_page

# Katalog acilista BIR KEZ kurulur: ayarlar surec omru boyunca degismez.
CATALOG = build_catalog(settings)

# Kaynagi olan her tezgahin KENDI hub'i vardir. Tek hub, uc kaynagin
# durumunu tek durumda toplardi: uc tezgah da ayni cevrimi, ayni alarmlari
# gosterirdi.
#
# Tek process/tek worker varsayimi (IIS HttpPlatformHandler standardi):
# uvicorn --workers N kullanilirsa her worker AYRI hub takimi + AYRI
# dinleyiciler + AYRI CSV yazicisi kurar (ikinci UDP bagi da catisir) —
# kullanma.
HUBS: dict[str, LiveHub] = {
    m.id: LiveHub(source_name=m.source.kind, feature_names=settings.feature_names())
    for m in machines_with_source(CATALOG)
}


def _hub_for(tezgah: str) -> LiveHub:
    """Tezgahin hub'i; yoksa NE YAPILACAGINI soyleyen 404.

    Ciplak 404 yerine yonlendirme: kaynaksiz bir tezgahi elle cagiran biri
    hangi tezgahlarin yayin yaptigini bir istekte ogrenebilmeli.
    """
    hub = HUBS.get(tezgah)
    if hub is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"bilinmeyen ya da kaynaksiz tezgah: {tezgah}; "
                "yayin yapan tezgahlar: GET /api/machines"
            ),
        )
    return hub


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Tek giris adaptoru: Prometec gateway'i (ADR-0002), salt okuyucu. Ayni
    # yol simulatorden de beslenir (promos3_sim.exe --stream). Kapatilabilir
    # (testler) ve gorev kopsa kendi icinde yeniden baglanir; kapaniste iptal
    # edilir.
    tasks: list[asyncio.Task[None]] = []
    for m in machines_with_source(CATALOG):
        hub = HUBS[m.id]
        if m.source.kind in ("provis", "promos3-sim"):
            tasks.append(
                asyncio.create_task(run_promos3_ingest(hub, settings.promos3_bind, m.source.port))
            )
        elif m.source.kind == "csv":
            tasks.append(
                asyncio.create_task(
                    run_csv_ingest(
                        hub,
                        csv_dir=settings.csv_dir(),
                        period_ms=settings.sim_period_ms,
                        retention_min=settings.sim_retention_minutes,
                    )
                )
            )
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        for task in tasks:
            with suppress(asyncio.CancelledError):
                await task


app = FastAPI(title="ALP Backend", lifespan=lifespan)


# --- API ---
# Tum API uclari /api altinda toplanir (frontend ile cakismasin).
@app.get("/api/health")
def health() -> dict[str, str]:
    """Altyapi saglik kontrolu. Silme; deploy ve izleme buna bakar."""
    return {"status": "ok"}


@app.get("/api/machines")
def machines() -> CatalogOut:
    """Tesis/tezgah katalogu + her tezgahin kaynagi, HALKASI ve VERI TAZELIGI.

    Karsilama ekraninin tek kaynagi. Iki ayri soru IKI AYRI ALANDA gider ve
    hicbiri otekinin yerine gecmez:

      connected  kaynak adaptorunun halkasi ayakta mi (UDP soketi bagli, CSV
                 ingest kosuyor). Soketin baglanmasi VERI GELDIGI ANLAMINA
                 GELMEZ: PROMOS3_BIND=127.0.0.1 ile kosan bu makinede A/1'e
                 gercek gateway'den tek bayt gelmeden de True'dur.
      dataAgeS   son uygulanan yukun uzerinden gecen saniye (SUNUCUDA
                 hesaplanir); None = bu tezgaha hic veri gelmedi.

    Yesil rozetin sarti dataAgeS'tir, connected DEGIL: tanimli ama SESSIZ bir
    kaynak yesil gorunmez. Esik telde `stalenessS` olarak gider
    (hub.DATA_STALE_AFTER_S) — sayinin tek sahibi backend'dir.
    """
    bagli = {mid for mid, h in HUBS.items() if h.upstream_connected}
    # Kaynaksiz tezgahin hub'i YOKTUR; sozlukte de yer almaz ve telde
    # dataAgeS null kalir ("kaynak yok" zaten ayri bir durumdur).
    yaslar = {mid: h.data_age_s for mid, h in HUBS.items()}
    return catalog_wire(CATALOG, connected_ids=bagli, data_age_s=yaslar)


@app.get("/api/stream")
def stream(tezgah: str) -> StreamingResponse:
    """Secilen tezgahin canli durum akisi (SSE)."""
    return StreamingResponse(
        _hub_for(tezgah).sse_frames(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/api/live")
def live(tezgah: str) -> dict:
    """Anlik goruntu (REST) — /api/stream'in tek seferlik hali; test/teshis icin."""
    hub = _hub_for(tezgah)
    return {"status": hub.status_wire(), "state": hub.state_wire()}


@app.get("/api/events")
def events(tezgah: str) -> list[EventRow]:
    """Olay gecmisi (son EVENT_LIMIT kayit, en yeni basta)."""
    return _hub_for(tezgah).state.events


@app.get("/api/alarms")
def alarms(tezgah: str) -> list[Alarm]:
    """Alarm listesi (en yeni basta)."""
    return _hub_for(tezgah).state.alarms


# Tam kosum SUREC BOYUNCA DEGISMEZ: `veri/` altindaki 262 dosya statiktir,
# CSV tekrar oynatmasi onlari yalnizca OKUR. Bu yuzden bir kez kurulur ve
# saklanir — her istekte 262 dosyayi yeniden okumak ayni cevabi ~0,5 sn
# harcayarak uretirdi (sayi baselines.py'de olculmustur).
#
# KOK ARGUMANDIR, ICERIDEN OKUNMAZ. `settings.csv_dir()`u govdede cagirsaydik
# onbellek neyi sakladigini SOYLEMEZDI: anahtar bos kalir, kok degistiginde
# (test) eski korpus dogru cevap gibi geri gelirdi. Argumana tasinca anahtar
# kokun kendisi olur ve yanlis cevap yapisal olarak imkansizlasir.
@lru_cache(maxsize=1)
def _kosum_kaydi(root: Path) -> KosumOut:
    return build_kosum(root)


# lru_cache KILITSIZDIR: iki es zamanli ilk istek 262 dosyayi iki kez okur
# (sonuc dogru kalir, emek bosa gider). Kilit bunu tek okumaya indirir ve
# `to_thread` ile birlikte olay dongusunun o yarim saniye boyunca bloke
# olmamasini saglar.
_KOSUM_KILIT = asyncio.Lock()


@app.get("/api/kosum")
async def kosum(tezgah: str) -> KosumOut:
    """Tezgahin KAYITLI TAM KOSUMU — CSV korpusunun tamami, SALT OKUYUCU.

    Canli akisla (/api/stream, /api/live) ILGISI YOKTUR ve ona dokunmaz: o
    yol hub'dan beslenir ve ekranda KAYAN BIR PENCERE gosterir (120 ornek),
    yani 131 anlik kosumun tamamini hicbir zaman gostermez. Burasi dosyalari
    bastan sona okur.

    KOSUM KAYDI CSV KAYNAGININ OZELLIGIDIR, her tezgahin degil: kaynagi
    baska olan (ya da hic olmayan) tezgah icin 404 doner. Ciplak degil
    yol gosteren bir 404 — `_hub_for` ile ayni idiom.
    """
    machine = find_machine(CATALOG, tezgah)
    if machine is None or machine.source is None or machine.source.kind != "csv":
        raise HTTPException(
            status_code=404,
            detail=(
                f"bu tezgahin kayitli kosumu yok: {tezgah}; "
                "kosum kaydi CSV kaynakli tezgaha aittir: GET /api/machines"
            ),
        )

    async with _KOSUM_KILIT:
        try:
            return await asyncio.to_thread(_kosum_kaydi, settings.csv_dir())
        except FileNotFoundError as exc:
            # Katalog CSV kaynagini VAAT ETMISTIR ama dosyalar yerinde
            # degildir: bos bir kosum donmek "kosum bos" diye okunurdu.
            # measurements.read_page ile ayni kalip — ne yapilacagini soyle.
            raise HTTPException(
                status_code=503, detail=f"CSV kaynagi okunamadi: {exc}"
            ) from exc


@app.get("/api/measurements")
def measurements(
    unit: int | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> MeasurementPage:
    """CSV sim'in yazdigi olcumler (en yeni basta) — SALT OKUYUCU teshis ucu.

    Canli akisla (/api/stream, /api/live) ILGISI YOKTUR: o yol Promos3
    telgrafindan beslenir ve bellekte durur. Bu uc DB'yi okur.
    """
    return read_page(db, unit, limit)


# --- Frontend (production) ---
# Vite build ciktisi: frontend/dist. Dev'de bu klasor yoktur (Vite ayri
# portta calisir), o yuzden kosullu mount. Prod'da IIS tek process olarak
# bu app'i baslatir; frontend buradan servis edilir.
_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if _DIST.is_dir():
    # Statik varliklar (js, css, vs)
    app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    # SPA fallback: /api disindaki tum yollar index.html'e gider,
    # boylece React Router (varsa) client-side calisir. Tanimsiz /api yollari
    # index.html DEGIL 404 almali; yoksa JSON bekleyen istemci HTML alir ve
    # asil hata (yanlis yol) maskelenir.
    @app.get("/{full_path:path}")
    def spa(full_path: str) -> FileResponse:
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        return FileResponse(_DIST / "index.html")
