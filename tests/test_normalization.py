import pytest

from app.core.errors import ValidacionError
from app.core.normalization import limpiar_espacios, normalizar_claves, resolver_catalogo
from app.schemas.solicitud import Estado, Prioridad, Tipo


# CB-11: variantes de escritura se resuelven al valor canónico
@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("Diferencia de inventario", Tipo.DIFERENCIA_INVENTARIO),
        ("diferencia de inventario", Tipo.DIFERENCIA_INVENTARIO),
        ("error_en_traslado", Tipo.ERROR_TRASLADO),
        ("ERROR EN TRASLADO", Tipo.ERROR_TRASLADO),
        ("  mercancia averiada ", Tipo.MERCANCIA_AVERIADA),
        ("Mercancía-Averiada", Tipo.MERCANCIA_AVERIADA),
        ("error  de   referencia", Tipo.ERROR_REFERENCIA),
        ("otro", Tipo.OTRO),
    ],
)
def test_resolver_tipo_normaliza_variantes(entrada, esperado):
    assert resolver_catalogo(entrada, Tipo) is esperado


def test_resolver_prioridad_y_estado():
    assert resolver_catalogo("ALTA", Prioridad) is Prioridad.ALTA
    assert resolver_catalogo(" baja ", Prioridad) is Prioridad.BAJA
    assert resolver_catalogo("en_proceso", Estado) is Estado.EN_PROCESO
    assert resolver_catalogo("pendiente", Estado) is Estado.PENDIENTE


@pytest.mark.parametrize("entrada", ["Robo", "Altísima", 1, "123"])
def test_resolver_valor_desconocido_devuelve_none(entrada):
    assert resolver_catalogo(entrada, Tipo) is None
    assert resolver_catalogo(entrada, Prioridad) is None


@pytest.mark.parametrize("entrada", [None, "", "   "])
def test_resolver_valor_ausente_devuelve_none(entrada):
    assert resolver_catalogo(entrada, Tipo) is None


# CB-15: nombres de campo con mayúscula, tilde o espacios
def test_normalizar_claves_acepta_variantes_de_escritura():
    datos = {"ID": 101, "Tienda": "Santafé", "Descripción": "Faltan 5", "Fecha Creación": "x", "tipo-reportado": "y"}

    resultado = normalizar_claves(datos)

    assert resultado == {
        "id": 101,
        "tienda": "Santafé",
        "descripcion": "Faltan 5",
        "fecha_creacion": "x",
        "tipo_reportado": "y",
    }


# CB-22: dos campos que normalizan al mismo nombre son ambiguos
def test_normalizar_claves_rechaza_campos_ambiguos():
    with pytest.raises(ValidacionError) as error:
        normalizar_claves({"descripcion": "a", "Descripción": "b"})

    assert error.value.detalles[0]["campo"] == "descripcion"


def test_limpiar_espacios_recorta_y_reduce_repetidos():
    assert limpiar_espacios("  Santa    Fé  ") == "Santa Fé"
