"""Catálogos (valores admitidos) y modelo de salida. Único lugar donde se definen."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class Tipo(str, Enum):
    DIFERENCIA_INVENTARIO = "Diferencia de inventario"
    MERCANCIA_AVERIADA = "Mercancía averiada"
    ERROR_TRASLADO = "Error en traslado"
    ERROR_REFERENCIA = "Error de referencia"
    OTRO = "Otro"


class Prioridad(str, Enum):
    ALTA = "Alta"
    MEDIA = "Media"
    BAJA = "Baja"


class Estado(str, Enum):
    PENDIENTE = "Pendiente"
    EN_PROCESO = "En proceso"
    RESUELTA = "Resuelta"


# Valores por defecto configurables (RN-05)
TIPO_POR_DEFECTO = Tipo.OTRO
PRIORIDAD_POR_DEFECTO = Prioridad.MEDIA
ESTADO_INICIAL = Estado.PENDIENTE


class Solicitud(BaseModel):
    id: int
    tienda: str
    tipo: Tipo
    tipo_reportado: Optional[str] = None
    descripcion: str
    prioridad: Prioridad
    prioridad_reportada: Optional[str] = None
    estado: Estado
    fecha_creacion: datetime
