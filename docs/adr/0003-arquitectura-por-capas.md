# ADR-0003 · Arquitectura por capas

- **Estado:** Aceptado
- **Fecha:** 2026-11-26
- **Relacionado con:** RNF-02, RNF-03 (`01-contexto.md`); evolución hacia notificaciones y validación de tiendas

## Contexto

Busco un prototipo pequeño, funcional y entendible que otras personas puedan mantener, y que pueda evolucionar hacia notificaciones y validación de tiendas contra una API externa sin reescribirse. Ninguna arquitectura venía definida, así que la elegí considerando que dispongo de 150 minutos.

## Decisión

Organizo el código en **tres capas con dependencias en un solo sentido**, cada una en su propio paquete, más un paquete de utilidades transversales:

```
app/
├── main.py                    arma la aplicación
├── config.py                  configuración (DATABASE_PATH)
├── api/solicitudes.py         ──► capa HTTP
├── services/solicitudes.py    ──► capa de negocio
├── repositories/solicitudes.py──► capa de persistencia (SQLite)
├── schemas/solicitud.py       catálogos y modelo de salida
└── core/
    ├── errors.py              errores de dominio y formato uniforme
    └── normalization.py       reglas de forma
```

Dependencias: `api → services → repositories`; todas pueden usar `schemas` y `core`.

| Paquete | Responsabilidad | No hace |
|---|---|---|
| `api` | HTTP: rutas, lectura del cuerpo, códigos de respuesta | Reglas de negocio ni SQL |
| `services` | Reglas de negocio: valores por defecto, estado inicial, fecha de creación, duplicados | HTTP ni SQL |
| `repositories` | Guardar y consultar en SQLite | Validar ni decidir |
| `schemas` | Modelos de salida y catálogos (tipo, prioridad, estado) | — |
| `core` | Normalización y excepciones de dominio, usadas por varias capas | — |

Inicialmente planteé módulos sueltos dentro de `app/`. Al crecer a ocho archivos, los agrupé en paquetes por capa para que la estructura se lea a simple vista. Si se agregan más entidades (tiendas, notificaciones), cada paquete recibe un archivo por entidad.

## Alternativas consideradas

| Alternativa | Por qué la descarté |
|---|---|
| Todo en un archivo | Más rápido de escribir, pero mezcla HTTP, reglas y SQL; difícil de probar por partes y de extender con nuevas integraciones. |
| Hexagonal completa (puertos y adaptadores) | Correcta para un sistema grande, pero excesiva para dos endpoints y 150 minutos; contradice "pequeño y entendible". Tomo solo su idea principal: el repositorio es reemplazable. |

## Consecuencias

**Positivas**
- Cada capa se entiende y se prueba por separado.
- La evolución encaja sin reescribir: la notificación y el cliente del catálogo de tiendas serían servicios nuevos en `services` que el servicio de solicitudes invoca.
- Cambiar SQLite por un motor más robusto afecta solo al paquete `repositories`.

**Negativas**
- Más archivos que una solución plana para un problema pequeño.
