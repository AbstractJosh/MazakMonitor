"""Tam kosum kaydi — CSV korpusunun TAMAMI, tek okumada. SALT OKUYUCU.

CANLI YOLA DOKUNMAZ ve dokunamaz: bu modul hub'i, SSE akisini ve DB'yi hic
tanimaz; yalnizca `veri/` altindaki dosyalari okur. csv_replay.py ayni 131
ani donguyle hub'a beslemeye devam eder.

NEDEN AYRI BIR YOL GEREKTI: canli ekran KAYAN BIR PENCERE gosterir
(live.WINDOW = 120 ornek) ama unite basina 131 an vardir — yani canli ekran
kosumun tamamini HICBIR ZAMAN gostermez, tur basa sardikca pencerenin
basindan dokulur. Bu modul ayni dosyalari bastan sona okur.

/api/measurements NEDEN KULLANILMADI: o uc CSV sim'in yazdigi SQLite
tablosunu okur; tablo budanir (varsayilan 60 dk), 500 satirda kirpilir ve
tekrar dongusunun turlari ic ice girer. Tek ve TEMIZ bir kosum oradan
cikarilamaz.

ZAMAN — TELDE AN GONDERILMEZ. CSV'nin zamani DUVAR SAATIDIR (tezgahin disa
aktardigi yerel an) ve saat dilimi TASIMAZ; bir UTC zaman noktasi degildir.
Bu yuzden telde ikiye ayrilir: takvim gunu (`YYYY-MM-DD`) ve gunun saati
(`HH:MM:SS`). Naif bir ISO an gonderseydik arayuz onu tarayici diliminde
cozer, tasarim sisteminin `formatDateTime`i Istanbul'a cevirir ve iki dilim
tutmadigi her makinede kosum saatleri KAYARDI. Ayrimin gerekcesi tasarim
sistemi ADR-0005'te de yazar: an ile takvim gunu ayri kavramlardir.
"""

import math
from dataclasses import dataclass
from pathlib import Path

from app.csv_live import csv_feature_id
from app.domain import CamelModel
from app.sim.csv_reader import Moment, read_measurement, read_moments


class KosumSeries(CamelModel):
    """Kosum boyunca tek bir ozellik yuvasi."""

    # csv_live.csv_feature_id ile BIREBIR ayni kimlik: canli kutucukla kosum
    # cizgisi ayni sinyali ayni adla anar.
    id: str
    unit_no: int
    slot: int
    # Ad CSV kolon basligindan gelir (kuruluma ozel, koda gomulmez) —
    # csv_live.py ile ayni kural ve ayni yedek.
    name: str
    # Bu yuvanin KOSUM BOYU ortalamasi. baselines.py ile ayni tanim ve ayni
    # gerekce; orada canli esigin tabani icin, burada grafigin altinda
    # yazilan baglam icin hesaplanir.
    baseline: float
    min_value: float
    max_value: float
    # Kac anda okundu. Yuvanin kosumun TAMAMINDA mi yoksa bir kisminda mi
    # dolu oldugunu soyler; `count < KosumOut.count` ise iz kopukludur.
    count: int


class KosumRow(CamelModel):
    """Bir an: gunun saati + o anda okunan degerler."""

    day: str
    time: str
    # Seri kimligi -> deger. OKUNMAYAN YUVA ANAHTARSIZDIR: 0 yazmak, hic
    # olculmemis bir yuvayi sifir olculmus gibi cizerdi.
    values: dict[str, float]


class KosumOut(CamelModel):
    """Tam kosum — grafigin tek kaynagi."""

    # Kosumun ilk/son ani. Bos korpusta hepsi None; ekran o zaman bir sey
    # iddia etmez.
    start_day: str | None = None
    start_time: str | None = None
    end_day: str | None = None
    end_time: str | None = None
    # Gercekten okunabilen an sayisi (bozuk/eksik dosyalar dusuldukten sonra).
    count: int = 0
    series: list[KosumSeries] = []
    rows: list[KosumRow] = []


