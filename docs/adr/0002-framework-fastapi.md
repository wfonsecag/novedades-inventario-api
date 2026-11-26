# ADR-0002 · Framework web: FastAPI

- **Estado:** Aceptado
- **Fecha:** 2026-11-26
- **Relacionado con:** RF-06, RF-07, RNF-03, RNF-06 (`01-contexto.md`)

## Contexto

Podía construir la API en Python (FastAPI o Flask) o en Node.js. La solución exige muchas reglas de validación y normalización (§4 y §10 del contexto), errores comprensibles y que sea fácil de probar. Elegí Python como lenguaje.

## Decisión

Uso **FastAPI** con **Pydantic v2** para los modelos y **Uvicorn** como servidor.

- Los modelos de salida y los catálogos se declaran con Pydantic y `Enum`.
- La lectura del cuerpo y la normalización (nombres de campo, `Content-Type` ausente, campos ambiguos) se hacen **antes** de Pydantic, porque son reglas propias del negocio (ver ADR-0003).
- Se reemplazan los manejadores de error por defecto (que devuelven 422 con un formato técnico) por manejadores propios con el formato uniforme del contexto (§6.3).
- Las pruebas usan `TestClient` de FastAPI con `pytest`.

## Alternativas consideradas

| Alternativa | Por qué la descarté |
|---|---|
| Flask | Validación manual o con extensiones adicionales; sin documentación OpenAPI integrada. Más código para el mismo resultado. |
| Node.js (Express) | Válido, pero prioricé Python por dominio y dependencias ya instaladas y por la validación declarativa de Pydantic. |

## Consecuencias

**Positivas**
- Documentación interactiva gratis en `/docs` (Swagger), útil para probar la API sin herramientas adicionales.
- Validación declarativa y tipada; `TestClient` permite probar sin levantar el servidor.

**Negativas**
- El formato de error por defecto de FastAPI no es comprensible para un canal de negocio: obliga a escribir manejadores propios (incluidos 404 y 405).
- Dependencias externas (FastAPI, Uvicorn, Pydantic, pytest, httpx): se declaran con versión en `requirements.txt`.
