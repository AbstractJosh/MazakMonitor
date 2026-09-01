from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

_URL = settings.db_url()
_SQLITE = _URL.startswith("sqlite")

# check_same_thread: SQLite baglantisi varsayilan olarak kendi thread'ine
# kilitlidir; FastAPI istekleri havuzdan farkli thread'lerde alir.
engine = create_engine(
    _URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if _SQLITE else {},
)


@event.listens_for(engine, "connect")
def _configure_sqlite_pragmas(dbapi_conn, _record) -> None:
    """SQLite'in iki varsayilani bu semada YANLIS sonuc verir - sessizce.

    - foreign_keys VARSAYILAN OLARAK KAPALIDIR. Acilmazsa ON DELETE CASCADE
      hic calismaz: budama olcum satirini siler, ozellik ve limit satirlari
      yetim kalir. Hicbir hata verilmez, dosya sessizce buyur.
    - journal_mode=WAL: sim YAZARKEN teshis ucu OKUYABILSIN. Iki AYRI surec
      ayni dosyayi acar; varsayilan journal'da yazan okuru kilitler ve
      /api/measurements "database is locked" ile duser.
    """
    if not _SQLITE:
        return
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
