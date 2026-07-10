# Plan de implementación — Puntos 8, 9 y 10 (addenda post-reunión)

Addenda acordada **post-reunión** (Jul 2026). Complementa [ROADMAP_PRIORIZADO.md](ROADMAP_PRIORIZADO.md).

**Estado general:** ✅ Hecho (Jul 2026)  
**Última revisión:** Julio 2026

Estos ítems son **independientes** del [Punto 7 — carga de protocolos por lab](PLAN_PUNTO_7_LAB_CARGA_PROTOCOLOS.md) y entre sí; se implementaron en PRs relacionados.

---

## Resumen ejecutivo

| Ítem | Complejidad | Estimación | Estado |
|------|-------------|------------|--------|
| 8 Categoría de animal (HP + CT) | Baja | 4–8 h | ✅ Hecho |
| 9 Editar / eliminar portaobjetos (**solo HP**) | Media | 1–2 días | ✅ Hecho |
| 10 Marcar imágenes para incluir en PDF | Baja | 4–8 h | ✅ Hecho |

**Tests:** `protocols/test_roadmap_items_8_9_10.py`  
**Migración:** `protocols/migrations/0023_animal_category_and_pdf_image_flag.py`

---

## 8. Categoría de animal (HP y CT) — ✅ Hecho

### Implementado

| Cambio | Detalle |
|--------|---------|
| Modelo | `Protocol.animal_category` — `CharField`, `blank=True` |
| Formularios | `CytologyProtocolForm`, `HistopathologyProtocolForm`, `ProtocolEditForm` |
| Templates | `protocol_form.html`, `protocol_edit.html`, `protocol_detail.html` |
| PDF | `_build_animal_line()` en `report_pdf_builder.py` |
| Admin | Campo en `ProtocolAdmin` |

---

## 9. Editar / eliminar portaobjetos (solo histopatología) — ✅ Hecho

### Implementado

| Cambio | Detalle |
|--------|---------|
| Edición HP | Filas editables en `sample_register.html` cuando `can_edit_existing_slides` |
| Eliminación HP | `SlideDeleteView` + `delete_histopathology_slide()` en `protocol_service.py` |
| Auditoría | `ProcessingLog` en update/delete |
| Restricción | No eliminar slide referenciado en informe finalizado |
| CT | Sin edición/eliminación estructural (decisión mantenida) |

**Archivos:** `protocol_detail_context.py`, `views.py`, `sample_register.html`, `protocols/urls.py` (`slide_delete`).

---

## 10. Marcar imágenes para incluir en el PDF — ✅ Hecho

### Implementado

| Cambio | Detalle |
|--------|---------|
| Modelo | `ReportImage.include_in_pdf` — `BooleanField`, `default=True` |
| Formulario | Checkbox en `ReportImageForm` / formset |
| Template | `reports/_report_image_form_row.html` |
| PDF | `report_pdf_builder.py` filtra `include_in_pdf=True` |
| Migración | Default `True` para filas existentes |

---

## Referencias (diseño original)

<details>
<summary>Ver especificación previa a la implementación</summary>

### 8 — Decisión original

Agregar campo **categoría de animal** en protocolos de **histopatología y citología**.

- **v1:** campo **abierto** (texto libre).
- **Futuro:** clasificación por raza desde la facultad.

### 9 — Decisión original

Editar/eliminar portaobjetos **solo HP**; CT fuera de alcance.

### 10 — Decisión original

Booleano en `ReportImage` para elegir qué fotos van al PDF; default marcado.

</details>

---

## Referencias

- [ROADMAP_PRIORIZADO.md](ROADMAP_PRIORIZADO.md) — bloques 8, 9, 10
- [PLAN_PUNTO_7_LAB_CARGA_PROTOCOLOS.md](PLAN_PUNTO_7_LAB_CARGA_PROTOCOLOS.md) — carga delegada por lab
- [PLAN_PUNTOS_11_12.md](PLAN_PUNTOS_11_12.md) — habilitación MV y protección endpoints públicos
