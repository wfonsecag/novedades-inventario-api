# 01 · Contexto — API de novedades de inventario



Este documento responde **qué** se construye y **por qué**. El **cómo** está en los ADR (`docs/adr/`) y el **orden de construcción** en `02-spec.md`.

---

## 1. Objetivo y alcance

**Problema.** Las tiendas reportan novedades de inventario por distintos canales. El equipo responsable necesita centralizar esos reportes, identificar prioridades y darles seguimiento.

**Objetivo del prototipo.** Una API REST pequeña, funcional y entendible que registre solicitudes y permita consultarlas filtrando por estado y prioridad.

| En alcance | Fuera de alcance (y por qué) |
|---|---|
| `POST /solicitudes` | Interfaz gráfica — el valor está en la API; cualquier canal puede consumirla |
| `GET /solicitudes` con filtros `estado` y `prioridad` | Cambio de estado (PUT/PATCH) y borrado — los dejo para v2 para enfocarme en registro y consulta |
| Validación y normalización de datos | Autenticación/autorización — prototipo local con datos ficticios |
| Fecha de creación asignada por el servidor | Paginación — volumen de prototipo; se plantea como v2 |
| Rechazo de duplicados por `id` | Notificaciones y validación de tienda contra catálogo externo — las diseño como evolución en `04-diseno-evolucion.md`, sin implementarlas |
| Persistencia en SQLite | Despliegue en la nube |

## 2. Glosario

| Término | Definición |
|---|---|
| **Solicitud** | Registro de una novedad de inventario reportada por una tienda. |
| **Novedad** | Hecho que afecta el inventario de una tienda (faltante, avería, error de traslado, etc.). |
| **Canal** | Sistema o persona que envía la solicitud a la API. |
| **Tipo** | Categoría de la novedad: *qué pasó*. |
| **Prioridad** | Urgencia declarada por el canal: *qué tan pronto debe atenderse*. |
| **Estado** | Etapa del seguimiento de la solicitud. |
| **Normalizar** | Convertir variantes de escritura de un mismo valor a su forma canónica (`"ALTA"` → `"Alta"`). |

## 3. Principio de diseño de la validación

> **Tolerante con la forma, estricta con el significado.**

- **Se acepta y normaliza** lo que tiene una sola interpretación posible: mayúsculas/minúsculas, tildes, espacios sobrantes, guiones o guiones bajos, números enviados como texto, nombres de campo con mayúscula o tilde.
- **Se asigna un valor por defecto trazable** cuando un dato clasificatorio (`tipo`, `prioridad`) falta o no se reconoce, para no detener el registro de una novedad real. El valor original se conserva.
- **Se rechaza con un mensaje claro** solo lo que no puede interpretarse sin adivinar o sin lo cual no existe un reporte atendible (`id`, `tienda`, `descripcion`).
- **Escritura tolerante, lectura explícita:** en el `POST` se aplican valores por defecto; en los filtros del `GET` un valor desconocido se rechaza, porque una consulta mal escrita no debe devolver resultados engañosos.

## 4. Datos de entrada — `POST /solicitudes`

Cuerpo JSON (se intenta leer como JSON aunque falte el encabezado `Content-Type`). Los **nombres de campo** se normalizan antes de validar: minúsculas, sin tildes, espacios y guiones convertidos en `_` (`"ID"`, `"Tienda"`, `"Descripción"` son válidos). Si dos campos normalizan al mismo nombre (`"descripcion"` y `"Descripción"`), la solicitud es ambigua y se rechaza con 422.

**Espacios sobrantes:** en `tienda` se quitan al inicio y al final y se reducen los repetidos internos; en `descripcion` solo se quitan al inicio y al final (se respeta el texto del reporte). **`null` o texto vacío** equivalen a "no enviado".

