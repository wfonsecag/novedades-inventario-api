"""Excepciones de dominio. Cada una sabe su código HTTP y su código de error uniforme."""
from typing import Dict, List, Optional


class ErrorDeDominio(Exception):
    status_code = 500
    codigo = "ERROR_INTERNO"

    def __init__(self, mensaje: str, detalles: Optional[List[Dict[str, str]]] = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.detalles = detalles or []

    def como_respuesta(self) -> dict:
        return respuesta_uniforme(self.codigo, self.mensaje, self.detalles)


class JsonInvalidoError(ErrorDeDominio):
    status_code = 400
    codigo = "JSON_INVALIDO"


class ValidacionError(ErrorDeDominio):
    status_code = 422
    codigo = "VALIDACION"


class DuplicadoError(ErrorDeDominio):
    status_code = 409
    codigo = "DUPLICADO"


def detalle(campo: str, problema: str) -> Dict[str, str]:
    return {"campo": campo, "problema": problema}


# Errores del framework (rutas y métodos) traducidos al formato uniforme
CODIGOS_HTTP = {
    404: ("NO_ENCONTRADO", "La ruta solicitada no existe."),
    405: ("METODO_NO_PERMITIDO", "El método HTTP no está permitido en esta ruta."),
}
MENSAJE_ERROR_INTERNO = "Ocurrió un error inesperado. Intenta de nuevo más tarde."


def respuesta_uniforme(codigo: str, mensaje: str, detalles: Optional[List[Dict[str, str]]] = None) -> dict:
    return {"error": codigo, "mensaje": mensaje, "detalles": detalles or []}
