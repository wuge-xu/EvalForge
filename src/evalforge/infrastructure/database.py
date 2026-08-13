from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from evalforge.core.config import Settings, get_settings


def create_database_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url,
        echo=settings.database_echo,
        pool_pre_ping=True,
    )


def create_session_factory(
    engine: Engine,
) -> sessionmaker[Session]:
    return sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )


@lru_cache
def get_engine() -> Engine:
    return create_database_engine(get_settings())


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return create_session_factory(get_engine())


def reset_database_caches() -> None:
    get_session_factory.cache_clear()

    if get_engine.cache_info().currsize:
        get_engine().dispose()

    get_engine.cache_clear()


def check_database_connection(
    engine: Engine,
) -> tuple[str, str]:
    with engine.connect() as connection:
        database_name = connection.execute(text("SELECT current_database()")).scalar_one()

        vector_version = connection.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        ).scalar_one()

    return str(database_name), str(vector_version)