| Campo | Obligatorio | Tipo aceptado | Regla | Si falla |
|---|---|---|---|---|
| `id` | Sí | Entero o texto numérico (`101`, `"101"`, `" 101 "`) | Entero > 0 y ≤ 9 223 372 036 854 775 807. Se rechazan booleanos, decimales (`101.5`, `"101.0"`) y texto no numérico | 422 |
| `tienda` | Sí | Texto o número (un código `1234` se convierte a `"1234"`). Se rechazan booleanos, listas y objetos | 1 a 200 caracteres tras quitar espacios sobrantes; conserva mayúsculas y tildes | 422 |
| `tipo` | No | Texto (otro tipo de dato se convierte a texto) | Se normaliza contra el catálogo (§5.1). Si falta o no se reconoce → `"Otro"` y el texto original va a `tipo_reportado` | — (no falla) |
| `descripcion` | Sí | Texto o número (se convierte a texto). Se rechazan booleanos, listas y objetos | 1 a 2000 caracteres tras quitar espacios sobrantes. **No se trunca** | 422 |
| `prioridad` | No | Texto (otro tipo de dato se convierte a texto) | Se normaliza contra el catálogo (§5.2). Si falta o no se reconoce → `"Media"` y el texto original va a `prioridad_reportada` | — (no falla) |
| `estado` | No | Texto | Si falta → `"Pendiente"`. Si se envía, debe normalizar a `"Pendiente"`; cualquier otro valor (reconocido o no) se rechaza | 422 |
| `fecha_creacion` | — | — | **Se ignora**: la asigna el servidor | — |
| Cualquier otro campo | — | — | **Se ignora**: no se guarda ni produce error | — |

**Ejemplo válido** (con la escritura de un canal real):

```json
{ "ID": "101", "Tienda": "Santafé", "Tipo": "diferencia de inventario",
  "Descripción": "Faltan 5 unidades", "Prioridad": "ALTA", "Estado": "Pendiente" }
```

## 5. Catálogos (valores admitidos)

La comparación ignora mayúsculas, tildes, espacios repetidos, `_` y `-`. Los catálogos están definidos en un único lugar del código.

### 5.1 Tipo

| Valor canónico | Significado | Ejemplo de descripción |
|---|---|---|
| Diferencia de inventario | El conteo físico no coincide con el sistema | "Faltan 5 unidades" |
| Mercancía averiada | Producto dañado | "Bolso con costura rota" |
| Error en traslado | Lo recibido no coincide con lo despachado | "Llegaron 10 de 12 cinturones" |
| Error de referencia | Código, etiqueta o talla incorrectos | "Zapato talla 38 etiquetado 39" |
| Otro | No encaja en los anteriores o el tipo no se reconoció | "Exhibidor sin precio" |

### 5.2 Prioridad

`Alta` · `Media` · `Baja` — la declara el canal.

### 5.3 Estado

`Pendiente` · `En proceso` · `Resuelta` — al crear solo se admite `Pendiente`; los demás existen para el seguimiento (v2) y para el filtro.

## 6. Datos de salida

### 6.1 Solicitud (respuesta de `POST` y elementos de `GET`)

```json
{
  "id": 101,
  "tienda": "Santafé",
  "tipo": "Diferencia de inventario",
  "tipo_reportado": null,
  "descripcion": "Faltan 5 unidades",
  "prioridad": "Alta",
  "prioridad_reportada": null,
  "estado": "Pendiente",
  "fecha_creacion": "2026-11-26T15:10:00Z"
}
```

- `tipo_reportado` / `prioridad_reportada`: `null` si el valor se reconoció o no se envió; el texto original si se aplicó el valor por defecto.
- `fecha_creacion`: UTC, ISO 8601.

### 6.2 `GET /solicitudes`

- Parámetros opcionales: `estado`, `prioridad`. Se combinan con **Y**. Se normalizan igual que en el `POST`.
- Parámetro vacío (`?estado=`) = sin filtro. Parámetros no definidos (`?tipo=...`) se ignoran.
- Respuesta `200` con una lista (vacía si no hay coincidencias), ordenada por `fecha_creacion` y luego `id`, ascendente.

### 6.3 Formato de error (uniforme)

```json
{
  "error": "VALIDACION",
  "mensaje": "La solicitud tiene datos inválidos.",
  "detalles": [ { "campo": "descripcion", "problema": "Es obligatorio y no puede estar vacío." } ]
}
```

| HTTP | `error` | Cuándo |
|---|---|---|
| 201 | — | Solicitud creada |
| 200 | — | Consulta exitosa |
| 400 | `JSON_INVALIDO` | Cuerpo vacío, JSON mal formado o que no es un objeto |
| 404 | `NO_ENCONTRADO` | Ruta inexistente |
| 405 | `METODO_NO_PERMITIDO` | Método no soportado en la ruta (p. ej. `DELETE /solicitudes`) |
| 409 | `DUPLICADO` | Ya existe una solicitud con ese `id` |
| 422 | `VALIDACION` | Campo obligatorio ausente o inválido; filtro con valor desconocido (incluye la lista de valores admitidos) |
| 500 | `ERROR_INTERNO` | Error no previsto. Mensaje genérico, **sin traza ni detalles internos** |

