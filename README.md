# API de novedades de inventario

Prototipo de API REST para que las tiendas reporten **novedades de inventario** por cualquier canal y el equipo responsable pueda centralizarlas, identificar prioridades y darles seguimiento.

- `POST /solicitudes` registra una novedad, valida y normaliza los datos, asigna la fecha de creación y evita duplicados por identificador.
- `GET /solicitudes` consulta las novedades con filtros opcionales y combinables por `estado` y `prioridad`.
- Persistencia en **SQLite**: los datos sobreviven a un reinicio sin instalar ningún servicio.

**Stack:** Python 3.10+ · FastAPI · Pydantic v2 · SQLite (`sqlite3` estándar) · pytest

---

## Cómo ejecutar

**Requisitos:** Python 3.10 o superior.

```powershell
git clone https://github.com/wfonsecag/novedades-inventario-api.git
cd novedades-inventario-api

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS

pip install -r requirements.txt
uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Documentación interactiva (Swagger): `http://127.0.0.1:8000/docs`
- Estado del servicio: `http://127.0.0.1:8000/health`

La base de datos se crea sola en `novedades.db`. Para usar otro archivo: `$env:DATABASE_PATH = "otra.db"` (PowerShell) o `export DATABASE_PATH=otra.db` (Linux / macOS).

## Cómo probar

```powershell
pytest -v
```

**100 pruebas** automatizadas (unidad, integración con SQLite y API). Cada prueba usa una base temporal propia. El detalle de los casos, con resultado esperado y observado, las pruebas manuales y la matriz de trazabilidad está en [`docs/03-casos-de-prueba.md`](docs/03-casos-de-prueba.md).

## Ejemplos de uso

**Registrar** (se aceptan mayúsculas, tildes e `id` como texto):

```json
POST /solicitudes
{ "ID": "101", "Tienda": "Santafé", "Tipo": "diferencia de inventario",
  "Descripción": "Faltan 5 unidades", "Prioridad": "ALTA" }
```

```json
201 Created
{ "id": 101, "tienda": "Santafé", "tipo": "Diferencia de inventario", "tipo_reportado": null,
  "descripcion": "Faltan 5 unidades", "prioridad": "Alta", "prioridad_reportada": null,
  "estado": "Pendiente", "fecha_creacion": "2026-11-26T15:52:38Z" }
```

**Consultar:** `GET /solicitudes?estado=pendiente&prioridad=alta`

**Error** (formato uniforme en todas las respuestas de error):

```json
409 Conflict
{ "error": "DUPLICADO", "mensaje": "Ya existe una solicitud con id 101.",
  "detalles": [ { "campo": "id", "problema": "El identificador ya fue registrado." } ] }
```

| Código | Cuándo |
|---|---|
| `201` / `200` | Registro / consulta exitosa |
| `400` | Cuerpo vacío o JSON mal formado |
| `409` | `id` duplicado |
| `422` | Dato obligatorio ausente o inválido; filtro con valor no reconocido |
| `404` / `405` / `500` | Ruta inexistente / método no permitido / error interno (sin exponer detalles) |

## Supuestos principales

El detalle completo está en [`docs/01-contexto.md`](docs/01-contexto.md). Los más relevantes:

- **Tolerante con la forma, estricta con el significado.** Acepto y normalizo variantes de escritura (mayúsculas, tildes, espacios, número como texto, nombres de campo como `Descripción`); rechazo con un mensaje claro solo lo que no se puede interpretar.
- `id`, `tienda` y `descripcion` son obligatorios. El `id` lo asigna el canal.
- **Tipos admitidos:** Diferencia de inventario, Mercancía averiada, Error en traslado, Error de referencia, Otro. **Prioridades:** Alta, Media, Baja. **Estados:** Pendiente, En proceso, Resuelta.
- La **prioridad la declara el canal**. Si `tipo` o `prioridad` faltan o no se reconocen, asigno `Otro` / `Media` y conservo el texto original en `tipo_reportado` / `prioridad_reportada`, para no perder ninguna novedad real.
- Toda solicitud nueva nace en `Pendiente`; la fecha de creación la asigna el servidor en UTC.
- Los campos no definidos se ignoran, para que los canales puedan evolucionar sin romper la integración.

