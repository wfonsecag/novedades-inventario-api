import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def db_path(tmp_path):
    """Base de datos SQLite temporal y aislada para cada prueba."""
    return str(tmp_path / "test.db")


@pytest.fixture
def client(db_path):
    # El "with" ejecuta el arranque de la aplicación (lifespan), igual que en producción.
    with TestClient(create_app(db_path)) as cliente:
        yield cliente