## 7. Requisitos funcionales

| ID | Requisito | Criterio de aceptación |
|---|---|---|
| RF-01 | Registrar solicitudes con `POST /solicitudes` | Con datos válidos responde 201 y devuelve la solicitud completa |
| RF-02 | Consultar solicitudes con `GET /solicitudes` | Responde 200 con todas las solicitudes ordenadas |
| RF-03 | Filtrar por `estado` | Solo devuelve solicitudes en ese estado |
| RF-04 | Filtrar por `prioridad` | Solo devuelve solicitudes con esa prioridad |
| RF-05 | Combinar filtros | `estado` y `prioridad` aplican a la vez |
| RF-06 | Validar campos obligatorios y valores admitidos | Datos inválidos → 422 con detalle por campo |
| RF-07 | Devolver errores comprensibles | Todo error usa el formato de §6.3 |
| RF-08 | Asignar fecha de creación | El servidor la asigna; la del cliente se ignora |
| RF-09 | Evitar duplicados por `id` | Segundo registro con el mismo `id` → 409; el original no cambia |
| RF-10 | Persistir la información | Las solicitudes sobreviven a un reinicio del servidor |
| RF-11 | Normalizar entradas | Variantes de escritura se guardan en forma canónica |
| RF-12 | Valores por defecto trazables | `tipo` → "Otro" y `prioridad` → "Media" cuando faltan o no se reconocen, conservando el original |

## 8. Requisitos no funcionales

| ID | Requisito |
|---|---|
| RNF-01 | **Ejecutable con pocos pasos:** Python 3.10+, `pip install -r requirements.txt` y un comando para iniciar. Sin servicios externos. |
| RNF-02 | **Mantenible:** separación en capas (API → servicio → repositorio); catálogos y valores por defecto en un único lugar. |
| RNF-03 | **Probado:** pruebas automatizadas con `pytest` que cubren casos válidos, de error y de borde; base de datos aislada por prueba. |
| RNF-04 | **Robusto:** ninguna entrada del cliente produce un 500; los errores internos no exponen trazas. |
| RNF-05 | **Consistente ante concurrencia:** dos registros simultáneos con el mismo `id` no generan duplicado (garantizado por la llave primaria). |
| RNF-06 | **Documentado:** OpenAPI/Swagger disponible en `/docs`; README con ejecución, pruebas y supuestos. |
| RNF-07 | **Seguro con los datos:** solo datos ficticios; sin secretos en el repositorio; la base de datos local no se versiona. |
| RNF-08 | **Rendimiento de prototipo:** respuesta local menor a 200 ms con cientos de registros. |

## 9. Reglas de negocio

| ID | Regla |
|---|---|
| RN-01 | Una solicitud se identifica por su `id`, que asigna el canal y es único. |
| RN-02 | Toda solicitud nueva nace en estado `Pendiente`. |
| RN-03 | La fecha de creación es la del servidor en el momento del registro. |
| RN-04 | La prioridad la declara el canal; el sistema solo la normaliza. |
| RN-05 | Si `tipo` falta o no se reconoce → `"Otro"`; si `prioridad` falta o no se reconoce → `"Media"`. El texto original se guarda en `*_reportado`. Los valores por defecto son configurables. |
| RN-06 | Un `tipo` "Otro" **no** modifica la prioridad enviada por el canal. |
| RN-07 | Un registro rechazado no deja rastro en la base de datos. |

## 10. Casos borde