## Decisión descartada y limitación

- **Descarté la persistencia en memoria (diccionario).** Pierde los datos al reiniciar, lo que contradice el objetivo de dar seguimiento, y obliga a programar un bloqueo propio para evitar duplicados simultáneos. Con SQLite la llave primaria garantiza la unicidad. Ver [ADR-0001](docs/adr/0001-persistencia-sqlite.md).
- **Limitación para la siguiente versión:** SQLite no es apto para varias instancias ni para escritura intensiva; el siguiente paso sería un motor cliente-servidor más robusto, cambiando solo el paquete `repositories`. También quedan pendientes el cambio de estado de una solicitud (PUT/PATCH), la paginación de la consulta y la autenticación.

## Estructura del proyecto

```
novedades-inventario-api/
├── app/
│   ├── main.py                     # crea la aplicación y los manejadores de error
│   ├── config.py                   # configuración (DATABASE_PATH)
│   ├── api/solicitudes.py          # capa HTTP: endpoints
│   ├── services/solicitudes.py     # capa de negocio: reglas de validación y registro
│   ├── repositories/solicitudes.py # capa de persistencia: SQLite
│   ├── schemas/solicitud.py        # catálogos y modelo de salida
│   └── core/
│       ├── errors.py               # errores de dominio y formato uniforme
│       └── normalization.py        # normalización de campos y valores
├── tests/                          # pruebas automatizadas (pytest)
├── docs/                           # documentación del proceso (ver abajo)
├── requirements.txt
└── pytest.ini
```

Dependencias en un solo sentido: `api → services → repositories`. Ver [ADR-0003](docs/adr/0003-arquitectura-por-capas.md).

## Documentación

Trabajé con **Spec-Driven Development**: primero especifiqué, luego decidí, luego desglosé en tareas y solo entonces construí, con pruebas antes del código en cada tarea.

| Documento | Contenido |
|---|---|
| [`00-experiencia.md`](docs/00-experiencia.md) | Tres proyectos en los que participé: problema, tecnologías, contribución, decisión difícil y qué cambiaría hoy |
| [`01-contexto.md`](docs/01-contexto.md) | Alcance, requisitos funcionales y no funcionales, entradas y salidas, reglas de negocio, casos borde y supuestos |
| [`adr/`](docs/adr/) | Decisiones: SQLite, FastAPI y arquitectura por capas, con alternativas descartadas |
| [`02-spec.md`](docs/02-spec.md) | Plan de construcción en tareas T0–T10 y flujo de ramas |
| [`03-casos-de-prueba.md`](docs/03-casos-de-prueba.md) | Pruebas automatizadas y manuales, resultado esperado y observado, trazabilidad |
| [`04-diseno-evolucion.md`](docs/04-diseno-evolucion.md) | Diseño de notificaciones de prioridad Alta y validación de tienda contra catálogo externo |
| [`05-bitacora-ia.md`](docs/05-bitacora-ia.md) | Uso de inteligencia artificial en el proceso |
| [`06-bitacora-trabajo.md`](docs/06-bitacora-trabajo.md) | Registro cronológico del trabajo |

**Flujo de ramas (Git Flow):** `main` solo recibe versiones publicadas; `develop` integra; cada tarea se desarrolla en una rama `feature/*` (o `refactor/*`) que se fusiona con `--no-ff`; la versión se prepara en `release/1.0.0` y se publica con el tag `v1.0.0`. Se puede ver con `git log --graph --oneline --all`.

## Dependencias

| Paquete | Uso | Licencia |
|---|---|---|
| FastAPI | Framework web | MIT |
| Pydantic | Modelos y serialización | MIT |
| Uvicorn | Servidor ASGI | BSD-3-Clause |
| pytest | Pruebas | MIT |
| httpx | Cliente HTTP para `TestClient` | BSD-3-Clause |

Todos los datos usados son ficticios.

## Tiempo invertido

**Tiempo real invertido:** 2 horas.
