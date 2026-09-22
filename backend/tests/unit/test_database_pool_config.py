import pytest
from unittest.mock import patch
from app.core.config import settings


def test_database_pool_config_defaults():
    assert settings.DB_POOL_SIZE == 3
    assert settings.DB_MAX_OVERFLOW == 2
    assert settings.DB_POOL_TIMEOUT == 30
    assert settings.DB_POOL_RECYCLE == 1800
    assert settings.SCAN_MAX_WORKERS == 2


def test_database_engine_sqlite_kwargs():
    with patch("sqlalchemy.create_engine") as mock_create_engine:
        with patch.object(settings, "DATABASE_URL", "sqlite:///./test.db"):
            # Re-import database module to trigger engine creation logic
            import importlib
            import app.core.database
            importlib.reload(app.core.database)

            mock_create_engine.assert_called_once()
            args, kwargs = mock_create_engine.call_args
            assert args[0] == "sqlite:///./test.db"
            assert kwargs.get("connect_args") == {"check_same_thread": False}
            assert "pool_size" not in kwargs


def test_database_engine_postgres_kwargs():
    with patch("sqlalchemy.create_engine") as mock_create_engine:
        with patch.object(settings, "DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb"):
            import importlib
            import app.core.database
            importlib.reload(app.core.database)

            mock_create_engine.assert_called_once()
            args, kwargs = mock_create_engine.call_args
            assert args[0] == "postgresql://user:pass@localhost:5432/testdb"
            assert kwargs.get("connect_args") == {}
            assert kwargs.get("pool_size") == 3
            assert kwargs.get("max_overflow") == 2
            assert kwargs.get("pool_timeout") == 30
            assert kwargs.get("pool_recycle") == 1800
            assert kwargs.get("pool_pre_ping") is True

    # Reload database module back to default sqlite setting for remaining tests
    import importlib
    import app.core.database
    importlib.reload(app.core.database)
