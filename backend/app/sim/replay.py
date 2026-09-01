"""CSV tekrar-oynatma simulatoru — veri/ altindaki olcumleri DB'ye yazar.

    cd backend && uv run python -m app.sim.replay

promos3_sim.exe ILE KARISTIRILMAZ: o TEL bicimini uretir (UDP 1789 -> hub ->
SSE -> ekran), bu ise OLCUM SATIRI uretir (CSV -> SQLite). Iki yol birbirine
dokunmaz; bu sim sokete tek bayt yazmaz.

Zaman damgasi: recorded_at = SIMDI, source_time = CSV'nin kendi zamani.
Dongu basa donunce cakisma olmaz ve kaynak zaman da kaybolmaz.
"""

import argparse
import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import delete, inspect
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal, engine
from app.models import Measurement, MeasurementFeature, MeasurementLimit
from app.sim.csv_reader import MeasurementRecord, Moment, read_measurement, read_moments

log = logging.getLogger("app.sim.replay")

# "database is locked" gecicidir (baska surec yaziyor). Kac kez denenecegi.
LOCK_RETRIES = 3

# Surekli kipte tur basina en az bu kadar beklenir (bkz. run()).
MIN_LAP_MS = 200


def _to_row(r: MeasurementRecord, now: datetime) -> Measurement:
    return Measurement(
        recorded_at=now,
        source_time=r.source_time,
        unit_no=r.unit_no,
        channel_nr=r.channel_nr,
        tool_nr=r.tool_nr,
        program_nr=r.program_nr,
        cut_nr=r.cut_nr,
        workpiece=r.workpiece,
        alarm=r.alarm,
        alarm_limit=r.alarm_limit,
        source_file=r.source_file,
        features=[
            MeasurementFeature(
                slot=f.slot, name=f.name, value=f.value, work_value=f.work_value
            )
            for f in r.features
        ],
        limits=[
            MeasurementLimit(
                limit_nr=lv.limit_nr,
                level=lv.level,
                lim_type=lv.lim_type,
                feature_nr=lv.feature_nr,
            )
            for lv in r.limits
        ],
    )


def write_moment(session: Session, moment: Moment, now: datetime) -> int:
    """Bir ani yazar; yazilan Measurement sayisini doner (0..unite sayisi).

    Bozuk bir dosya TUM ani dusurmez: o unite atlanir, digeri yazilir.
    """
    written = 0
    for unit_no, path in moment.files:
        record = read_measurement(path, unit_no)
        if record is None:
            continue
        session.add(_to_row(record, now))
        written += 1
    session.commit()
    return written


def prune(session: Session, older_than: datetime) -> int:
    """recorded_at esikten eski satirlari siler; silinen olcum sayisini doner.

    Cocuklar DB'nin ON DELETE CASCADE'i ile gider (models.py'de
    passive_deletes=True). ORM'in 65 bin satiri tek tek yuklemesi kabul
    edilemez olurdu.
    """
    deleted = session.execute(
        delete(Measurement).where(Measurement.recorded_at < older_than)
    ).rowcount
    session.commit()
    return deleted


def _with_lock_retry(session: Session, label: str, work: Callable[[], int]) -> int:
    """SQLite kilidi gecicidir: kisa geri cekilmeyle birkac kez dene.

    Yalniz "database is locked" mesaji burada yutulur ve yeniden denenir;
    baska turden bir OperationalError (tablo/kolon uyusmazligi, disk I/O,
    izin hatasi gibi KALICI bir ariza) oldugu gibi yeniden firlatilir --
    cagiran (run) bunu belirgin bir cikis koduyla durdurur, boylece kalici
    bir ariza sessizce loglanan sifir-satir turlarina gizlenmez.

    HER yazma buradan gecer, yalniz an yazmalari degil: spec 11'in
    "locked -> geri cekil ve 3 kez dene" satiri budamayi AYIRMAZ, ustelik
    budama turun en buyuk yazma islemidir (saatte ~65 bin satirlik DELETE),
    yani kilide en cok maruz kalan yer orasidir.
    """
    for attempt in range(LOCK_RETRIES):
        try:
            return work()
        except OperationalError as exc:
            session.rollback()
            if "locked" not in str(exc).lower():
                raise
            if attempt == LOCK_RETRIES - 1:
                log.warning("Yazilamadi (%s): %s", label, exc)
                return 0
            time.sleep(0.2 * (attempt + 1))
    return 0


