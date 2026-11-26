# 03 · Casos de prueba

Verifico la solución en dos niveles: **pruebas automatizadas** (`pytest`) que cubren cada requisito y caso borde de `01-contexto.md`, y **pruebas manuales** contra el servidor en ejecución, con resultado esperado y observado.

## 1. Pruebas automatizadas

```powershell
pytest -v
```

| Archivo | Nivel | Qué verifica | Pruebas |
|---|---|---|---|
| `test_health.py` | API | El servicio responde | 1 |
| `test_normalization.py` | Unidad | Catálogos y normalización de campos y valores | 19 |
| `test_repository.py` | Integración (SQLite) | Inserción, duplicados, filtros, orden y persistencia | 5 |
| `test_service.py` | Unidad + SQLite | Reglas de negocio del registro | 49 |
| `test_api_post.py` | API | `POST /solicitudes` de punta a punta | 12 |
| `test_api_get.py` | API | `GET /solicitudes` y filtros | 11 |
| `test_errores.py` | API | Formato uniforme de 404, 405 y 500 | 3 |
| **Total** | | | **100** |

**Resultado observado:** ✅ `100 passed, 1 warning in 3.91s` (Windows, PowerShell, entorno virtual con `requirements.txt`).

La advertencia es un aviso de deprecación de la librería de pruebas (Starlette sugiere `httpx2` en lugar de `httpx` para `TestClient`); no afecta los resultados.

Cada prueba usa una base SQLite temporal propia, por lo que el orden de ejecución no afecta los resultados.

## 2. Pruebas manuales

**Preparación.** Inicio el servidor con una base exclusiva para estas pruebas:

```powershell
$env:DATABASE_PATH = "manual.db"
uvicorn app.main:app
```

En otra terminal defino una función auxiliar que muestra el código HTTP y el cuerpo de la respuesta, incluso cuando es un error (en PowerShell 5.1 el cuerpo de un error se lee de `ErrorDetails`):

```powershell
function Probar($Metodo, $Ruta, $Cuerpo) {
  $p = @{ Method = $Metodo; Uri = "http://127.0.0.1:8000$Ruta"; UseBasicParsing = $true }
  if ($Cuerpo) { $p.ContentType = "application/json; charset=utf-8"; $p.Body = [Text.Encoding]::UTF8.GetBytes($Cuerpo) }
  try { $r = Invoke-WebRequest @p; "$($r.StatusCode) $($r.Content)" }
  catch {
    if ($_.Exception.Response) { "$([int]$_.Exception.Response.StatusCode) $($_.ErrorDetails.Message)" }
    else { "SIN RESPUESTA: el servidor no está corriendo" }
  }
}
```

| # | Caso | Comando | Esperado | Observado |
|---|---|---|---|---|
| M1 | Registro con la escritura de un canal real (mayúsculas, tildes, `id` como texto) | `Probar POST /solicitudes '{"ID": "101", "Tienda": "Santafé", "Tipo": "diferencia de inventario", "Descripción": "Faltan 5 unidades", "Prioridad": "ALTA"}'` | `201` con valores canónicos: `"tipo": "Diferencia de inventario"`, `"prioridad": "Alta"`, `"estado": "Pendiente"` y `fecha_creacion` asignada | ✅ `201` — `{"id":101,"tienda":"Santafé","tipo":"Diferencia de inventario","tipo_reportado":null,"descripcion":"Faltan 5 unidades","prioridad":"Alta","prioridad_reportada":null,"estado":"Pendiente","fecha_creacion":"2026-11-26T15:52:38Z"}` |
| M2 | Consulta con filtro en otra escritura | `Probar GET "/solicitudes?prioridad=alta"` | `200` con una lista que contiene la solicitud `101` | ✅ `200` — lista con la solicitud `101` (mismos valores de M1) |
| M3 | **Error:** identificador duplicado | Repetir el comando de M1 | `409` con `"error": "DUPLICADO"`; la solicitud original no cambia | ✅ `409` — `{"error":"DUPLICADO","mensaje":"Ya existe una solicitud con id 101.","detalles":[{"campo":"id","problema":"El identificador ya fue registrado."}]}` |
| M4 | **Error:** JSON mal formado | `Probar POST /solicitudes '{id:1'` | `400` con `"error": "JSON_INVALIDO"` | ✅ `400` — `{"error":"JSON_INVALIDO","mensaje":"El cuerpo de la solicitud no es un JSON válido.","detalles":[]}` |
| M5 | **Error:** campos obligatorios faltantes | `Probar POST /solicitudes '{"id": 102}'` | `422` con `"error": "VALIDACION"` y detalle para `tienda` y `descripcion` | ✅ `422` — `{"error":"VALIDACION","mensaje":"La solicitud tiene datos inválidos.","detalles":[{"campo":"tienda",...},{"campo":"descripcion",...}]}` |
| M6 | Persistencia tras reinicio | Detener el servidor (Ctrl+C), iniciarlo de nuevo y repetir M2 | `200`; la solicitud `101` sigue existiendo | ✅ `200` — la solicitud `101` sigue existiendo con la misma `fecha_creacion` (`15:52:38Z`) tras reiniciar el servidor |

**Nota sobre la consola.** PowerShell 5.1 muestra "SantafÃ©" porque interpreta la respuesta JSON como Latin-1. El dato se guarda y se entrega en UTF-8: en el navegador y en `/docs` se ve "Santafé". Es una limitación de la consola, no de la API.

