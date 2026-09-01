from pathlib import Path

from app.sim.baselines import compute_baselines
from app.sim.csv_reader import Moment, read_moments

BASLIK = """Program ; 0
Channel ; 1
Tool ; 11
Cut ; 0
Start date ; 2026-08-10 11:23:02.192
End date ; 2026-08-10 11:23:02.192
File version ; 1

Time (s) ; Date ; Time ; Workpiece ID ; SPINDEL ; Work SPINDEL ; VIBRATION ; Work VIBRATION ; Y AXIS ; Work Y AXIS ; Z AXIS ; Work Z AXIS ; Alarm ; Alarm limit ; Teach-In ; Setup ; Rework ; Limit 1 ; Limit type ; Limit feature ; Limit 2 ; Limit type ; Limit feature ; Limit 3 ; Limit type ; Limit feature ; Limit 4 ; Limit type ; Limit feature ; Limit 5 ; Limit type ; Limit feature ; Limit 6 ; Limit type ; Limit feature ; Limit 7 ; Limit type ; Limit feature ; Limit 8 ; Limit type ; Limit feature
"""


def _yaz(klasor: Path, ad: str, spindel: str, vibration: str = "") -> None:
    """Tek satirlik gercek bicimde bir CSV yazar (41 kolon, `;` ayrac)."""
    kolonlar = [
        "0",
        "10.08.2026",
        "11:23:02",
        "",
        spindel,
        "87",
        vibration,
        "",
        "96",
        "85",
        "96",
        "91",
        "",
        "",
        "",
        "",
        "",
    ]
    # 8 limit yuvasi: yalnizca ilki dolu (yuva 1 -> SPINDEL).
    kolonlar += ["110", "1", "1"] + [""] * 21
    klasor.mkdir(parents=True, exist_ok=True)
    (klasor / ad).write_text(BASLIK + " ; ".join(kolonlar) + "\n", encoding="utf-8")


def _kok(tmp_path: Path) -> list[Moment]:
    _yaz(tmp_path / "10660", "a_260810_112302.csv", "100")
    _yaz(tmp_path / "10660", "b_260810_112303.csv", "120")
    _yaz(tmp_path / "10660", "c_260810_112304.csv", "140")
    return read_moments(tmp_path)


def test_yuva_ortalamasi_tum_dosyalardan_gelir(tmp_path: Path):
    tabanlar = compute_baselines(_kok(tmp_path))
    # (100 + 120 + 140) / 3
    assert tabanlar[(10660, 1)] == 120.0


def test_degeri_olmayan_yuva_GIRIS_URETMEZ(tmp_path: Path):
    """10665'in VIBRATION kolonu 131/131 bostur.

    Bos bir ortalama (0 ya da None) uretmek yerine hic anahtar uretilmez —
    csv_live.py'nin o ozelligi hic kurmamasiyla ayni kural.
    """
    tabanlar = compute_baselines(_kok(tmp_path))
    assert (10660, 2) not in tabanlar


def test_uniteler_AYRI_ortalanir(tmp_path: Path):
    """Iki unitenin ozellik adlari farklidir; ayni yuva numarasi ayni sey degil."""
    _yaz(tmp_path / "10660", "a_260810_112302.csv", "100")
    _yaz(tmp_path / "10665", "a_260810_112302.csv", "200")
    tabanlar = compute_baselines(read_moments(tmp_path))
    assert tabanlar[(10660, 1)] == 100.0
    assert tabanlar[(10665, 1)] == 200.0


def test_bozuk_dosya_TABANI_DUSURMEZ(tmp_path: Path):
    """Okunamayan dosya atlanir, kalanlarin ortalamasi yine dogru cikar."""
    moments = _kok(tmp_path)
    (tmp_path / "10660" / "d_260810_112305.csv").write_text("bu bir CSV degil\n", encoding="utf-8")
    tabanlar = compute_baselines(read_moments(tmp_path))
    assert tabanlar[(10660, 1)] == 120.0
    assert len(moments) == 3


def test_hic_dosya_yoksa_BOS_doner():
    assert compute_baselines([]) == {}
