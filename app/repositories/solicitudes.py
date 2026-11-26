"""Persistencia. El servicio depende de la interfaz Repositorio, no de SQLite (ADR-0001)."""
import sqlite3
from contextlib import closing
from typing import List, Optional, Protocol

from app.core.errors import DuplicadoError, detalle
from app.schemas.solicitud import Estado, Prioridad, Solicitud

_CREAR_TABLA = """
CREATE TABLE IF NOT EXISTS solicitudes (
    id                  INTEGER PRIMARY KEY,
    tienda              TEXT NOT NULL,
    tipo                TEXT NOT NULL,
    tipo_reportado      TEXT,
    descripcion         TEXT NOT NULL,
    prioridad           TEXT NOT NULL,
    prioridad_reportada TEXT,
    estado              TEXT NOT NULL,
    fecha_creacion      TEXT NOT NULL
)
"""

_COLUMNAS = (
    "id", "tienda", "tipo", "tipo_reportado", "descripcion",
    "prioridad", "prioridad_reportada", "estado", "fecha_creacion",
)


class Repositorio(Protocol):
    def insertar(self, solicitud: Solicitud) -> None: ...

    def listar(
        self, estado: Optional[Estado] = None, prioridad: Optional[Prioridad] = None
    ) -> List[Solicitud]: ...


class RepositorioSQLite:
    def __init__(self, db_path: str):
        self.db_path = db_path
        with closing(self._conectar()) as conexion, conexion:
            conexion.execute(_CREAR_TABLA)

    def _conectar(self) -> sqlite3.Connection:
        conexion = sqlite3.connect(self.db_path)
        conexion.row_factory = sqlite3.Row
        return conexion

    def insertar(self, solicitud: Solicitud) -> None:
        fila = solicitud.model_dump(mode="json")
        marcadores = ", ".join("?" for _ in _COLUMNAS)
        sql = f"INSERT INTO solicitudes ({', '.join(_COLUMNAS)}) VALUES ({marcadores})"
        try:
            with closing(self._conectar()) as conexion, conexion:
                conexion.execute(sql, [fila[c] for c in _COLUMNAS])
        except sqlite3.IntegrityError as error:
            # La llave primaria garantiza la unicidad, incluso con peticiones simultáneas.
            raise DuplicadoError(
                f"Ya existe una solicitud con id {solicitud.id}.",
                [detalle("id", "El identificador ya fue registrado.")],
            ) from error

    def listar(
        self, estado: Optional[Estado] = None, prioridad: Optional[Prioridad] = None
    ) -> List[Solicitud]:
        condiciones, parametros = [], []
        if estado is not None:
            condiciones.append("estado = ?")
            parametros.append(estado.value)
        if prioridad is not None:
            condiciones.append("prioridad = ?")
            parametros.append(prioridad.value)
        donde = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
        sql = f"SELECT * FROM solicitudes {donde} ORDER BY fecha_creacion, id"
        with closing(self._conectar()) as conexion:
            filas = conexion.execute(sql, parametros).fetchall()
        return [Solicitud(**dict(fila)) for fila in filas]
