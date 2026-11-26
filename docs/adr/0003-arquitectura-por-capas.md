# ADR-0003 · Arquitectura por capas

- **Estado:** Aceptado
- **Fecha:** 2026-11-26
- **Relacionado con:** RNF-02, RNF-03 (`01-contexto.md`); evolución hacia notificaciones y validación de tiendas

## Contexto

Busco un prototipo pequeño, funcional y entendible que otras personas puedan mantener, y que pueda evolucionar hacia notificaciones y validación de tiendas contra una API externa sin reescribirse. Ninguna arquitectura venía definida, así que la elegí considerando que dispongo de 150 minutos.

## Decisión

Organizo el código en **tres capas con dependencias en un solo sentido**, más módulos de apoyo:

```
api.py ──► service.py ──► repository.py ──► SQLite
  │             │
  └── schemas.py (modelos y catálogos) ◄──┘
errors.py (formato uniforme de error)   normalization.py (reglas de forma)
```

| Módulo | Responsabilidad | No hace |
|---|---|---|
| `api.py` | HTTP: rutas, lectura del cuerpo, códigos de respuesta | Reglas de negocio ni SQL |
| `service.py` | Reglas de negocio: valores por defecto, estado inicial, fecha de creación, duplicados | HTTP ni SQL |
| `repository.py` | Guardar y consultar en SQLite | Validar ni decidir |
| `schemas.py` | Modelos de salida y catálogos (tipo, prioridad, estado) | — |
| `normalization.py` | Normalizar nombres de campo y valores de texto | — |
| `errors.py` | Excepciones de dominio y su traducción al formato de error | — |

## Alternativas consideradas

| Alternativa | Por qué la descarté |
|---|---|
| Todo en un archivo | Más rápido de escribir, pero mezcla HTTP, reglas y SQL; difícil de probar por partes y de extender con nuevas integraciones. |
| Hexagonal completa (puertos y adaptadores) | Correcta para un sistema grande, pero excesiva para dos endpoints y 150 minutos; contradice "pequeño y entendible". Tomo solo su idea principal: el repositorio es reemplazable. |

## Consecuencias

**Positivas**
- Cada capa se entiende y se prueba por separado.
- La evolución encaja sin reescribir: la notificación y el cliente del catálogo de tiendas serían servicios que `service.py` invoca.
- Cambiar SQLite por un motor más robusto afecta solo a `repository.py`.

**Negativas**
- Más archivos que una solución plana para un problema pequeño.
