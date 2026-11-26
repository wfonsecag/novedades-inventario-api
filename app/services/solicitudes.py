"""Reglas de negocio para registrar solicitudes (§4 y §9 de 01-contexto.md)."""
import re
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from app.core.errors import ValidacionError, detalle
from app.core.normalization import limpiar_espacios, normalizar_claves, resolver_catalogo
from app.repositories.solicitudes import Repositorio
from app.schemas.solicitud import (
    ESTADO_INICIAL,
    PRIORIDAD_POR_DEFECTO,
    TIPO_POR_DEFECTO,
    Estado,
    Prioridad,
    Solicitud,
    Tipo,
)

ID_MAXIMO = 2**63 - 1  # límite de INTEGER en SQLite
TIENDA_MAX = 200
DESCRIPCION_MAX = 2000
_ENTERO = re.compile(r"^[+-]?\d+$")


def _ahora_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _vacio(valor: Any) -> bool:
    return valor is None or (isinstance(valor, str) and not valor.strip())


class ServicioSolicitudes:
    def __init__(self, repositorio: Repositorio, reloj: Callable[[], datetime] = _ahora_utc):
        self.repositorio = repositorio
        self.reloj = reloj

    def registrar(self, datos: Dict[str, Any]) -> Solicitud:
        datos = normalizar_claves(datos)
        errores: List[Dict[str, str]] = []

        id_ = self._validar_id(datos.get("id"), errores)
        tienda = self._validar_texto(datos.get("tienda"), "tienda", TIENDA_MAX, errores, reducir_internos=True)
        descripcion = self._validar_texto(datos.get("descripcion"), "descripcion", DESCRIPCION_MAX, errores)
        estado = self._validar_estado(datos.get("estado"), errores)
        tipo, tipo_reportado = self._con_valor_por_defecto(datos.get("tipo"), Tipo, TIPO_POR_DEFECTO)
        prioridad, prioridad_reportada = self._con_valor_por_defecto(
            datos.get("prioridad"), Prioridad, PRIORIDAD_POR_DEFECTO
        )

        if errores:
            raise ValidacionError("La solicitud tiene datos inválidos.", errores)

        solicitud = Solicitud(
            id=id_,
            tienda=tienda,
            tipo=tipo,
            tipo_reportado=tipo_reportado,
            descripcion=descripcion,
            prioridad=prioridad,
            prioridad_reportada=prioridad_reportada,
            estado=estado,
            fecha_creacion=self.reloj(),
        )
        self.repositorio.insertar(solicitud)
        return solicitud

    # --- Reglas por campo ---------------------------------------------------

    @staticmethod
    def _validar_id(valor: Any, errores: List[Dict[str, str]]) -> Optional[int]:
        if _vacio(valor):
            errores.append(detalle("id", "Es obligatorio."))
            return None
        if isinstance(valor, bool) or not isinstance(valor, (int, str)):
            errores.append(detalle("id", "Debe ser un número entero."))
            return None
        texto = str(valor).strip()
        if not _ENTERO.match(texto):
            errores.append(detalle("id", "Debe ser un número entero."))
            return None
        numero = int(texto)
        if not 0 < numero <= ID_MAXIMO:
            errores.append(detalle("id", f"Debe ser mayor que 0 y menor o igual a {ID_MAXIMO}."))
            return None
        return numero

    @staticmethod
    def _validar_texto(
        valor: Any, campo: str, maximo: int, errores: List[Dict[str, str]], reducir_internos: bool = False
    ) -> Optional[str]:
        if isinstance(valor, bool) or isinstance(valor, (list, dict)):
            errores.append(detalle(campo, "Debe ser texto."))
            return None
        if _vacio(valor):
            errores.append(detalle(campo, "Es obligatorio y no puede estar vacío."))
            return None
        texto = str(valor)
        texto = limpiar_espacios(texto) if reducir_internos else texto.strip()
        if len(texto) > maximo:
            errores.append(detalle(campo, f"No puede superar {maximo} caracteres (tiene {len(texto)})."))
            return None
        return texto

    @staticmethod
    def _validar_estado(valor: Any, errores: List[Dict[str, str]]) -> Estado:
        if _vacio(valor):
            return ESTADO_INICIAL
        if resolver_catalogo(valor, Estado) is not ESTADO_INICIAL:
            errores.append(
                detalle("estado", f"Una solicitud nueva solo puede crearse en estado '{ESTADO_INICIAL.value}'.")
            )
        return ESTADO_INICIAL

    @staticmethod
    def _con_valor_por_defecto(valor: Any, catalogo: Type, por_defecto: Any) -> Tuple[Any, Optional[str]]:
        """RN-05: si el valor falta o no se reconoce, usa el valor por defecto y conserva el original."""
        miembro = resolver_catalogo(valor, catalogo)
        if miembro is not None:
            return miembro, None
        original = None if _vacio(valor) else str(valor).strip()
        return por_defecto, original
