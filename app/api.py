"""Capa HTTP: recibe la petición, delega en el servicio y arma la respuesta."""
import json

from fastapi import APIRouter, Request

from app.errors import JsonInvalidoError
from app.schemas import Solicitud
from app.service import ServicioSolicitudes

router = APIRouter(prefix="/solicitudes", tags=["Solicitudes"])

_EJEMPLO_POST = {
    "id": 101,
    "tienda": "Santafé",
    "tipo": "Diferencia de inventario",
    "descripcion": "Faltan 5 unidades",
    "prioridad": "Alta",
    "estado": "Pendiente",
}


def _servicio(request: Request) -> ServicioSolicitudes:
    return request.app.state.servicio


async def _leer_json(request: Request) -> dict:
    """Lee el cuerpo como JSON aunque falte el Content-Type (CB-25)."""
    crudo = await request.body()
    if not crudo.strip():
        raise JsonInvalidoError("El cuerpo de la solicitud está vacío; se esperaba un objeto JSON.")
    try:
        datos = json.loads(crudo)
    except (ValueError, UnicodeDecodeError):
        raise JsonInvalidoError("El cuerpo de la solicitud no es un JSON válido.") from None
    if not isinstance(datos, dict):
        raise JsonInvalidoError("El cuerpo de la solicitud debe ser un objeto JSON ({...}).")
    return datos


@router.post(
    "",
    response_model=Solicitud,
    status_code=201,
    summary="Registrar una solicitud",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {"application/json": {"schema": {"type": "object"}, "example": _EJEMPLO_POST}},
        }
    },
    responses={400: {"description": "JSON inválido"}, 409: {"description": "id duplicado"},
               422: {"description": "Datos inválidos"}},
)
async def registrar_solicitud(request: Request) -> Solicitud:
    datos = await _leer_json(request)
    return _servicio(request).registrar(datos)
