from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.models import Base

# Alembic Config nesnesi (alembic.ini degerlerine erisim)
config = context.config

# DB URL'i tek kaynaktan al: app/config.py (env'den okur).
#
# db_url() cagrilir, HAM `database_url` alani DEGIL: o alan .env yokken bos
# stringtir ve create_engine("") "Could not parse SQLAlchemy URL" ile duser.
# Etkin URL'i (yoksa veri/mazak.db) yalnizca db_url() bilir; app/db.py da
# ondan okur - iki yol AYNI veritabanini acmali.
config.set_main_option("sqlalchemy.url", settings.db_url())

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model metadata'si. (Import yukarida: app.models yalnizca sqlalchemy'den
# turer - settings'e, config'e ya da URL'e hicbir bagi yok, yani siralama
# zorunlulugu YOKTUR. conftest.py'deki noqa'lar bunun aksine GERCEK bir
# zorunluluk tasir: orada os.environ import'lardan once yazilmali.)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()