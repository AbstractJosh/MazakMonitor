"""CSV taban cizgileri: her ozelligin TUM degerlerinin ortalamasi.

NEDEN VAR: CSV'nin kendi `Limit 1..8` kolonlari 10665 unitesinde
KULLANILAMAZ. Olculdu (262 dosyanin tamami):

    10660  SPINDEL      limit 110-150   ortalama 113,4   -> ~%103
    10660  X/Y/Z AXIS   limit 110-168   ortalama 107-124 -> ~%100
    10665  M131 DEBI    limit  50       ortalama 212,9   -> ~%426
    10665  M131BASINC   limit  35       ortalama 101,5   -> ~%290
    10665  M08 DEBI     limit  50       ortalama 224,1   -> ~%448

10665'te iz, limit cizgisinin DORT KATI yukseklikte akar: cizgi grafigin
tabanina yapisir, yuzde rozeti kalici olarak %400'un ustunde durur. Ikisi de
bilgi tasimaz. Bu modul esigi verinin KENDISINDEN turetir; sapma yuzdesini
EKLEMEZ, onu kullanici secer (bkz. frontend/src/domain/esik.ts).

TABAN NEDEN TUM DOSYALARDAN: cizilen pencere WINDOW=120 ornektir ama unite
basina 131 an vardir — pencere veri kumesinin tamami DEGILDIR. Ortalamayi
pencereden almak, tekrar dongusu basa sardikca cizgiyi oynatirdi; dosyalardan
alinan taban ise sabittir.
"""

from collections.abc import Iterable
from pathlib import Path

from app.sim.csv_reader import Moment, read_measurement

# (unite no, ozellik yuvasi) -> o yuvanin tum CSV degerlerinin ortalamasi.
Baselines = dict[tuple[int, int], float]


def compute_baselines(moments: Iterable[Moment]) -> Baselines:
    """Anlarin TUM dosyalarini okur, yuva basina ortalamayi doner.

    DEGERI OLMAYAN YUVA GIRIS URETMEZ: 10665'in VIBRATION kolonu 131/131
    bostur ve limit yuvasi (170) dolu olsa bile tek bir degeri yoktur. Bos bir
    ortalamanin (0 ya da None) yerine hic anahtar uretmemek, csv_live.py'nin o
    ozelligi hic kurmamasiyla ayni kuraldir.

    Bozuk dosya TUM tabani dusurmez (read_measurement None doner): o dosya
    atlanir, kalanlarin ortalamasi yine dogru cikar — csv_replay'in
    `_read_and_write` icindeki ayni kural.
    """
    toplam: dict[tuple[int, int], float] = {}
    adet: dict[tuple[int, int], int] = {}

    for moment in moments:
        for unit_no, path in moment.files:
            _biriktir(toplam, adet, unit_no, path)

    return {key: toplam[key] / adet[key] for key in toplam}


def _biriktir(
    toplam: dict[tuple[int, int], float],
    adet: dict[tuple[int, int], int],
    unit_no: int,
    path: Path,
) -> None:
    record = read_measurement(path, unit_no)
    if record is None:
        return
    for fv in record.features:
        if fv.value is None:
            continue
        key = (unit_no, fv.slot)
        toplam[key] = toplam.get(key, 0.0) + fv.value
        adet[key] = adet.get(key, 0) + 1
