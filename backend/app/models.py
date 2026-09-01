"""Olcum tablolari — CSV tekrar-oynatma simulatorunun yazdigi sema.

Kolon adlari domain.py ile AYNI sozcukleri kullanir (unit_no, channel_nr,
feature_nr, lim_type, level), boylece CONTEXT.md'deki "Kod/kaynak"
karsiliklari tek kalir. domain.py'nin KENDISINE dokunulmaz: o dosya
frontend types.ts ile birebir sozlesmedir.

Sekil UZUN (long) formdur, GENIS degil: iki izleme unitesinin ozellik adlari
FARKLIDIR (10660: SPINDEL / X AXIS / Y AXIS / Z AXIS -- 10665: VIBRATION /
M131 DEBI / M131BASINC / M08 DEBI), dolayisiyla "her ozellige bir kolon" tek
tabloda toplanamaz.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Tum olcum tablolarinin ortak tabani (migrations/env.py buna baglanir)."""


class Measurement(Base):
    """Bir izleme unitesinden bir an — CSV dosyasi basina tek satir."""

    __tablename__ = "measurement"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Sim'in yazdigi an — UTC, naive. "Taze veri" olcusu budur.
    recorded_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    # CSV'nin KENDI zamani (Start date) — yerel, naive. Kaynak kaybolmasin.
    source_time: Mapped[datetime] = mapped_column(DateTime)
    # 10660 / 10665. Dosyanin ICINDE yoktur; klasor adindan gelir.
    unit_no: Mapped[int] = mapped_column(Integer, index=True)
    channel_nr: Mapped[int] = mapped_column(Integer)
    tool_nr: Mapped[int] = mapped_column(Integer)
    program_nr: Mapped[int] = mapped_column(Integer)
    cut_nr: Mapped[int] = mapped_column(Integer)
    workpiece: Mapped[str | None] = mapped_column(String(64))
    alarm: Mapped[int | None] = mapped_column(Integer)
    alarm_limit: Mapped[int | None] = mapped_column(Integer)
    # Hangi dosyadan geldigi — bir deger tuhaf gorundugunde tek izlenebilirlik.
    source_file: Mapped[str] = mapped_column(String(128))

    # passive_deletes: silmeyi DB'ye birak. ORM'in cocuklari tek tek yukleyip
    # silmesi 65 bin satirlik budamada kabul edilemez.
    features: Mapped[list["MeasurementFeature"]] = relationship(
        back_populates="measurement",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="MeasurementFeature.slot",
    )
    limits: Mapped[list["MeasurementLimit"]] = relationship(
        back_populates="measurement",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="MeasurementLimit.limit_nr",
    )

    # Teshis ucunun TEK sorgu sekli: uniteye gore suz, zamana gore sirala.
    __table_args__ = (Index("ix_measurement_unit_time", "unit_no", "recorded_at"),)


class MeasurementFeature(Base):
    """Ozellik (CONTEXT: Ozellik / feature) — an basina 4 satir."""

    __tablename__ = "measurement_feature"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    measurement_id: Mapped[int] = mapped_column(
        ForeignKey("measurement.id", ondelete="CASCADE"), index=True
    )
    slot: Mapped[int] = mapped_column(Integer)
    # Ad kuruluma ozeldir, koda gomulmez: CSV kolon satirindan okunur.
    name: Mapped[str] = mapped_column(String(64))
    # Bos hucre None kalir, 0 OLMAZ: "sensor 0 olctu" ile "sensor yok" ayni
    # sey degildir (10665'te VIBRATION 131/131 bostur).
    value: Mapped[float | None] = mapped_column(Float)
    work_value: Mapped[float | None] = mapped_column(Float)

    measurement: Mapped[Measurement] = relationship(back_populates="features")


class MeasurementLimit(Base):
    """Limit (CONTEXT: Limit) — an basina 0..8 satir; bos yuva satir uretmez."""

    __tablename__ = "measurement_limit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    measurement_id: Mapped[int] = mapped_column(
        ForeignKey("measurement.id", ondelete="CASCADE"), index=True
    )
    limit_nr: Mapped[int] = mapped_column(Integer)
    level: Mapped[float] = mapped_column(Float)
    lim_type: Mapped[int | None] = mapped_column(Integer)
    # Hangi ozellik yuvasina ait (CSV "Limit feature").
    feature_nr: Mapped[int | None] = mapped_column(Integer)

    measurement: Mapped[Measurement] = relationship(back_populates="limits")
