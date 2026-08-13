from sqlalchemy import text

from evalforge.core.config import Settings
from evalforge.infrastructure.database import (
    create_database_engine,
    create_session_factory,
)


def test_database_engine_and_session_factory() -> None:
    settings = Settings(
        _env_file=None,
        database_url="sqlite+pysqlite:///:memory:",
        database_echo=False,
    )

    engine = create_database_engine(settings)
    session_factory = create_session_factory(engine)

    try:
        with session_factory() as session:
            result = session.execute(text("SELECT 1")).scalar_one()

        assert engine.url.drivername == "sqlite+pysqlite"
        assert result == 1
    finally:
        engine.dispose()
