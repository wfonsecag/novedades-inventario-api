# 06 · Bitácora de trabajo

Registro cronológico del flujo de trabajo. Cada entrada corresponde a un commit del historial.

| # | Fase / tarea | Rama | Qué hice |
|---|---|---|---|
| 1 | Preparación | `main`, `develop` | Creé el repositorio, el `.gitignore` y la rama `develop`. |
| 2 | Fase 1 · Especificar | `feature/planeacion` | Definí alcance, requisitos, reglas de negocio, casos borde y supuestos (`01-contexto.md`). Hice una segunda revisión que agregó 5 casos borde. |
| 3 | Fase 2 · Decidir | `feature/planeacion` | Registré las decisiones de persistencia, framework y arquitectura (ADR-0001 a 0003). |
| 4 | Fase 3 · Desglosar | `feature/planeacion` | Ordené la construcción en tareas T0 a T10 con su rama y criterio de terminado (`02-spec.md`). |
| 5 | T0 · Esqueleto | `feature/esqueleto` | Creé la app con `/health`, la configuración de la base por variable de entorno y el fixture de pruebas con base temporal. Prueba escrita antes del código. Ajusté `pytest.ini` para que `pytest` encuentre el paquete `app` en cualquier entorno. |
| 6 | T1 · Normalización y catálogos | `feature/modelo-persistencia` | Definí los catálogos de tipo, prioridad y estado, la normalización de nombres de campo y valores (con detección de campos ambiguos) y las excepciones de dominio. |
| 7 | T2 · Repositorio SQLite | `feature/modelo-persistencia` | Implementé la persistencia detrás de una interfaz `Repositorio`: tabla creada al iniciar, duplicados detectados por la llave primaria, consulta con filtros combinables y orden por fecha. Probé que los datos persisten al reabrir el archivo. |
| 8 | T3 · Servicio de solicitudes | `feature/registro-solicitudes` | Implementé las reglas de negocio del registro: validación y conversión de `id`, `tienda` y `descripcion`; valores por defecto trazables para `tipo` y `prioridad`; estado inicial `Pendiente`; fecha del servidor en UTC; campos no definidos ignorados. Los errores de validación se acumulan para informar todos los campos a la vez. |
| 9 | T4 · Endpoint POST | `feature/registro-solicitudes` | Expuse `POST /solicitudes`: leo el cuerpo como JSON aunque falte el `Content-Type`, respondo 201 y traduzco los errores de dominio a 400/409/422 con formato uniforme. Corregí un efecto secundario: la base se abría al importar el módulo; ahora se abre al iniciar la aplicación (lifespan). |
| 10 | Refactor · Estructura por capas | `refactor/estructura-por-capas` | Agrupé los módulos de `app/` en paquetes por capa (`api`, `services`, `repositories`, `schemas`, `core`) para mejorar la lectura de la estructura. Sin cambios de comportamiento: las 86 pruebas siguen pasando. Actualicé ADR-0003 y la spec. |
| 11 | T5 · Endpoint GET | `feature/consulta-solicitudes` | Expuse `GET /solicitudes` con filtros `estado` y `prioridad` normalizados y combinables: parámetro vacío = sin filtro; valor desconocido = 422 con los valores admitidos; parámetros no definidos se ignoran. Agregué una prueba de punta a punta (registrar y luego consultar). |
| 12 | T6 · Manejo global de errores | `feature/manejo-errores` | Unifiqué el formato de 404, 405 y 500. El 500 registra el detalle en el log del servidor y responde un mensaje genérico, sin traza. Ajusté una prueba que asumía que el encabezado `Allow` lista todos los métodos de la ruta; el framework solo incluye el primero que coincide. |
| 13 | T7 · Verificación | `feature/manejo-errores` | Ejecuté la suite completa (100 pruebas) y 6 pruebas manuales contra el servidor (registro, consulta, duplicado, JSON inválido, campos faltantes y persistencia tras reinicio). Documenté resultado esperado y observado y la matriz de trazabilidad. Corregí la función auxiliar de PowerShell, que no mostraba el cuerpo de los errores en la versión 5.1. |
| 14 | T9 · Diseño de evolución | `feature/diseno-evolucion` | Diseñé las notificaciones de prioridad Alta (outbox transaccional, restricción única, reintentos con espera exponencial) y la validación de tienda contra el catálogo externo (timeout, reintento, caché, circuit breaker, registro pendiente ante indisponibilidad). Elegí código sobre Power Automate y documenté en qué caso usaría este último. |

**Tiempo real invertido:** _(se completa al cierre)_