| # | Caso | Entrada | Resultado esperado |
|---|---|---|---|
| CB-01 | `id` como texto numérico | `"id": " 101 "` | 201, `id = 101` |
| CB-02 | `id` no numérico | `"id": "abc"` | 422 |
| CB-03 | `id` cero, negativo o decimal | `0`, `-5`, `101.5` | 422 |
| CB-04 | `id` booleano | `true` | 422 |
| CB-05 | `id` duplicado | Mismo `id` dos veces | 1.º 201, 2.º 409; el original no cambia |
| CB-06 | Campo obligatorio ausente o `null` | Sin `descripcion` | 422 indicando el campo |
| CB-07 | Texto solo con espacios | `"tienda": "   "` | 422 |
| CB-08 | Tienda con nombre largo y tilde | 150 caracteres, "Santafé" | 201, se conserva tal cual |
| CB-09 | Tienda como número | `"tienda": 1234` | 201, `tienda = "1234"` |
| CB-10 | Descripción > 2000 caracteres | 2001 caracteres | 422 (no se trunca) |
| CB-11 | Variantes de escritura | `"ALTA"`, `"error_en_traslado"`, `"mercancia averiada"` | 201 con valores canónicos |
| CB-12 | Tipo desconocido | `"tipo": "Robo"` | 201, `tipo = "Otro"`, `tipo_reportado = "Robo"` |
| CB-13 | Prioridad desconocida o ausente | `"prioridad": "Altísima"` / sin campo | 201, `prioridad = "Media"`, `prioridad_reportada = "Altísima"` / `null` |
| CB-14 | Estado distinto de Pendiente al crear | `"estado": "Resuelta"` | 422 |
| CB-15 | Nombres de campo con mayúscula/tilde | `"Descripción"`, `"ID"` | 201 |
| CB-16 | Campos extra o `fecha_creacion` del cliente | `"canal": "WhatsApp"`, `"fecha_creacion": "2020-01-01"` | 201; se ignoran |
| CB-17 | Cuerpo vacío, JSON mal formado o una lista | `""`, `{id:1`, `[]` | 400 |
| CB-18 | Filtro con valor desconocido | `?prioridad=urgente` | 422 con valores admitidos |
| CB-19 | Filtro vacío o con otra escritura | `?estado=`, `?prioridad=alta` | 200; sin filtro / filtro normalizado |
| CB-20 | Sin coincidencias | `?estado=Resuelta` sin datos | 200 con `[]` |
| CB-21 | Reinicio del servidor | Registrar, reiniciar, consultar | La solicitud sigue existiendo |
| CB-22 | Campo repetido con distinta escritura | `"descripcion"` y `"Descripción"` en el mismo cuerpo | 422 (ambiguo) |
| CB-23 | Tipo o prioridad con dato no textual | `"prioridad": 1` | 201, `prioridad = "Media"`, `prioridad_reportada = "1"` |
| CB-24 | `tienda` o `descripcion` booleana, lista u objeto | `"tienda": true` | 422 |
| CB-25 | Sin encabezado `Content-Type` | Cuerpo JSON válido | 201 |
| CB-26 | Ruta o método no soportado | `DELETE /solicitudes` | 405 con formato uniforme |

## 11. Supuestos

| ID | Supuesto | Alternativa si el negocio lo define distinto |
|---|---|---|
| S-01 | El `id` lo asigna el canal, por eso los duplicados se controlan por identificador | Generarlo en el servidor y usar otra llave de idempotencia |
| S-02 | Catálogo de tipos de §5.1, definido a partir de las novedades más comunes en tienda | Se cambia en un solo lugar del código |
| S-03 | Prioridades `Alta/Media/Baja` y estados `Pendiente/En proceso/Resuelta` | Ídem |
| S-04 | Valores por defecto `Otro` y `Media` | Rechazar con 422 en lugar de asignar valor por defecto |
| S-05 | Fechas en UTC | Mostrar en hora de Colombia en la capa de presentación |
| S-06 | No hay catálogo de tiendas en esta versión | Validación contra API externa (ver `04-diseno-evolucion.md`) |
| S-07 | Un solo proceso del servidor | Ver limitaciones |

## 12. Trade-offs y limitaciones conocidas

| Decisión | Se gana | Se pierde / riesgo | Mitigación |
|---|---|---|---|
| Valores por defecto en `tipo` y `prioridad` | Ningún reporte real se pierde | Un caso urgente mal escrito queda en "Media"; "Otro" puede crecer | `*_reportado` permite encontrarlos; v2: alertas o sinónimos |
| Ignorar campos no definidos | Los canales pueden evolucionar sin romper la integración | Un error de escritura en un campo opcional pasa sin aviso | Los opcionales tienen valores por defecto seguros |
| SQLite | Persistencia sin instalar nada; unicidad garantizada por la base | No escala a múltiples instancias ni a escritura intensiva | Repositorio detrás de una interfaz → motor más robusto en v2 (ver ADR-0001) |
| Sin paginación | Simplicidad | Respuestas grandes con mucho volumen | v2: `limit`/`offset` |

## 13. Trazabilidad

Se completa en `03-casos-de-prueba.md`: cada requisito (RF, RNF, RN) y caso borde (CB) queda vinculado a la prueba automatizada que lo verifica, con resultado esperado y observado.
