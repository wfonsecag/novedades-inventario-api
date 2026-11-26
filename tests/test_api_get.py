from datetime import datetime, timedelta, timezone

import pytest

from app.repositories.solicitudes import RepositorioSQLite
from app.schemas.solicitud import Estado, Prioridad, Solicitud, Tipo

BASE = datetime(2026, 11, 26, 15, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def datos(client, db_path):
    """Carga solicitudes con distintos estados y prioridades directamente en la base."""
    repo = RepositorioSQLite(db_path)
    combinaciones = [
        (1, Prioridad.ALTA, Estado.PENDIENTE),
        (2, Prioridad.BAJA, Estado.PENDIENTE),
        (3, Prioridad.ALTA, Estado.EN_PROCESO),
        (4, Prioridad.MEDIA, Estado.EN_PROCESO),
    ]
    for minuto, (id_, prioridad, estado) in enumerate(combinaciones):
        repo.insertar(Solicitud(
            id=id_, tienda="Santafé", tipo=Tipo.DIFERENCIA_INVENTARIO, descripcion="Faltan 5 unidades",
            prioridad=prioridad, estado=estado, fecha_creacion=BASE + timedelta(minutes=minuto),
        ))
    return client


def ids(respuesta):
    assert respuesta.status_code == 200
    return [s["id"] for s in respuesta.json()]


# RF-02
def test_get_sin_datos_devuelve_lista_vacia(client):
    assert ids(client.get("/solicitudes")) == []


def test_get_devuelve_todas_ordenadas_por_fecha(datos):
    assert ids(datos.get("/solicitudes")) == [1, 2, 3, 4]


# RF-03, RF-04, RF-05
def test_get_filtra_por_estado(datos):
    assert ids(datos.get("/solicitudes", params={"estado": "En proceso"})) == [3, 4]


def test_get_filtra_por_prioridad(datos):
    assert ids(datos.get("/solicitudes", params={"prioridad": "Alta"})) == [1, 3]


def test_get_combina_filtros(datos):
    assert ids(datos.get("/solicitudes", params={"estado": "Pendiente", "prioridad": "Alta"})) == [1]


# CB-19: escritura distinta y parámetro vacío
def test_get_normaliza_filtros(datos):
    assert ids(datos.get("/solicitudes", params={"estado": "en_proceso", "prioridad": "ALTA"})) == [3]


def test_get_filtro_vacio_equivale_a_sin_filtro(datos):
    assert ids(datos.get("/solicitudes?estado=&prioridad=")) == [1, 2, 3, 4]


# CB-20
def test_get_sin_coincidencias_devuelve_lista_vacia(datos):
    assert ids(datos.get("/solicitudes", params={"estado": "Resuelta"})) == []


# CB-18
def test_get_filtro_desconocido_responde_422_con_valores_admitidos(datos):
    respuesta = datos.get("/solicitudes", params={"prioridad": "urgente", "estado": "abierto"})

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["error"] == "VALIDACION"
    detalles = {d["campo"]: d["problema"] for d in cuerpo["detalles"]}
    assert "Alta, Media, Baja" in detalles["prioridad"]
    assert "Pendiente, En proceso, Resuelta" in detalles["estado"]


def test_get_parametros_no_definidos_se_ignoran(datos):
    assert ids(datos.get("/solicitudes", params={"tipo": "Otro"})) == [1, 2, 3, 4]


# Lo registrado por POST se puede consultar (integración de punta a punta)
def test_get_devuelve_lo_registrado_por_post(client):
    client.post("/solicitudes", json={"id": 7, "tienda": "Oviedo", "descripcion": "Caja rota", "prioridad": "baja"})

    respuesta = client.get("/solicitudes", params={"prioridad": "Baja"})

    assert [(s["id"], s["tienda"], s["prioridad"]) for s in respuesta.json()] == [(7, "Oviedo", "Baja")]
