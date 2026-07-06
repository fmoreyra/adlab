# Especificación: plantilla PDF de informes (3.1)

Referencia institucional: Word de la facultad (`Informe HP 25-587 MV Ricartes Brian .docx`).

## Assets versionados

| Archivo | Origen Word | Uso |
|---------|-------------|-----|
| `assets/static/images/reports/header_banner.png` | `word/media/image1.png` (2480×397) | Encabezado en cada página |
| `assets/static/images/reports/footer_banner.png` | `word/media/image3.png` (2480×290) | Pie en cada página |

Los banners se copian a `public/images/reports/` en el build de assets y se resuelven en runtime vía `django.contrib.staticfiles.finders`.

## Tipografía

- Word usa **Calibri** 12pt (cuerpo) y 14pt (títulos).
- Implementación v1: **Helvetica** en ReportLab (sin TTF adicional).
- Futuro: registrar Calibri en `assets/fonts/` si la facultad lo confirma.

## Márgenes A4

- Superior: ~1.15 in (espacio para banner)
- Inferior: ~0.85 in (espacio para pie)
- Laterales: 72 pt (1 in)

## Estructura del documento

1. `LABORATORIO DE ANATOMÍA PATOLÓGICA` (14pt, negrita, centrado)
2. `Esperanza, de {año}` (14pt, negrita, centrado) — año de `report.report_date`
3. `INFORME HISTOPATOLÓGICO Nº {protocol_number}` o `INFORME CITOLÓGICO Nº …` (14pt, negrita, centrado)
4. Metadatos (12pt): fecha de remisión, material, animal, propietario, MV comitente, fijación (HP), tinción
5. **RESULTADOS:** macro, micro, cassettes (HP), imágenes, diagnóstico
6. **OBSERVACIONES:** comentarios, recomendaciones
7. Firma digital (derecha) + bloque institucional

## Mapeo de campos

Ver plan 3.1 en el roadmap y `build_report_context()` en `src/protocols/services/report_pdf_builder.py`.

## Motor

ReportLab (`BaseDocTemplate` + callbacks de página). No se renderiza el `.docx` en producción.
