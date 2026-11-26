# ADR-0001 · Persistencia en SQLite

- **Estado:** Aceptado
- **Fecha:** 2026-11-26
- **Relacionado con:** RF-09, RF-10, RNF-01, RNF-05 (`01-contexto.md`)

## Contexto

Tenía dos opciones de persistencia: en memoria o SQLite. El objetivo de negocio es **dar seguimiento** a las novedades, así que perder los registros al reiniciar contradice el propósito. Además necesito **evitar duplicados por identificador**, incluso si dos peticiones llegan al mismo tiempo, y quiero que cualquier persona pueda ejecutar la solución sin instalar servicios.

## Decisión

Uso **SQLite** mediante el módulo estándar `sqlite3` de Python, sin ORM, detrás de una interfaz de repositorio.

- Una tabla `solicitudes` con `id INTEGER PRIMARY KEY`: la **base de datos** garantiza la unicidad; un duplicado se detecta por `IntegrityError` y se traduce a HTTP 409.
- La ruta del archivo se configura con la variable de entorno `DATABASE_PATH` (por defecto `novedades.db`). El archivo se crea solo al iniciar (`CREATE TABLE IF NOT EXISTS`) y no se versiona.
- Las pruebas usan una base **temporal y aislada por prueba**; la prueba de persistencia (CB-21) usa un archivo temporal para simular el reinicio.

## Alternativas consideradas

| Alternativa | Por qué la descarté |
|---|---|
| **Diccionario en memoria** *(decisión descartada)* | Pierde todos los datos al reiniciar, lo que contradice "dar seguimiento". Además, la unicidad ante peticiones simultáneas exige programar un bloqueo propio, que es más código y más riesgo que delegarlo a la llave primaria. |
| ORM (SQLAlchemy) | Añade una dependencia y una capa de abstracción que una sola tabla no justifica. |
| Motor de base de datos cliente-servidor | Requiere instalar y operar un servidor: va contra RNF-01 (ejecutable con pocos pasos) para un prototipo. Es el destino natural cuando el sistema crezca (ver limitaciones). |

## Consecuencias

**Positivas**
- Persistencia real sin instalar nada (`sqlite3` viene con Python).
- Unicidad atómica garantizada por el motor, no por código propio.
- SQL estándar: migrar a un motor más robusto implica cambiar solo la implementación del repositorio.

**Negativas / limitaciones**
- SQLite serializa las escrituras: no es apto para varias instancias del servicio ni para escritura intensiva. **Limitación para la siguiente versión:** migrar a un motor cliente-servidor más robusto cuando haya más de una instancia o volumen real; la elección concreta dependerá del estándar tecnológico de la organización.
- Se abre una conexión por petición: simple y segura entre hilos, aunque no es lo más eficiente; suficiente para el volumen de un prototipo.
