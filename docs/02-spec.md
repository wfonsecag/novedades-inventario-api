# 02 · Spec y plan de construcción

Este documento define **en qué orden** construyo la solución especificada en `01-contexto.md` con las decisiones de `docs/adr/`. Cada tarea es pequeña, verificable y se cierra con un commit.

---

## 1. Método de trabajo

Sigo **Spec-Driven Development**: primero especifico (contexto), luego decido (ADR), luego desgloso (este documento) y solo entonces construyo. Cada fase cierra con una revisión antes de avanzar.

| Fase | Pregunta | Entregable |
|---|---|---|
| 1. Especificar | ¿Qué y por qué? | `01-contexto.md` |
| 2. Decidir | ¿Cómo? | `adr/0001` a `adr/0003` |
| 3. Desglosar | ¿En qué orden? | `02-spec.md` |
| 4. Construir | — | Código y pruebas (T0–T6) |
| 5. Verificar | ¿Cumple lo especificado? | `03-casos-de-prueba.md` (T7) |
| 6. Diseñar la evolución | Notificaciones y catálogo de tiendas | `04-diseno-evolucion.md` (T9) |
| 7. Entregar | — | README, bitácoras, release `v1.0.0` (T8, T10) |

### Ciclo de cada tarea de código (TDD ligero)

1. **Defino** qué archivos toco y qué comportamiento espero.
2. **Escribo la prueba** y confirmo que falla.
3. **Escribo el código mínimo** para que pase.
4. **Ejecuto** `pytest` completo y reviso el diff.
5. **Hago commit** con el mensaje definido en la tarea.
6. **Registro** hora y avance en `06-bitacora-trabajo.md`.

**Definición de terminado (aplica a todas las tareas):** las pruebas nuevas y las anteriores pasan, el código respeta las capas del ADR-0003 y el commit referencia la tarea.

---

## 2. Tareas

### T0 · Esqueleto del proyecto
- **Rama:** `feature/esqueleto`
- **Archivos:** `requirements.txt`, `pytest.ini`, `app/__init__.py`, `app/main.py`, `app/config.py`, `tests/conftest.py`, `tests/test_health.py`
- **Qué hace:** fábrica de la app (`create_app`), ruta `GET /health`, ruta de la base de datos por `DATABASE_PATH`, fixture de pruebas con base temporal aislada.
- **Cubre:** RNF-01, RNF-03
- **Terminado cuando:** `uvicorn app.main:app` arranca y `pytest` pasa la prueba de `/health`.
- **Commit:** `chore(T0): crear esqueleto FastAPI con health check y fixture de pruebas`

### T1 · Normalización y catálogos
- **Rama:** `feature/modelo-persistencia`
- **Archivos:** `app/core/normalization.py`, `app/schemas/solicitud.py`, `app/core/errors.py`, `tests/test_normalization.py`
- **Qué hace:** catálogos `Tipo`, `Prioridad`, `Estado`; funciones para normalizar nombres de campo (con detección de ambigüedad), valores de texto y resolución contra catálogo; modelo de salida `Solicitud`; excepciones de dominio (`ValidacionError`, `DuplicadoError`, `JsonInvalidoError`).
- **Cubre:** RF-11, CB-11, CB-15, CB-22
- **Terminado cuando:** las variantes de escritura resuelven al valor canónico y los nombres de campo ambiguos se detectan.
- **Commit:** `feat(T1): agregar catálogos y normalización de campos y valores`

### T2 · Repositorio SQLite
- **Rama:** `feature/modelo-persistencia` (misma rama que T1)
- **Archivos:** `app/repositories/solicitudes.py`, `tests/test_repository.py`
- **Qué hace:** crea la tabla si no existe; `insertar` (traduce `IntegrityError` a `DuplicadoError`); `listar` con filtros opcionales y orden por `fecha_creacion`, `id`.
- **Cubre:** RF-09, RF-10, RNF-05, CB-05, CB-21
- **Terminado cuando:** inserta y lista, rechaza el duplicado sin alterar el original y los datos persisten al reabrir el archivo.
- **Commit:** `feat(T2): implementar repositorio SQLite con unicidad por id`

### T3 · Servicio de solicitudes
- **Rama:** `feature/registro-solicitudes`
- **Archivos:** `app/services/solicitudes.py`, `tests/test_service.py`
- **Qué hace:** valida y convierte `id`, `tienda`, `descripcion`; aplica valores por defecto trazables a `tipo` y `prioridad`; fija estado `Pendiente`; asigna `fecha_creacion` en UTC; ignora campos no definidos.
- **Cubre:** RF-06, RF-08, RF-12, RN-01 a RN-07, CB-01 a CB-04, CB-06 a CB-14, CB-16, CB-23, CB-24
- **Terminado cuando:** todas las reglas del §4 del contexto tienen prueba unitaria y pasan.
- **Commit:** `feat(T3): implementar reglas de negocio para registrar solicitudes`

