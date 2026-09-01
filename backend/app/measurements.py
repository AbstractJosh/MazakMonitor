"""Olcum teshis ucu — SALT OKUYUCU.

Bu uc, CSV sim'in DB'ye GERCEKTEN yazip yazmadigini gorunur kilar. Ekranda
karsiligi YOKTUR (frontend bu fazda degismedi); tarayicidan Vite'in vekili
uzerinden acilir:  http://<LANIP>:5173/api/measurements

domain.py'ye DOKUNULMAZ - o dosya frontend types.ts ile birebir sozlesmedir.
Buradaki modeller yalnizca bu ucun cevabini tarif eder; ortak olan tek sey
camelCase taban sinifidir.
"""

from datetime import datetime

from fastapi import HTTPException
from pydantic import ConfigDict
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, selectinload

from app.domain import CamelModel
from app.models import Measurement

# Tek istekte donebilecek en fazla satir.
MAX_LIMIT = 500


class _OrmModel(CamelModel):
    """CamelModel + ORM nesnesinden dogrudan dogrulama.

    from_attributes SINIFTA acilir, model_validate cagrisinda DEGIL: cagrideki
    bayrak yalnizca en ust seviyeye uygulanir ve ic ice `features`/`limits`
    listeleri "not a valid dict" ile duserdi.

    ConfigDict pydantic v2'de kalitimla BIRLESIR; CamelModel'in camelCase
    ureteci ve populate_by_name'i korunur.
    """

    model_config = ConfigDict(from_attributes=True)


class FeatureOut(_OrmModel):
    slot: int
    name: str
    value: float | None = None
    work_value: float | None = None


class LimitOut(_OrmModel):
    limit_nr: int
    level: float
    lim_type: int | None = None
    feature_nr: int | None = None


class MeasurementOut(_OrmModel):
    id: int
    # Sim'in yazdigi an (UTC) — tazeligi bu gosterir.
    recorded_at: datetime
    # CSV'nin kendi zamani — kaynagi bu gosterir.
    source_time: datetime
    unit_no: int
    channel_nr: int
    tool_nr: int
    program_nr: int
    cut_nr: int
    workpiece: str | None = None
    alarm: int | None = None
    alarm_limit: int | None = None
    source_file: str
    features: list[FeatureOut] = []
    limits: list[LimitOut] = []


class MeasurementPage(CamelModel):
    # Suzgece uyan TUM satir sayisi (limit'ten etkilenmez): "veri geliyor mu"
    # sorusunun cevabi budur.
    total: int
    measurements: list[MeasurementOut] = []


def _clamp_limit(limit: int) -> int:
    """1..MAX_LIMIT araligina kirpar.

    Ust sinir olmadan `limit=999999` butun tabloyu bellege alirdi; sim
    saniyede 18 satir yaziyor.
    """
    return max(1, min(limit, MAX_LIMIT))


def read_page(db: Session, unit: int | None, limit: int) -> MeasurementPage:
    """En yeni olcumler (istege bagli unite suzgeciyle).

    Tablolar yoksa ciplak 500 DEGIL, ne yapilacagini soyleyen 503 doner.
    `.\\basla.bat` artik HER kosumda `alembic upgrade head` calistirir (ayri
    bir "provis"/"sim" kipi kalmadi), yani betikten baslatilan bir kurulumda
    bu dal beklenmez; elle baslatilan backend (`uv run uvicorn ...`,
    migration'siz) ya da semasi eski kalmis bir DB hala tablosuz olabilir ve
    o zaman bu uca bakan biri sebepsiz bir "Internal Server Error"
    goruyordu. replay.run() ayni durumda zaten bu kalibi kuruyor
    (cikis kodu 2 + "alembic upgrade head"); eksik olan tek yer burasiydi.
    """
    try:
        return _read_page(db, unit, limit)
    except OperationalError as exc:
        # Yalniz "tablo yok" hali cevrilir. Baska bir OperationalError
        # (orn. "database is locked") oldugu gibi kalir: ona semayi
        # uygulamayi onermek yanlis ize sokardi.
        if "no such table" not in str(exc).lower():
            raise
        raise HTTPException(
            status_code=503,
            detail="olcum tablolari yok; once: cd backend && uv run alembic upgrade head",
        ) from exc


def _read_page(db: Session, unit: int | None, limit: int) -> MeasurementPage:
    where_clause = [Measurement.unit_no == unit] if unit is not None else []

    total = db.scalar(select(func.count()).select_from(Measurement).where(*where_clause)) or 0
    rows = db.scalars(
        select(Measurement)
        .where(*where_clause)
        # selectinload: N+1 sorguyu onler — 50 olcum icin 3 sorgu, 101 degil.
        .options(selectinload(Measurement.features), selectinload(Measurement.limits))
        .order_by(Measurement.recorded_at.desc(), Measurement.id.desc())
        .limit(_clamp_limit(limit))
    ).all()

    return MeasurementPage(
        total=total,
        measurements=[MeasurementOut.model_validate(row) for row in rows],
    )