## 3. Matriz de trazabilidad

### Requisitos funcionales

| Requisito | Prueba(s) que lo verifican |
|---|---|
| RF-01 Registrar | `test_post_registra_solicitud_y_responde_201`, M1 |
| RF-02 Consultar | `test_get_devuelve_todas_ordenadas_por_fecha`, `test_get_sin_datos_devuelve_lista_vacia` |
| RF-03 Filtro por estado | `test_get_filtra_por_estado` |
| RF-04 Filtro por prioridad | `test_get_filtra_por_prioridad`, M2 |
| RF-05 Filtros combinados | `test_get_combina_filtros` |
| RF-06 Validar obligatorios y valores admitidos | `test_campos_obligatorios_ausentes_reportan_todos_los_errores`, `test_post_datos_invalidos_responde_422_con_detalle_por_campo`, M5 |
| RF-07 Errores comprensibles | `assert_formato_error` en `test_api_post.py` y `test_errores.py`, M3–M5 |
| RF-08 Fecha de creación | `test_registra_ejemplo_con_variantes_de_escritura`, `test_campos_extra_y_fecha_del_cliente_se_ignoran` |
| RF-09 Evitar duplicados | `test_insertar_duplicado_lanza_error_y_conserva_original`, `test_post_duplicado_responde_409`, M3 |
| RF-10 Persistir | `test_los_datos_persisten_al_reabrir`, M6 |
| RF-11 Normalizar entradas | `test_resolver_tipo_normaliza_variantes`, `test_normalizar_claves_acepta_variantes_de_escritura`, M1 |
| RF-12 Valores por defecto trazables | `test_tipo_desconocido_queda_como_otro_con_original`, `test_prioridad_desconocida_queda_media_con_original` |

### Requisitos no funcionales

| Requisito | Verificación |
|---|---|
| RNF-01 Ejecutable con pocos pasos | Instalación y arranque descritos en el README; probados en mi equipo |
| RNF-02 Mantenible por capas | Revisión de dependencias `api → services → repositories` (ADR-0003) |
| RNF-03 Probado y aislado | 100 pruebas con base temporal por prueba |
| RNF-04 Robusto, sin trazas expuestas | `test_error_interno_responde_500_sin_exponer_detalles`, casos CB-17 y CB-24 |
| RNF-05 Consistente ante concurrencia | Unicidad por llave primaria: `test_insertar_duplicado_lanza_error_y_conserva_original` |
| RNF-06 Documentado | `/docs` (Swagger) y README |
| RNF-07 Seguro con los datos | `.gitignore` excluye `*.db` y `.env`; solo datos ficticios |
| RNF-08 Rendimiento de prototipo | Verificación manual: las respuestas de M1–M6 son inmediatas en local |

### Casos borde

| Caso | Prueba |
|---|---|
| CB-01 | `test_id_acepta_entero_o_texto_numerico` |
| CB-02, CB-03, CB-04 | `test_id_invalido_se_rechaza` (10 variantes) |
| CB-05 | `test_insertar_duplicado_lanza_error_y_conserva_original`, `test_post_duplicado_responde_409` |
| CB-06, CB-07 | `test_campos_obligatorios_ausentes_reportan_todos_los_errores`, `test_texto_obligatorio_vacio_o_nulo_se_rechaza` |
| CB-08 | `test_tienda_larga_con_tilde_se_conserva_y_reduce_espacios`, `test_tienda_mayor_a_200_caracteres_se_rechaza` |
| CB-09 | `test_tienda_numerica_se_convierte_a_texto` |
| CB-10 | `test_descripcion_respeta_texto_interno_y_limite` |
| CB-11 | `test_resolver_tipo_normaliza_variantes`, `test_resolver_prioridad_y_estado` |
| CB-12 | `test_tipo_desconocido_queda_como_otro_con_original` |
| CB-13 | `test_prioridad_desconocida_queda_media_con_original`, `test_prioridad_ausente_queda_media_sin_original` |
| CB-14 | `test_estado_distinto_de_pendiente_se_rechaza` |
| CB-15 | `test_normalizar_claves_acepta_variantes_de_escritura` |
| CB-16 | `test_campos_extra_y_fecha_del_cliente_se_ignoran` |
| CB-17 | `test_post_cuerpo_invalido_responde_400` (7 variantes) |
| CB-18 | `test_get_filtro_desconocido_responde_422_con_valores_admitidos` |
| CB-19 | `test_get_normaliza_filtros`, `test_get_filtro_vacio_equivale_a_sin_filtro` |
| CB-20 | `test_get_sin_coincidencias_devuelve_lista_vacia` |
| CB-21 | `test_los_datos_persisten_al_reabrir`, M6 |
| CB-22 | `test_normalizar_claves_rechaza_campos_ambiguos` |
| CB-23 | `test_prioridad_no_textual_se_convierte_a_texto` |
| CB-24 | `test_texto_con_tipo_de_dato_invalido_se_rechaza` |
| CB-25 | `test_post_sin_content_type_json_se_acepta` |
| CB-26 | `test_ruta_inexistente_responde_404_con_formato_uniforme`, `test_metodo_no_soportado_responde_405_con_formato_uniforme` |