### T4 · Endpoint `POST /solicitudes`
- **Rama:** `feature/registro-solicitudes` (misma rama que T3)
- **Archivos:** `app/api/solicitudes.py`, `app/main.py`, `tests/test_api_post.py`
- **Qué hace:** lee el cuerpo crudo como JSON (sin depender de `Content-Type`), invoca el servicio, responde 201; traduce errores de dominio a 400/409/422 con el formato uniforme.
- **Cubre:** RF-01, RF-07, RF-09, CB-05, CB-17, CB-25
- **Terminado cuando:** el ejemplo del §4 del contexto responde 201 y los errores llegan con el formato del §6.3.
- **Commit:** `feat(T4): exponer POST /solicitudes con errores uniformes`

### T5 · Endpoint `GET /solicitudes`
- **Rama:** `feature/consulta-solicitudes`
- **Archivos:** `app/api/solicitudes.py`, `tests/test_api_get.py`
- **Qué hace:** lista con filtros `estado` y `prioridad` normalizados y combinables; parámetro vacío = sin filtro; valor desconocido = 422 con valores admitidos.
- **Cubre:** RF-02 a RF-05, CB-18 a CB-20
- **Terminado cuando:** las combinaciones de filtros devuelven exactamente las solicitudes esperadas.
- **Commit:** `feat(T5): exponer GET /solicitudes con filtros por estado y prioridad`

### T6 · Manejo global de errores
- **Rama:** `feature/manejo-errores`
- **Archivos:** `app/main.py`, `app/core/errors.py`, `tests/test_errores.py`
- **Qué hace:** formato uniforme para 404, 405 y 500 (sin traza); ninguna entrada del cliente produce 500.
- **Cubre:** RF-07, RNF-04, CB-26
- **Terminado cuando:** rutas y métodos inexistentes y un error interno simulado responden con el formato uniforme.
- **Commit:** `feat(T6): unificar respuestas de error 404, 405 y 500`

### T7 · Verificación y casos de prueba
- **Rama:** `feature/manejo-errores` (misma rama que T6)
- **Archivos:** `docs/03-casos-de-prueba.md`
- **Qué hace:** ejecuto la suite completa y documento los casos con resultado **esperado y observado**, más la matriz de trazabilidad requisito → prueba; incluyo al menos tres casos manuales con `curl` (uno de error).
- **Cubre:** RF, RNF y CB del contexto
- **Terminado cuando:** cada requisito y caso borde tiene al menos una prueba y su resultado observado.
- **Commit:** `test(T7): documentar casos de prueba con resultado esperado y observado`

### T8 · README
- **Rama:** `release/1.0.0`
- **Archivos:** `README.md`
- **Qué hace:** propósito, requisitos, instalación, ejecución, pruebas, ejemplos de uso, supuestos, decisión descartada, limitaciones, dependencias y mapa de la documentación.
- **Terminado cuando:** alguien sin contexto puede clonar, ejecutar y probar siguiendo solo el README.
- **Commit:** `docs(T8): escribir README con ejecución, pruebas y supuestos`

### T9 · Diseño de evolución
- **Rama:** `feature/diseno-evolucion`
- **Archivos:** `docs/04-diseno-evolucion.md`
- **Qué hace:** en una página, cómo notificar automáticamente las solicitudes de prioridad Alta (correo o Teams) sin avisos duplicados y cómo validar la tienda contra una API externa de catálogo; diagrama; manejo de credenciales, indisponibilidad, reintentos y fallos; elección de herramienta (Power Automate, código o combinación).
- **Terminado cuando:** cabe en una página e incluye diagrama y las cuatro preocupaciones operativas.
- **Commit:** `docs(T9): diseñar notificaciones y validación de tienda`

### T10 · Bitácoras y cierre
- **Rama:** `release/1.0.0`
- **Archivos:** `docs/05-bitacora-ia.md`, `docs/06-bitacora-trabajo.md`
- **Qué hace:** bitácora de uso de IA con reflexión final; cronología y tiempo real invertido. La versión queda registrada con el tag `v1.0.0`.
- **Terminado cuando:** las bitácoras coinciden con el historial de commits.
- **Commit:** `docs(T10): completar bitácoras de IA y de trabajo`

> `06-bitacora-trabajo.md` se crea en T0 y se actualiza al cerrar cada tarea; en T10 solo se completa el tiempo total.

---

## 3. Flujo de ramas (Git Flow)

| Orden | Rama | Tareas | Se fusiona en |
|---|---|---|---|
| 1 | `feature/planeacion` | Fases 1 a 3 | `develop` |
| 2 | `feature/esqueleto` | T0 | `develop` |
| 3 | `feature/modelo-persistencia` | T1, T2 | `develop` |
| 4 | `feature/registro-solicitudes` | T3, T4 | `develop` |
| 5 | `feature/consulta-solicitudes` | T5 | `develop` |
| 6 | `feature/manejo-errores` | T6, T7 | `develop` |
| 7 | `feature/diseno-evolucion` | T9 | `develop` |
| 8 | `release/1.0.0` | T8, T10 | `main` (con tag `v1.0.0`) y de vuelta a `develop` |

**Reglas que sigo**
- Cada rama nace de `develop` actualizado.
- Las fusiones usan `--no-ff` para que cada rama quede visible en el historial (`git log --graph`).
- Mensajes con **Conventional Commits** y referencia a la tarea: `tipo(Tn): descripción`.
- `hotfix/*` solo si aparece un defecto real después de publicar `v1.0.0`.
