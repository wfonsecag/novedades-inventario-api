from datetime import datetime, timedelta, timezone

import pytest

from app.core.errors import DuplicadoError
from app.repositories.solicitudes import RepositorioSQLite
from app.schemas.solicitud import Estado, Prioridad, Solicitud, Tipo

BASE = datetime(2026, 11, 26, 15, 0, 0, tzinfo=timezone.utc)


def nueva(id_, prioridad=Prioridad.ALTA, estado=Estado.PENDIENTE, minutos=0, descripcion="Faltan 5 unidades"):
    return Solicitud(
        id=id_,
        tienda="Santafé",
        tipo=Tipo.DIFERENCIA_INVENTARIO,
        descripcion=descripcion,
        prioridad=prioridad,
        estado=estado,
        fecha_creacion=BASE + timedelta(minutes=minutos),
    )


@pytest.fixture
def repo(db_path):
    return RepositorioSQLite(db_path)


def test_insertar_y_listar(repo):
    solicitud = nueva(101)

    repo.insertar(solicitud)

    assert repo.listar() == [solicitud]


# CB-05 / RF-09: el duplicado se rechaza y el original no cambia
def test_insertar_duplicado_lanza_error_y_conserva_original(repo):
    original = nueva(101, descripcion="Original")
    repo.insertar(original)

    with pytest.raises(DuplicadoError):
        repo.insertar(nueva(101, descripcion="Intento duplicado"))

    assert repo.listar() == [original]


def test_listar_ordena_por_fecha_y_luego_id(repo):
    repo.insertar(nueva(3, minutos=5))
    repo.insertar(nueva(2, minutos=0))
    repo.insertar(nueva(1, minutos=5))

    assert [s.id for s in repo.listar()] == [2, 1, 3]


def test_listar_filtra_por_estado_prioridad_y_combinados(repo):
    repo.insertar(nueva(1, Prioridad.ALTA, Estado.PENDIENTE))
    repo.insertar(nueva(2, Prioridad.BAJA, Estado.PENDIENTE))
    repo.insertar(nueva(3, Prioridad.ALTA, Estado.RESUELTA))

    assert [s.id for s in repo.listar(estado=Estado.PENDIENTE)] == [1, 2]
    assert [s.id for s in repo.listar(prioridad=Prioridad.ALTA)] == [1, 3]
    assert [s.id for s in repo.listar(estado=Estado.PENDIENTE, prioridad=Prioridad.ALTA)] == [1]
    assert repo.listar(estado=Estado.EN_PROCESO) == []


# CB-21 / RF-10: los datos sobreviven a un "reinicio" (nueva instancia sobre el mismo archivo)
def test_los_datos_persisten_al_reabrir(db_path):
    RepositorioSQLite(db_path).insertar(nueva(101))

    assert [s.id for s in RepositorioSQLite(db_path).listar()] == [101]
