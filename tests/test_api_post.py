import json

import pytest

EJEMPLO = {
    "ID": "101", "Tienda": "Santafé", "Tipo": "diferencia de inventario",
    "Descripción": "Faltan 5 unidades", "Prioridad": "ALTA", "Estado": "Pendiente",
}


def assert_formato_error(respuesta, status, codigo):
    assert respuesta.status_code == status
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"error", "mensaje", "detalles"}
    assert cuerpo["error"] == codigo
    return cuerpo


# RF-01: ejemplo de punta a punta
def test_post_registra_solicitud_y_responde_201(client):
    respuesta = client.post("/solicitudes", json=EJEMPLO)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert {k: v for k, v in cuerpo.items() if k != "fecha_creacion"} == {
        "id": 101,
        "tienda": "Santafé",
        "tipo": "Diferencia de inventario",
        "tipo_reportado": None,
        "descripcion": "Faltan 5 unidades",
        "prioridad": "Alta",
        "prioridad_reportada": None,
        "estado": "Pendiente",
    }
    assert cuerpo["fecha_creacion"].endswith("Z")


# CB-05 / RF-09
def test_post_duplicado_responde_409(client):
    client.post("/solicitudes", json=EJEMPLO)

    cuerpo = assert_formato_error(client.post("/solicitudes", json=EJEMPLO), 409, "DUPLICADO")
    assert "101" in cuerpo["mensaje"]


# RF-06 / RF-07
def test_post_datos_invalidos_responde_422_con_detalle_por_campo(client):
    cuerpo = assert_formato_error(client.post("/solicitudes", json={"id": "abc", "tienda": "Santafé"}), 422, "VALIDACION")
    assert [d["campo"] for d in cuerpo["detalles"]] == ["id", "descripcion"]


# CB-17: cuerpo vacío, JSON mal formado, no objeto o bytes no UTF-8
@pytest.mark.parametrize("contenido", [b"", b"   ", b"{id:1", b"[]", b'"texto"', b"123", b"\xff\xfe"])
def test_post_cuerpo_invalido_responde_400(client, contenido):
    respuesta = client.post("/solicitudes", content=contenido, headers={"Content-Type": "application/json"})
    assert_formato_error(respuesta, 400, "JSON_INVALIDO")


# CB-25: sin Content-Type o con uno distinto, si el cuerpo es JSON válido se acepta
@pytest.mark.parametrize("headers", [{}, {"Content-Type": "text/plain"}])
def test_post_sin_content_type_json_se_acepta(client, headers):
    respuesta = client.post("/solicitudes", content=json.dumps(EJEMPLO).encode("utf-8"), headers=headers)
    assert respuesta.status_code == 201
