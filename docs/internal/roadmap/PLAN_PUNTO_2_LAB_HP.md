# Plan de implementación — Punto 2: Rediseño Lab Histopatología

Documento de planificación detallada. Complementa [ROADMAP_PRIORIZADO.md](ROADMAP_PRIORIZADO.md).

**Estado general del bloque:** ✅ Implementado (Jun 2026)  
**Última revisión:** Junio 2026

---

## Resumen ejecutivo

| Ítem | Complejidad | Estimación | Estado |
|------|-------------|------------|--------|
| 2.1 Simplificación de etapas | Media | 6–10 h | ✅ Hecho |
| 2.2 Pantalla única de registro | Media–Alta | 10–16 h | ✅ Hecho |

**Orden de implementación:** 2.1 → 2.2 (dos PRs sugeridos).

---

## Decisiones acordadas

| Tema | Decisión |
|------|----------|
| Cassettes (2.1) | Un botón **"Procesar"** por cassette (reemplaza Fijar → Incluir → Entacar) |
| Slides (2.1) | Colapsar montaje/coloración → un solo **"Marcar listo"** desde pendiente |
| Alcoholes/deshidratación | No existían en código; la simplificación aplica a `fijacion`, `inclusion`, `entacado` |
| Modelo BD | Sin migración de schema — reutilizar `fecha_*` existentes; colapsar lógica en servicios |
| Registro (2.2) | Pantalla única cassettes + slides, POST atómico; mantener `CassetteSlide` M:N |
| Superior/inferior | Eliminado en UI — multi-select de cassettes por slide, `posicion=COMPLETO` |
| Frontend | Django + JS vanilla (coherente con implementación actual) |

---

## 2.1 Simplificación de etapas — ✅ Implementado

### Cassettes: botón único "Procesado"

- Al crear cassette: sigue auto-`encasetado` (sin cambio).
- En estado del procesamiento: un solo botón **"Procesar"** mientras `estado != completado`.
- `Cassette.mark_processed()` setea `fecha_fijacion`, `fecha_inclusion`, `fecha_entacado` (now) y `estado=completado`.
- `revert_processed()` limpia las 3 fechas (requiere `observaciones`).
- Cassettes legacy en `en_proceso` con fijación parcial: **"Procesar"** completa el resto.

**Archivos:** `protocols/models.py`, `protocols/services/protocol_service.py`, templates `_cassette_timeline.html`, `_processing_actions.html`.

### Slides: botón único "Marcar listo"

- Desde `pendiente`: un clic setea `fecha_montaje`, `fecha_coloracion` y `estado=listo`.
- Revert desde `listo`: vuelve a `pendiente` limpiando fechas (motivo obligatorio).
- `get_processing_readiness()` sin cambio (sigue exigiendo `Slide.Status.LISTO`).

**Archivos:** `protocols/models.py`, `_slide_timeline.html`, `_processing_actions.html`.

### Auditoría

- `ProcessingLog` registra entrada al procesar (nota "procesado (colapsado)").

---

## 2.2 Pantalla única de registro — ✅ Implementado

### URL y vista

- **Ruta:** `/protocols/processing/register/<protocol_pk>/` → `SampleRegistrationView`
- **Legacy:** `cassette_create` y `slide_register` redirigen a la vista unificada.

### Comportamiento

**Sección superior — Cassettes**
- Filas dinámicas (1–20): código auto, descripción libre (`material_incluido`), observaciones opcionales.

**Sección inferior — Slides**
- Filas dinámicas: código auto, multi-select de cassettes (checkboxes), coloración opcional, observaciones.
- Sin columnas superior/inferior; `CassetteSlide.posicion=COMPLETO`.

**POST atómico (`@transaction.atomic`):**
1. Crear cassettes nuevos vía `ProtocolProcessingService.create_cassettes()`.
2. Crear slides + `CassetteSlide` con refs `new_{index}` / `existing_{id}`.
3. Redirect a `processing_status`.

**Modo append:** si ya hay cassettes, se pueden agregar solo slides (`cassette_count=0` permitido).

### Archivos principales

| Archivo | Cambio |
|---------|--------|
| `protocols/views.py` | `SampleRegistrationView`; redirects legacy |
| `protocols/urls.py` | Ruta `sample_register` |
| `protocols/forms.py` | `HistopathologySlideForm` sin límite de 3 cassettes |
| `protocols/services/protocol_service.py` | `register_histopathology_slides()`, fix `posicion` |
| `sample_register.html` | Template unificado |
| Navegación | `protocol_status.html`, `queue.html`, `dashboard_lab_staff.html` |

---

## Fuera de alcance (v1)

- Migración/eliminación de columnas `fecha_fijacion`, etc.
- API JSON / reintroducir Vue
- Cambios en citología (slides en recepción)
- Simplificar informes PDF o dashboard analytics más allá de ajustes WIP
- Admin Django (puede mantener acciones bulk granulares)

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Cassettes legacy a medias | `mark_processed()` completa fechas faltantes |
| Métricas dashboard desalineadas | WIP en `pages/api_views.py` conserva estados legacy |
| POST unified muy grande | Límite 20 cassettes + 50 slides; validación server-side |
| Pérdida de auditoría fina | `ProcessingLog` con nota "procesado (colapsado)" |

---

## Tests

- `protocols/tests.py` — `ProcessingViewsTest`, modelos, flujo unificado
- `protocols/tests/test_services.py` — `ProtocolProcessingServiceTest`
- Suite completa: 713 tests OK con `make test-with-sqlite`
