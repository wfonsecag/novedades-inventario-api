# 05 · Bitácora de uso de IA

**Herramienta:** Claude (Anthropic), asistente de IA conversacional.

La planeación (alcance, supuestos, reglas de negocio, decisiones técnicas y orden de tareas) la definí yo. Usé IA para estructurar esa planeación en documentos, contrastar alternativas y generar el código y las pruebas a partir de mi especificación. Revisé cada cambio y lo validé ejecutando las pruebas en mi equipo antes de cada commit.

## Interacciones que influyeron en la entrega

| Herramienta y objetivo | Prompt o instrucción relevante | Qué acepté, cambié o descarté | Cómo lo comprobé |
|---|---|---|---|
| Claude · estructurar la documentación | «Propón una estructura de documentación con requisitos funcionales, no funcionales, casos borde, datos de entrada y de salida, un ADR para las decisiones y una spec con tareas ordenadas» | Acepté la estructura (contexto → ADR → spec). Eliminé del plan el presupuesto de tiempo, las plantillas de comandos y el diagrama de ramas por no aportar a la entrega | Revisé que cada entregable exigido tuviera su documento y su tarea |
| Claude · decidir la persistencia | «Elige la opción más defendible, aplicable y con sentido entre memoria y SQLite» | Acepté SQLite tras preguntar si obligaba a instalar algo (no: `sqlite3` viene con Python). Corregí la propuesta para no nombrar un motor específico como evolución futura, solo "un motor más robusto" | Prueba de persistencia al reabrir la base y prueba manual reiniciando el servidor |
| Claude · definir validaciones | «Revisa que los supuestos no sean tan estrictos sino resilientes: tiendas con nombres largos, datos enviados como texto, que no se rompa» | La primera propuesta rechazaba demasiado. Definí el principio "tolerante con la forma, estricta con el significado", el manejo de tipos desconocidos como `Otro` conservando el original y la prioridad por defecto `Media`; aclaré que la prioridad la declara el canal | 26 casos borde con prueba automatizada |
| Claude · verificar la especificación | «Hazle una segunda revisión de verificación antes del commit» | Acepté 7 ajustes: campos ambiguos al normalizar, definición de espacios sobrantes, `null` equivalente a ausente, tipos de dato inesperados, estado desconocido, errores 404/405 y `Content-Type` ausente | Cada ajuste quedó como caso borde (CB-22 a CB-26) con su prueba |
| Claude · organizar el código | Revisión de la estructura de `app/` | La propuesta inicial era de módulos sueltos; pedí agruparlos en paquetes por capa para mejorar la lectura y actualicé el ADR-0003 | Las 86 pruebas existentes siguieron pasando tras la reorganización |
| Claude · generar código y pruebas por tarea | «Sigue con T3» (cada tarea según `02-spec.md`, prueba antes que código) | Acepté el código tarea por tarea. Detecté al ejecutar en mi equipo que `pytest` no encontraba el paquete `app` (se corrigió en `pytest.ini`) y se corrigió que la base se creaba al importar el módulo | `pytest` en mi equipo al cerrar cada tarea: 100 pruebas pasan |
| Claude · pruebas manuales | Comandos de PowerShell para probar la API en ejecución | La función propuesta no mostraba el cuerpo de los errores en PowerShell 5.1; lo detecté al ejecutarla y se corrigió | Ejecuté los 6 casos manuales y registré lo observado en `03-casos-de-prueba.md` |
| Claude · diseño de evolución | «Al ser integración, creo que código es la mejor opción» | Elegí código sobre Power Automate. Pedí recortar el borrador a una página dejando solo lo relevante | Revisé que cubriera diagrama, credenciales, indisponibilidad, reintentos y fallos |

## Reflexión

La IA me hizo avanzar más rápido al convertir mi planeación en documentos estructurados y al generar casos borde, pruebas y código repetitivo a partir de la spec.
Tuve que cuestionarla cuando sus supuestos de validación eran demasiado estrictos para datos que llegan de canales reales; ahí definí el principio de resiliencia.
También corregí decisiones que no le correspondían, como nombrar un motor de base de datos específico para el futuro.
Varios errores solo aparecieron al ejecutar en mi propio equipo (rutas de `pytest`, PowerShell 5.1), no en el entorno de la IA.
La lección: la IA acelera la construcción, pero la verificación en el entorno real y las decisiones de negocio siguen siendo mías.
