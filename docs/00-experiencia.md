# 00 · Mi experiencia

Tres proyectos en los que participé: el problema, las tecnologías, mi contribución, una decisión difícil o limitación y qué cambiaría hoy.

## 1. Registro de incidentes en visitas a tiendas (Power Apps)

- **Problema:** en una cadena de tiendas con sedes en todo el país, los técnicos dan soporte presencial a los equipos informáticos de cada tienda. Los incidentes se documentaban en hojas: el registro era lento, quedaba disperso y no servía para decidir qué atender primero.
- **Tecnologías:** Power Apps para registrar desde la tienda, una lista de SharePoint como base de datos, Power BI para el seguimiento y Power Automate para automatizar los procesos siguientes. Era adecuado porque la empresa ya usaba Microsoft 365: no hubo que montar infraestructura y la app se usaba desde cualquier dispositivo.
- **Mi contribución:** participé en el análisis del proceso (qué debía registrar el técnico y qué preguntas debía responder el tablero) y en el desarrollo de la app y del tablero.
- **Limitación:** SharePoint no es una base de datos relacional. Tiene límites de delegación y no garantiza integridad referencial, así que la calidad de los datos dependía del formulario. Usamos listas cerradas para tienda y tipo de incidente y, cuando creció el volumen, evaluamos migrar la base de datos.
- **Qué cambiaría hoy:** haría esa migración a Dataverse o SQL, con un catálogo de tiendas validado. Además definiría desde el inicio el estado y la prioridad del incidente y automatizaría las alertas de incidentes críticos sin avisos duplicados.

## 2. Tienda e-commerce: backend y frontend (Node.js + React)

- **Problema:** una tienda necesitaba vender en línea con un catálogo por categorías, órdenes de compra que descuentan inventario sin vender más de lo que hay, y una administración separada por roles (cliente y administrador).
- **Tecnologías:** Node.js con Express y PostgreSQL, JWT y bcrypt, middleware por rol, migraciones SQL versionadas y React con Vite. Express es liviano para una API de este tamaño y PostgreSQL da integridad con llaves foráneas y transacciones.
- **Mi contribución:** desarrollé la autenticación (registro, login con JWT y contraseñas con bcrypt), la administración de usuarios con control por rol y los CRUD de productos y categorías, con sus validaciones y consultas sobre PostgreSQL. También trabajé las órdenes con descuento de stock y las migraciones del esquema.
- **Decisión difícil:** convivían dos columnas de estado de la orden (`status` y `estado`). Las unifiqué con dos migraciones (copiar datos y luego eliminar la vieja) y un backup previo. Además, la orden se crea en una transacción con `SELECT … FOR UPDATE` para que dos compras simultáneas no dejen el stock negativo.
- **Qué cambiaría hoy:** validaría las entradas con un esquema (zod o joi) en lugar de hacerlo a mano en cada controlador, usaría una herramienta de migraciones y agregaría pruebas automáticas.

## 3. Actas de entrega de periféricos con firma (Power Apps)

- **Problema:** en la empresa donde trabajo, la entrega de periféricos a los usuarios (teclados, mouse, diademas, monitores, etc.) se soportaba con actas que no quedaban conectadas al inventario de activos. Era difícil saber qué tenía asignado cada persona y probar que lo había recibido.
- **Tecnologías:** Power Apps para diligenciar el acta y capturar la firma de entrega, y SharePoint como base de datos, conectado al inventario de activos de la empresa. Encajaba con Microsoft 365, que ya estaba en uso, y permitía firmar en el momento de la entrega, sin papel.
- **Mi contribución:** participé en el análisis del proceso, en el diseño de la app (campos del acta, flujo de entrega y firma, relación con el inventario) y en las pruebas antes de su uso.
- **Decisión difícil:** había que evitar que un mismo activo quedara entregado a dos personas. La entrega se registra contra el activo del inventario y cambia su estado, de modo que el acta y el inventario no se contradigan.
- **Qué cambiaría hoy:** generaría el acta firmada en PDF con Power Automate y la enviaría por correo al usuario. También agregaría el flujo de devolución para que el activo vuelva a quedar disponible.
