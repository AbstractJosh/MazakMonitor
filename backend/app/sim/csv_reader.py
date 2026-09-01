"""Provis olcum CSV'si -> dataclass. DB bilmez, zaman bilmez, dongu bilmez.

Bicim (`veri/<unite>/{program}_{kanal}_{takim}_{cut}_{YYMMDD}_{HHMMSS}.csv`):

    0  Program ; 0
    1  Channel ; 1
    2  Tool ; 11
    3  Cut ; 0
    4  Start date ; 2026-08-10 11:23:02.192
    5  End date ; 2026-08-10 11:23:02.192
    6  File version ; 1
    7  (bos)
    8  Time (s) ; Date ; Time ; Workpiece ID ; SPINDEL ; Work SPINDEL ; ...
    9  0 ; 10.08.2026 ; 11:23:02 ;  ; 115 ; 87 ; ...

Veri satiri 41 kolondur:

    0      Time (s)                  <- ALINMAZ: tek satirlik dosyada hep 0
    1,2    Date, Time
    3      Workpiece ID
    4..11  4 x (ozellik degeri, Work degeri)
    12,13  Alarm, Alarm limit
    14..16 Teach-In, Setup, Rework   <- ALINMAZ: 262/262 bos
    17..40 8 x (Limit N, Limit type, Limit feature)

Ozellik ADLARI kolon satirindan okunur, koda GOMULMEZ: adlar kuruluma
ozeldir (config.promos3_feature_names'in ayni gerekcesi).

UNITE NUMARASI DOSYANIN ICINDE YOKTUR; klasor adindan gelir ve cagirandan
parametre olarak alinir.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)

# Veri satirindaki kolon sayisi (262/262 dogrulandi). Uymazsa dosya atlanir.
COLUMN_COUNT = 41
FEATURE_SLOTS = 4
LIMIT_SLOTS = 8

_FIRST_FEATURE_COL = 4  # (deger, Work deger) ciftleri buradan baslar
_FIRST_LIMIT_COL = 17  # (Limit, tip, ozellik) ucluleri buradan baslar


@dataclass(frozen=True)
class FeatureValue:
    """Bir ozellik yuvasinin o andaki degeri."""

    slot: int
    name: str
    value: float | None
    work_value: float | None


@dataclass(frozen=True)
class LimitValue:
    """Bir limit yuvasi. Bos yuvalar hic uretilmez."""

    limit_nr: int
    level: float
    lim_type: int | None
    feature_nr: int | None


@dataclass(frozen=True)
class MeasurementRecord:
    """Bir uniteden bir an — tek CSV dosyasinin tamami."""

    unit_no: int
    source_time: datetime
    channel_nr: int
    tool_nr: int
    program_nr: int
    cut_nr: int
    workpiece: str | None
    alarm: int | None
    alarm_limit: int | None
    source_file: str
    features: list[FeatureValue]
    limits: list[LimitValue]


def _cells(line: str) -> list[str]:
    """`;` ile bol, her hucreyi kirp. Degerler bosluklarla sarilidir."""
    return [p.strip() for p in line.split(";")]


def _header_value(line: str) -> str:
    """`Tool ; 11` -> `11`."""
    _, _, value = line.partition(";")
    return value.strip()


def _to_int(cell: str) -> int | None:
    return int(cell) if cell else None


def _to_float(cell: str) -> float | None:
    return float(cell) if cell else None


def read_measurement(path: Path, unit_no: int) -> MeasurementRecord | None:
    """Tek CSV -> kayit. Bicim beklenene uymazsa None doner ve neden loglanir.

    Sessizce yanlis kolondan deger okumaktansa o ani HIC yazmamak yegdir:
    DB'ye girmis yanlis bir deger, kaynagindan artik ayirt edilemez.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        # UnicodeDecodeError OSError DEGILDIR (ValueError'dan turer) ve tek bir
        # UTF-8 disi bayt TUM sim'i oldururdu: ozellik adlari operatorun yazdigi
        # Turkce/Almanca etiketlerdir, yani cp1254 ile kaydedilmis bir dosya
        # gercekci bir giristir. errors="replace" ile okumak yerine dosyayi
        # ATLIYORUZ: bozuk bir ad sessizce DB'ye girerse kaynagindan artik
        # ayirt edilemez.
        log.warning("CSV okunamadi: %s (%s)", path.name, exc)
        return None

    if len(lines) < 10:
        log.warning("CSV cok kisa (%d satir): %s", len(lines), path.name)
        return None

    version = _header_value(lines[6])
    if version != "1":
        # Baska bir surum baska bir yerlesim demektir; tahmin etmeyiz.
        log.warning("Bilinmeyen File version %r: %s", version, path.name)
        return None

    headers = _cells(lines[8])
    values = _cells(lines[9])
    if len(headers) != COLUMN_COUNT or len(values) != COLUMN_COUNT:
        log.warning(
            "Beklenen %d kolon; baslik=%d veri=%d: %s",
            COLUMN_COUNT,
            len(headers),
            len(values),
            path.name,
        )
        return None

    try:
        return _parse(path, unit_no, lines, headers, values)
    except ValueError as exc:
        log.warning("Sayi cozulemedi: %s (%s)", path.name, exc)
        return None