def _write_with_retry(session: Session, moment: Moment, now: datetime) -> int:
    return _with_lock_retry(session, moment.name, lambda: write_moment(session, moment, now))


def _prune_with_retry(session: Session, older_than: datetime) -> int:
    return _with_lock_retry(session, "budama", lambda: prune(session, older_than))


def run(csv_dir: Path, period_ms: int, retention_min: int, once: bool) -> int:
    """Ana dongu. Cikis kodu: 0 basarili, 2 tablolar yok, 3 kalici db hatasi."""
    moments = read_moments(csv_dir)
    units = sorted({u for m in moments for u, _ in m.files})

    # Sessiz kosan bir simulator bu depoda daha once pahaliya patladi
    # (basla.bat madde 6): ne yaptigini acikca yazar.
    log.info("CSV SIM  -  yazilan her satir CSV'DEN gelir, canli olcum DEGILDIR")
    log.info("  kaynak     : %s", csv_dir)
    log.info("  an sayisi  : %d   uniteler: %s", len(moments), units)
    log.info("  veritabani : %s", settings.db_url())
    log.info(
        "  periyot    : %d ms  (tam tur ~%.0f sn)", period_ms, len(moments) * period_ms / 1000
    )
    log.info("  saklama    : %d dk", retention_min)

    if not inspect(engine).has_table("measurement"):
        log.error("`measurement` tablosu yok. Once semayi uygulayin:")
        log.error("    cd backend && uv run alembic upgrade head")
        return 2

    lap = 0
    with SessionLocal() as session:
        while True:
            lap += 1
            written = 0
            try:
                for moment in moments:
                    now = datetime.now(UTC).replace(tzinfo=None)
                    written += _write_with_retry(session, moment, now)
                    if period_ms > 0:
                        time.sleep(period_ms / 1000)
                deleted = _prune_with_retry(
                    session,
                    older_than=datetime.now(UTC).replace(tzinfo=None)
                    - timedelta(minutes=retention_min),
                )
            except OperationalError as exc:
                # "locked" disi bir OperationalError _with_lock_retry
                # tarafindan buraya yeniden firlatilir: kalici bir DB
                # arizasi (tablo/kolon uyusmazligi, disk I/O, izin hatasi)
                # sessizce sifir-satir bir tura donusmez, acikca durur.
                # BUDAMA da bu blogun icindedir: disarida kalinca "locked"
                # yalniz yazmada yeniden deneniyor, ayni hata budamada
                # yakalanmamis bir istisnayla sureci olduruyordu.
                log.error("Kalici veritabani hatasi, durduruluyor: %s", exc)
                return 3

            log.info("tur %d bitti: %d satir yazildi, %d eski satir budandi", lap, written, deleted)
            if once:
                return 0

            # Tur sonundaki bu bekleme KOSULSUZDUR: an-basi uyku ic dongudedir
            # ve `--period-ms 0` verildiginde hic uyunmaz, yani surekli kip
            # tur basina 131 yazma + 1 DELETE ile serbest kosardi. Tabani
            # burada tutmak `--once`i (test/teshis yolu) yavaslatmaz.
            time.sleep(max(period_ms, MIN_LAP_MS) / 1000)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)-5s %(message)s")
    parser = argparse.ArgumentParser(
        description="veri/ altindaki olcum CSV'lerini yerel veritabanina yazar"
    )
    parser.add_argument("--csv-dir", type=Path, default=settings.csv_dir())
    parser.add_argument("--period-ms", type=int, default=settings.sim_period_ms)
    parser.add_argument("--retention-min", type=int, default=settings.sim_retention_minutes)
    parser.add_argument("--once", action="store_true", help="tek gecis yapip cikar (test/teshis)")
    a = parser.parse_args(argv)
    return run(a.csv_dir, a.period_ms, a.retention_min, a.once)


if __name__ == "__main__":
    raise SystemExit(main())
