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

**Tiempo real invertido:** _(se completa al cierre)_
