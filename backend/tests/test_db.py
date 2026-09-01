"""DB URL cozumu ve SQLite PRAGMA'lari."""

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import text

from app.config import Settings, settings
from app.db import engine

# <depo>/backend — alembic.ini burada durur.
_BACKEND = Path(__file__).resolve().parents[1]


def test_db_url_bos_env_ile_sqlite_dosyasina_duser():
    """Sifir kurulumla calismak icin varsayilan yerel bir dosyadir."""
    s = Settings(database_url="")
    url = s.db_url()
    assert url.startswith("sqlite+pysqlite:///")
    assert url.endswith("/veri/mazak.db")


def test_db_url_env_verilirse_o_kazanir():
    """.env'deki DATABASE_URL varsayilani EZER (.env.example'daki niyet)."""
    s = Settings(database_url="postgresql+psycopg://kul@sunucu/alp")
    assert s.db_url() == "postgresql+psycopg://kul@sunucu/alp"


def test_alembic_database_url_yokken_de_kosar():
    """migrations/env.py ETKIN url'i (db_url()) kullanir, ham alani DEGIL.

    Ham `database_url` .env yokken bos stringtir; env.py onu okudugu surece
    `alembic upgrade head` her zaman "Could not parse SQLAlchemy URL" ile
    duserdi - yani `.\\basla.bat csv` varsayilan kurulumda hic baslamazdi.

    Alt surec sarttir: alembic'i ice aktarmak env.py'yi kosturur ve
    fileConfig() bu surecin loglamasini yeniden yapilandirirdi. "--sql"
    cevrimdisi kiptir: SQL'i basar, hicbir veritabanina BAGLANMAZ.
    """
    ortam = dict(os.environ)
    ortam.pop("DATABASE_URL", None)  # conftest test db'sini burada devre disi birak
    sonuc = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        cwd=_BACKEND,
        env=ortam,
        capture_output=True,
        text=True,
    )
    assert sonuc.returncode == 0, sonuc.stderr
    assert "CREATE TABLE measurement" in sonuc.stdout


def test_csv_dizini_varsayilani_depo_kokundeki_veri():
    s = Settings(sim_csv_dir="")
    assert s.csv_dir().name == "veri"
    assert (s.csv_dir() / "10660").is_dir()


def test_testler_csv_kokunu_ortamdan_bagimsiz_okur():
    """conftest SIM_CSV_DIR'i depodaki veri/ ile sabitler (DATABASE_URL gibi).

    test_csv_reader.py ve test_replay.py "262 dosya", "131 an", "uniteler ==
    {10660, 10665}" gibi HARFI iddialar tasir. Sabitleme olmadan, ortaminda
    (ya da backend/.env icinde) SIM_CSV_DIR tanimli bir gelistirici sebebi
    hic belli olmayan 15+ test hatasi alirdi.
    """
    veri = _BACKEND.parent / "veri"
    assert os.environ["SIM_CSV_DIR"] == str(veri)
    assert settings.csv_dir() == veri


def test_sqlite_pragmalari_acik():
    """Ikisi de SESSIZ hata kaynagidir; kapali olurlarsa hicbir sey patlamaz.

    foreign_keys kapaliysa budama cocuk satirlarini yetim birakir; WAL yoksa
    sim yazarken teshis ucu 'database is locked' ile duser.
    """
    with engine.connect() as c:
        assert c.execute(text("PRAGMA foreign_keys")).scalar() == 1
        assert c.execute(text("PRAGMA journal_mode")).scalar() == "wal"
