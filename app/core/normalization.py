"""Reglas de forma: se aceptan variantes de escritura con una sola interpretación posible."""
import re
import unicodedata
from enum import Enum
from typing import Any, Dict, Optional, Type, TypeVar

from app.core.errors import ValidacionError, detalle

E = TypeVar("E", bound=Enum)


def _sin_tildes(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def _forma_plana(texto: str) -> str:
    """Minúsculas, sin tildes, '_' y '-' como espacio, espacios repetidos reducidos."""
    texto = _sin_tildes(texto).lower().replace("_", " ").replace("-", " ")
    return " ".join(texto.split())


def limpiar_espacios(texto: str) -> str:
    """Quita espacios al inicio y al final y reduce los repetidos internos."""
    return " ".join(texto.split())


def normalizar_claves(datos: Dict[str, Any]) -> Dict[str, Any]:
    """Normaliza nombres de campo ('Descripción' -> 'descripcion'). Rechaza colisiones."""
    resultado: Dict[str, Any] = {}
    originales: Dict[str, str] = {}
    for clave, valor in datos.items():
        normalizada = _forma_plana(str(clave)).replace(" ", "_")
        if normalizada in resultado:
            raise ValidacionError(
                "La solicitud tiene campos repetidos con distinta escritura.",
                [detalle(normalizada, f"Recibido como '{originales[normalizada]}' y como '{clave}'.")],
            )
        resultado[normalizada] = valor
        originales[normalizada] = str(clave)
    return resultado


def resolver_catalogo(valor: Any, catalogo: Type[E]) -> Optional[E]:
    """Devuelve el miembro del catálogo que corresponde al valor, o None si no se reconoce."""
    if valor is None:
        return None
    plano = _forma_plana(str(valor))
    if not plano:
        return None
    for miembro in catalogo:
        if _forma_plana(miembro.value) == plano:
            return miembro
    return None
