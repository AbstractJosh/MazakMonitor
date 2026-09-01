# Test ortami: app.config import edilmeden ONCE ayarlanmali.
# PROMOS3_ENABLED=false -> lifespan giris adaptorunu baslatmaz, yani testler
# 1789'u dinlemeye kalkmaz (ve gercekten kosan bir gateway/simulator ile port
# icin yarismaz).
import os
import tempfile
from pathlib import Path

# UC KAYNAGIN DA kapatilmasi gerekir. Yalniz PROMOS3_ENABLED'i kapatmak
# artik yetmez: lifespan ayrica 1790'i dinleyen ikinci bir Promos3
# adaptoru ve GECICI DB'ye yazan bir CSV adaptoru kurardi.
os.environ["PROMOS3_ENABLED"] = "false"
os.environ["PROMOS3_SIM_ENABLED"] = "false"
os.environ["CSV_REPLAY_ENABLED"] = "false"

# Testler ASLA veri/mazak.db'ye yazmaz: URL gecici bir dosyaya sabitlenir.
# Bu da app.config'ten ONCE olmali - Settings ortami ice aktarma aninda okur.
_TEST_DB = Path(tempfile.mkdtemp(prefix="mazak-test-")) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{_TEST_DB.as_posix()}"

# Testler CSV'yi HER ZAMAN depodaki veri/ altindan okur. Ayni gerekce:
# test_csv_reader.py ve test_replay.py "262 dosya", "131 an", "uniteler ==
# {10660, 10665}" gibi HARFI iddialar tasiyor; ortaminda (ya da backend/.env
# icinde) SIM_CSV_DIR tanimli bir gelistirici sebebi hic belli olmayan 15+
# hata alirdi. Bu da app.config'ten ONCE olmali.
os.environ["SIM_CSV_DIR"] = str(Path(__file__).resolve().parents[2] / "veri")

import pytest  # noqa: E402 - DATABASE_URL env'i bu importtan ONCE sabitlenmeli

from app.db import engine  # noqa: E402 - DATABASE_URL env'i bu importtan ONCE sabitlenmeli
from app.models import Base  # noqa: E402 - ayni neden


@pytest.fixture
def anyio_backend() -> str:
    # Async testler anyio isaretiyle kosar; tek backend: asyncio (trio kurulu degil).
    return "asyncio"


@pytest.fixture
def db_bos():
    """Her testte bos ve taze tablolar.

    Migration DEGIL metadata kullanilir: testin dogruladigi sey semanin
    SEKLIDIR, alembic'in kendisi degil. Migration ayri bir adimda kosulur.
    """
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