@dataclass
class _Toplayici:
    """Tek yuvanin kosum boyu birikimi — tek gecislik ortalama/min/maks."""

    unit_no: int
    slot: int
    name: str
    total: float = 0.0
    count: int = 0
    min_value: float = math.inf
    max_value: float = -math.inf

    def ekle(self, value: float) -> None:
        self.total += value
        self.count += 1
        self.min_value = min(self.min_value, value)
        self.max_value = max(self.max_value, value)


def build_kosum(root: Path) -> KosumOut:
    """`veri/` altini bastan sona okur ve tam kosumu doner.

    TEK GECIS: seriler, tabanlar ve satirlar ayni okumadan cikar.
    compute_baselines'i ayrica cagirmak 262 dosyayi IKINCI kez okumak
    olurdu ve ortalamanin tanimini iki yerde tutardi.

    Kok ya da CSV yoksa FileNotFoundError yukselir (read_moments'in kurali):
    bos bir kosumla donmek "kosum var ama bosmus" diye okunurdu.
    """
    moments = read_moments(root)

    toplayicilar: dict[str, _Toplayici] = {}
    rows: list[KosumRow] = []
    for moment in moments:
        row = _row(moment, toplayicilar)
        # Tek bir dosyasi bile okunamayan an SATIR URETMEZ: bos bir an
        # grafikte cizgiyi koparirdi ve kopukluk veriden geliyormus gibi
        # gorunurdu.
        if row is not None:
            rows.append(row)

    series = [
        KosumSeries(
            id=fid,
            unit_no=t.unit_no,
            slot=t.slot,
            name=t.name,
            baseline=t.total / t.count,
            min_value=t.min_value,
            max_value=t.max_value,
            count=t.count,
        )
        # Sira SABIT (unite, yuva): grafik renkleri seri sirasina baglidir ve
        # sozluk sirasina birakilmis bir liste, dosya sistemi sirasi degisince
        # butun cizgileri yeniden boyardi.
        for fid, t in sorted(toplayicilar.items(), key=lambda kv: (kv[1].unit_no, kv[1].slot))
    ]

    ilk, son = (rows[0], rows[-1]) if rows else (None, None)
    return KosumOut(
        start_day=ilk.day if ilk else None,
        start_time=ilk.time if ilk else None,
        end_day=son.day if son else None,
        end_time=son.time if son else None,
        count=len(rows),
        series=series,
        rows=rows,
    )


def _row(moment: Moment, toplayicilar: dict[str, _Toplayici]) -> KosumRow | None:
    """Bir anin butun unitelerini okur; satiri uretir ve birikimi besler."""
    values: dict[str, float] = {}
    an: object = None
    day = time = ""

    for unit_no, path in moment.files:
        record = read_measurement(path, unit_no)
        if record is None:
            continue  # bozuk dosya TUM ani dusurmez (csv_replay ile ayni kural)

        if an is None:
            # Anin zamani ILK okunan dosyadan alinir. Iki unitenin dosya adi
            # birebir aynidir (ayni {YYMMDD}_{HHMMSS}) ve csv_reader zaten her
            # dosyada baslik zamani ile satir zamaninin ayni saniyeyi
            # gosterdigini dogrular — yani ikisi ayni ani tasir.
            an = record.source_time
            day = record.source_time.date().isoformat()
            time = record.source_time.strftime("%H:%M:%S")

        for fv in record.features:
            # Degeri olmayan yuva SERI URETMEZ: 10665'in VIBRATION kolonu
            # 131/131 bostur. csv_live.py ve baselines.py ile ayni kural —
            # hic dolmayacak bir cizgi, grafikte kalici bir bosluktan baska
            # bir sey vermez.
            if fv.value is None:
                continue
            fid = csv_feature_id(unit_no, fv.slot)
            values[fid] = fv.value
            t = toplayicilar.get(fid)
            if t is None:
                # Adsiz yuvada csv_live.py ile AYNI yedek kullanilir.
                t = toplayicilar[fid] = _Toplayici(
                    unit_no=unit_no, slot=fv.slot, name=fv.name or f"Özellik {fv.slot}"
                )
            t.ekle(fv.value)

    if an is None or not values:
        return None
    return KosumRow(day=day, time=time, values=values)
