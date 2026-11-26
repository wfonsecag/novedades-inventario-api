from fastapi.testclient import TestClient

from app.main import create_app


def assert_formato_error(respuesta, status, codigo):
    assert respuesta.status_code == status
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"error", "mensaje", "detalles"}
    assert cuerpo["error"] == codigo
    return cuerpo


# CB-26 / RF-07
def test_ruta_inexistente_responde_404_con_formato_uniforme(client):
    assert_formato_error(client.get("/no-existe"), 404, "NO_ENCONTRADO")


def test_metodo_no_soportado_responde_405_con_formato_uniforme(client):
    respuesta = client.delete("/solicitudes")
    assert_formato_error(respuesta, 405, "METODO_NO_PERMITIDO")
    assert "allow" in respuesta.headers  # se conserva el encabezado estándar del 405


# RNF-04: un error interno responde 500 sin exponer detalles
def test_error_interno_responde_500_sin_exponer_detalles(db_path, monkeypatch):
    with TestClient(create_app(db_path), raise_server_exceptions=False) as cliente:
        def fallar(**_):
            raise RuntimeError("detalle interno sensible")

        monkeypatch.setattr(cliente.app.state.servicio, "listar", fallar)
        respuesta = cliente.get("/solicitudes")

    cuerpo = assert_formato_error(respuesta, 500, "ERROR_INTERNO")
    assert "sensible" not in respuesta.text
    assert cuerpo["detalles"] == []