def _parse(
    path: Path,
    unit_no: int,
    lines: list[str],
    headers: list[str],
    values: list[str],
) -> MeasurementRecord | None:
    """Sayisal cozme. ValueError firlatabilir; cagiran yakalar."""
    # fromisoformat hem ".192" olan hem olmayan bicimi kabul eder.
    source_time = datetime.fromisoformat(_header_value(lines[4]))

    # Satirdaki Date/Time ile basligin Start date'i AYNI ani gostermeli
    # (262/262 boyle). Tutmuyorsa dosyanin iki yarisi farkli anlardandir.
    row_moment = f"{values[1]} {values[2]}"
    if row_moment != source_time.strftime("%d.%m.%Y %H:%M:%S"):
        log.warning("Baslik/satir zamani tutmadi (%s): %s", row_moment, path.name)
        return None

    features: list[FeatureValue] = []
    for slot_idx in range(FEATURE_SLOTS):
        i = _FIRST_FEATURE_COL + slot_idx * 2
        name = headers[i]
        # "Work <ad>" eslesmesi kolon hizasinin KANITIDIR. Tutmuyorsa
        # yerlesim varsaydigimiz gibi degildir ve dosya atlanir.
        if headers[i + 1] != f"Work {name}":
            log.warning(
                "Kolon hizasi tutmadi (%r / %r): %s", name, headers[i + 1], path.name
            )
            return None
        features.append(
            FeatureValue(
                slot=slot_idx + 1,
                name=name,
                value=_to_float(values[i]),
                work_value=_to_float(values[i + 1]),
            )
        )

    limits: list[LimitValue] = []
    for limit_idx in range(LIMIT_SLOTS):
        i = _FIRST_LIMIT_COL + limit_idx * 3
        if not values[i]:
            continue  # bos yuva satir uretmez (bu veride 5..8 hep bos)
        limits.append(
            LimitValue(
                limit_nr=limit_idx + 1,
                level=float(values[i]),
                lim_type=_to_int(values[i + 1]),
                feature_nr=_to_int(values[i + 2]),
            )
        )

    return MeasurementRecord(
        unit_no=unit_no,
        source_time=source_time,
        program_nr=int(_header_value(lines[0])),
        channel_nr=int(_header_value(lines[1])),
        tool_nr=int(_header_value(lines[2])),
        cut_nr=int(_header_value(lines[3])),
        workpiece=values[3] or None,
        alarm=_to_int(values[12]),
        alarm_limit=_to_int(values[13]),
        source_file=path.name,
        features=features,
        limits=limits,
    )


@dataclass(frozen=True)
class Moment:
    """Bir an: ayni dosya adini tasiyan (unite no, yol) ciftleri.

    Iki unitenin dosya adlari BIREBIR AYNIDIR, bu yuzden eslestirme anahtari
    dosya adidir. Bir uniteden eksik olan an DIGER unite icin yine uretilir:
    bu veride 54 ve 99 ikisinde de eksiktir, ama bu genel kural degildir.
    """

    name: str
    files: list[tuple[int, Path]]


def read_moments(root: Path) -> list[Moment]:
    """`veri/` altini tarar, anlari zaman sirasinda dondurur.

    Unite numarasi KLASOR ADIDIR; sayisal olmayan klasorler atlanir.
    Kok, unite klasoru YA DA CSV yoksa FileNotFoundError yukselir - sim'in bos
    bir listeyle sessizce donmesi "calisiyor ama hicbir sey yazmiyor" demek
    olurdu. Ucuncu hal (klasorler var, icleri bos) run()'in TEK bekleme
    noktasini da atlatiyordu: an-basi uyku ic dongudedir, bos listede o dongu
    hic donmez ve `while True` tur basina bir DELETE+COMMIT ile serbest kosar
    (olculdu: ~3000 tur/sn, %100 CPU, SQLite yazma kilidi surekli tutulur).
    """
    if not root.is_dir():
        raise FileNotFoundError(f"CSV kok dizini yok: {root}")

    units = [
        (int(c.name), c) for c in sorted(root.iterdir()) if c.is_dir() and c.name.isdigit()
    ]
    if not units:
        raise FileNotFoundError(f"{root} altinda unite klasoru yok (orn. 10660)")

    by_name: dict[str, list[tuple[int, Path]]] = {}
    for unit_no, folder in units:
        for csv in folder.glob("*.csv"):
            by_name.setdefault(csv.name, []).append((unit_no, csv))

    if not by_name:
        raise FileNotFoundError(f"{root} altindaki unite klasorlerinde CSV yok")

    # Dosya adi ...{YYMMDD}_{HHMMSS}.csv ile bittigi ve takim numarasi zamanla
    # arttigi icin ALFABETIK sira zaman sirasidir; ayrica ayristirmaya gerek yok.
    return [Moment(name=name, files=by_name[name]) for name in sorted(by_name)]
