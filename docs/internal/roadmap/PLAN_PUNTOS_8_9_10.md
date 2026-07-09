# Plan de implementación — Puntos 8, 9 y 10 (addenda post-reunión)

Addenda acordada **post-reunión** (Jul 2026). Complementa [ROADMAP_PRIORIZADO.md](ROADMAP_PRIORIZADO.md).

**Estado general:** ⬜ Pendiente (8, 9, 10)  
**Última revisión:** Julio 2026

Estos ítems son **independientes** del [Punto 7 — carga de protocolos por lab](PLAN_PUNTO_7_LAB_CARGA_PROTOCOLOS.md) y entre sí; pueden implementarse en PRs separados.

---

## Resumen ejecutivo

| Ítem | Complejidad | Estimación | Estado |
|------|-------------|------------|--------|
| 8 Categoría de animal (HP + CT) | Baja | 4–8 h | ⬜ Pendiente |
| 9 Editar / eliminar portaobjetos (**solo HP**) | Media | 1–2 días | ⬜ Pendiente |
| 10 Marcar imágenes para incluir en PDF | Baja | 4–8 h | ⬜ Pendiente |

---

## 8. Categoría de animal (HP y CT)

### Decisión

Agregar campo **categoría de animal** en protocolos de **histopatología y citología**.

- **v1:** campo **abierto** (texto libre o select con opción “Otra”).
- **Futuro:** la facultad entregará una **clasificación por raza**; migrar a choices / reglas dependientes de raza sin romper datos existentes.

### Situación actual

`Protocol` tiene `species` y `breed`; **no existe** categoría de animal.

### Implementación prevista

| Cambio | Detalle |
|--------|---------|
| Modelo | `Protocol.animal_category` — `CharField`, `blank=True`, `verbose_name` en español |
| Formularios | Create/edit HP y CT (`CytologyProtocolForm`, `HistopathologyProtocolForm`, `ProtocolEditForm`) |
| Templates | `protocol_form.html`, `protocol_edit.html`, detalle protocolo |
| PDF | Incluir en bloque de metadatos del informe (`report_pdf_builder.py`) si tiene valor |
| Admin | Campo visible en `ProtocolAdmin` |

### Fuera de alcance (v1)

- Catálogo cerrado por raza (esperar definición facultad).
- Validación cruzada raza ↔ categoría.

---

## 9. Editar / eliminar portaobjetos (solo histopatología)

### Decisión

El personal de lab debe poder **corregir** portaobjetos ya registrados y **eliminarlos** si se cargaron por error — **solo en histopatología (HP)**.

**Citología (CT): fuera de alcance.** Los portaobjetos de CT quedan **fijos al crearse** el protocolo (en recepción, según cantidad declarada). No se implementa edición ni eliminación posterior de slides en CT; errores de conteo deben corregirse **en el momento de la recepción**, no después.

> Nota: el ítem **2.3** (observaciones de banco por slide al marcar listo en CT) es un flujo aparte ya implementado; el punto 9 **no** amplía edición estructural de slides en CT.

### Situación actual

| Tipo | Comportamiento hoy |
|------|-------------------|
| **HP** | `sample_register.html` muestra cassettes/slides existentes en tabla **solo lectura**; solo se pueden **agregar** filas nuevas en visitas posteriores |
| **CT** | Slides se crean al recepcionar (`_create_cytology_slides_on_reception`); **no** deben editarse ni borrarse tras la recepción (decisión punto 9) |
| **Eliminar** | No hay flujo UI para borrar un `Slide` persistido (HP tampoco; es lo que agrega 9) |

### Implementación prevista

**Alcance:** solo protocolos `analysis_type=histopathology`.

**Permisos:** `StaffRequiredMixin`; solo mientras el protocolo esté en `received` o `processing` (no en `ready` / informe finalizado).

**HP — editar slide existente:**
- Campos editables: `tecnica_coloracion`, `observaciones`, vínculos a cassettes (`CassetteSlide`).
- UI: filas editables en `sample_register.html` o vista dedicada de mantenimiento de slides.

**HP — eliminar slide:**
- Confirmación explícita; registrar en `ProcessingLog`.
- Validar: no eliminar si el slide está referenciado en `ReportImage` de informe **finalizado** (o desvincular con advertencia).

**CT — sin cambios en este ítem:**
- No exponer acciones de editar/eliminar slide en UI ni API para citología.

**Auditoría:** `ProcessingLog` con acción de edición/eliminación y usuario (solo HP).

### Archivos probables

`protocols/models.py` (Slide), `protocol_service.py`, `sample_register.html`, `views.py`, tests de procesamiento HP.

### Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Códigos de portaobjetos únicos al reordenar | Regenerar o bloquear cambio de código si ya hay referencias |
| Informe ya elaborado | Bloquear delete; permitir editar observaciones solo en borrador de informe |
| Integridad M:N cassette–slide | Transacción atómica al actualizar `CassetteSlide` |

---

## 10. Marcar imágenes para incluir en el PDF

### Decisión

Al cargar imágenes al informe (galería macro/micro), el usuario debe poder **marcar cuáles van al PDF** final — no todas están obligadas a imprimirse.

### Situación actual

`ReportImage` no tiene flag de inclusión. El PDF embebe **todas** las imágenes del informe:

```python
report_images = report.images.order_by("order", "created_at")
# ... todas se procesan en report_pdf_builder.py
```

### Implementación prevista

| Cambio | Detalle |
|--------|---------|
| Modelo | `ReportImage.include_in_pdf` — `BooleanField`, `default=True`, help_text en español |
| Migración | Default `True` para filas existentes |
| Formulario | Checkbox en `ReportImageForm` / formset de edición de informe |
| Template | `reports/edit.html` — columna o toggle “Incluir en PDF” |
| PDF | `report_pdf_builder.py` filtra `images.filter(include_in_pdf=True)` |
| Galería web | Puede seguir mostrando **todas** las imágenes; solo el PDF respeta el flag |

### Comportamiento UX

- Default **marcado** al subir imagen nueva (comportamiento actual preservado).
- Desmarcar = la imagen queda en el informe digital pero **no** sale en el PDF adjunto al MV.

### Tests

- PDF con 3 imágenes, 1 desmarcada → solo 2 en PDF.
- Imágenes existentes post-migración → todas incluidas (`default=True`).

---

## Referencias

- [ROADMAP_PRIORIZADO.md](ROADMAP_PRIORIZADO.md) — bloques 8, 9, 10
- [PLAN_PUNTO_7_LAB_CARGA_PROTOCOLOS.md](PLAN_PUNTO_7_LAB_CARGA_PROTOCOLOS.md) — carga delegada por lab (punto aparte)
