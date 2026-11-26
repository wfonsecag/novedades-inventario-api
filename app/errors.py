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
        return {"error": self.codigo, "mensaje": self.mensaje, "detalles": self.detalles}


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
