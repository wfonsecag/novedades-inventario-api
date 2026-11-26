from datetime import datetime, timezone

import pytest

from app.errors import DuplicadoError, ValidacionError
from app.repository import RepositorioSQLite
from app.schemas import Estado, Prioridad, Tipo
from app.service import ServicioSolicitudes

AHORA = datetime(2026, 11, 26, 15, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def repo(db_path):
    return RepositorioSQLite(db_path)


@pytest.fixture
def servicio(repo):
    return ServicioSolicitudes(repo, reloj=lambda: AHORA)


def base(**cambios):
    datos = {"id": 101, "tienda": "Santafé", "descripcion": "Faltan 5 unidades"}
    datos.update(cambios)
    return datos


def campos_con_error(error):
    return [d["campo"] for d in error.value.detalles]


# --- Caso feliz con la escritura real de un canal (CB-11, CB-15, RN-02, RN-03) ---
def test_registra_ejemplo_con_variantes_de_escritura(servicio, repo):
    datos = {
        "ID": " 101 ", "Tienda": "Santafé", "Tipo": "diferencia de inventario",
        "Descripción": "Faltan 5 unidades", "Prioridad": "ALTA", "Estado": "Pendiente",
    }

    s = servicio.registrar(datos)

    assert (s.id, s.tienda, s.tipo, s.prioridad, s.estado) == (
        101, "Santafé", Tipo.DIFERENCIA_INVENTARIO, Prioridad.ALTA, Estado.PENDIENTE,
    )
    assert s.tipo_reportado is None and s.prioridad_reportada is None
    assert s.fecha_creacion == AHORA
    assert repo.listar() == [s]


# --- id (CB-01 a CB-04) ---
@pytest.mark.parametrize("valor", [101, "101", " 101 "])
def test_id_acepta_entero_o_texto_numerico(servicio, valor):
    assert servicio.registrar(base(id=valor)).id == 101


@pytest.mark.parametrize("valor", ["abc", 0, -5, "-5", 101.5, "101.0", True, None, "", 2**63])
def test_id_invalido_se_rechaza(servicio, valor):
    with pytest.raises(ValidacionError) as error:
        servicio.registrar(base(id=valor))
    assert campos_con_error(error) == ["id"]


# --- Obligatorios (CB-06, CB-07) ---
def test_campos_obligatorios_ausentes_reportan_todos_los_errores(servicio, repo):
    with pytest.raises(ValidacionError) as error:
        servicio.registrar({})
    assert campos_con_error(error) == ["id", "tienda", "descripcion"]
    assert repo.listar() == []  # RN-07


@pytest.mark.parametrize("campo", ["tienda", "descripcion"])
@pytest.mark.parametrize("valor", [None, "", "   "])
def test_texto_obligatorio_vacio_o_nulo_se_rechaza(servicio, campo, valor):
    with pytest.raises(ValidacionError) as error:
        servicio.registrar(base(**{campo: valor}))
    assert campos_con_error(error) == [campo]


# --- tienda (CB-08, CB-09, CB-24) ---
def test_tienda_larga_con_tilde_se_conserva_y_reduce_espacios(servicio):
    nombre = "Tienda Santafé " + "x" * 135
    s = servicio.registrar(base(tienda=f"  {nombre.replace(' ', '   ')}  "))
    assert s.tienda == nombre


def test_tienda_mayor_a_200_caracteres_se_rechaza(servicio):
    with pytest.raises(ValidacionError):
        servicio.registrar(base(tienda="x" * 201))


def test_tienda_numerica_se_convierte_a_texto(servicio):
    assert servicio.registrar(base(tienda=1234)).tienda == "1234"


@pytest.mark.parametrize("campo", ["tienda", "descripcion"])
@pytest.mark.parametrize("valor", [True, [], {"a": 1}])
def test_texto_con_tipo_de_dato_invalido_se_rechaza(servicio, campo, valor):
    with pytest.raises(ValidacionError) as error:
        servicio.registrar(base(**{campo: valor}))
    assert campos_con_error(error) == [campo]


# --- descripcion (CB-10) ---
def test_descripcion_respeta_texto_interno_y_limite(servicio):
    assert servicio.registrar(base(descripcion="  Faltan  5\nunidades  ")).descripcion == "Faltan  5\nunidades"
    assert len(servicio.registrar(base(id=102, descripcion="x" * 2000)).descripcion) == 2000
    with pytest.raises(ValidacionError):
        servicio.registrar(base(id=103, descripcion="x" * 2001))


# --- Valores por defecto trazables (CB-12, CB-13, CB-23, RN-05, RN-06) ---
def test_tipo_desconocido_queda_como_otro_con_original(servicio):
    s = servicio.registrar(base(tipo="Robo"))
    assert (s.tipo, s.tipo_reportado) == (Tipo.OTRO, "Robo")


@pytest.mark.parametrize("cambios", [{}, {"tipo": None}, {"tipo": "  "}, {"tipo": "otro"}])
def test_tipo_ausente_u_otro_explicito_no_guarda_original(servicio, cambios):
    s = servicio.registrar(base(**cambios))
    assert (s.tipo, s.tipo_reportado) == (Tipo.OTRO, None)


def test_prioridad_desconocida_queda_media_con_original(servicio):
    s = servicio.registrar(base(prioridad="Altísima"))
    assert (s.prioridad, s.prioridad_reportada) == (Prioridad.MEDIA, "Altísima")


def test_prioridad_ausente_queda_media_sin_original(servicio):
    s = servicio.registrar(base())
    assert (s.prioridad, s.prioridad_reportada) == (Prioridad.MEDIA, None)


def test_prioridad_no_textual_se_convierte_a_texto(servicio):
    s = servicio.registrar(base(prioridad=1))
    assert (s.prioridad, s.prioridad_reportada) == (Prioridad.MEDIA, "1")


def test_tipo_otro_no_modifica_prioridad_enviada(servicio):
    s = servicio.registrar(base(tipo="Robo", prioridad="alta"))
    assert (s.tipo, s.prioridad) == (Tipo.OTRO, Prioridad.ALTA)


# --- estado (CB-14, RN-02) ---
@pytest.mark.parametrize("valor", [None, "", "pendiente", "PENDIENTE"])
def test_estado_ausente_o_pendiente_queda_pendiente(servicio, valor):
    assert servicio.registrar(base(estado=valor)).estado == Estado.PENDIENTE


@pytest.mark.parametrize("valor", ["Resuelta", "en proceso", "abierto"])
def test_estado_distinto_de_pendiente_se_rechaza(servicio, valor):
    with pytest.raises(ValidacionError) as error:
        servicio.registrar(base(estado=valor))
    assert campos_con_error(error) == ["estado"]


# --- Campos ignorados (CB-16, RF-08) ---
def test_campos_extra_y_fecha_del_cliente_se_ignoran(servicio):
    s = servicio.registrar(base(canal="WhatsApp", fecha_creacion="2020-01-01"))
    assert s.fecha_creacion == AHORA
    assert "canal" not in s.model_dump()


# --- Duplicados (RF-09) ---
def test_duplicado_se_rechaza(servicio):
    servicio.registrar(base())
    with pytest.raises(DuplicadoError):
        servicio.registrar(base(descripcion="Otra"))
