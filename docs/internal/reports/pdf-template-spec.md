# Especificación: plantilla PDF de informes (3.1)

Referencia institucional: Word renovado de la facultad
(`Informe HP 25-587 MV Ricartes Brian .docx`, jul 2026).

## Assets versionados

| Archivo | Origen Word | Uso |
|---------|-------------|-----|
| `assets/static/images/reports/header_banner.png` | Marca del Word (logo FCV + 3 líneas) + línea separadora | Encabezado en cada página |
| `assets/static/images/reports/footer_banner.png` | `word/media/image2.png` (recortado, sin padding lateral embebido) | Pie en cada página |
| `assets/fonts/carlito/*.ttf` + `OFL.txt` | Sustituto libre de Calibri (SIL OFL 1.1) | Tipografía del cuerpo del PDF |

## Tipografía

- Word usa **Calibri** 12pt (cuerpo) y 14pt (títulos).
- **Calibri no se redistribuye** (licencia Microsoft). En su lugar usamos
  **Carlito** (métricamente compatible con Calibri, misma opción que LibreOffice).
- **Latinaires** (header “HOSPITAL…”): tipografía comercial Sudtipos; no se
  versiona en el repo. La marca del header ya está rasterizada en
  `header_banner.png`.
- Registro ReportLab: `register_report_fonts()` en
  `src/protocols/services/report_pdf_fonts.py` (fallback a Helvetica si faltan
  los TTF).

## Márgenes A4

- Cuerpo (laterales): 0.5 in (720 twips, igual que el Word renovado)
- Banners header/footer: 0.2 in laterales (más anchos que el cuerpo)
- Superior: ~1.22 in (banner + respiro corto hasta el título)
- Inferior: ~0.85 in (espacio para pie)

## Estructura del documento

1. Banner institucional (logo FCV circular + UNL/Facultad + Hospital Escuela)
2. `LABORATORIO DE ANATOMÍA PATOLÓGICA` (14pt, negrita, centrado)
3. `Esperanza, {fecha larga}` (14pt, negrita, centrado) — `report.report_date`
   (fecha de emisión / finalización del informe)

4. `INFORME HISTOPATOLÓGICO Nº {protocol_number}` o `INFORME CITOLÓGICO Nº …`
   (14pt, negrita, centrado)
5. Metadatos (12pt): fecha de remisión, material, animal, propietario, MV
   comitente, fijación (HP), tinción — etiquetas en negrita sutil + valor
   regular
6. **RESULTADOS:** macro, micro, cassettes (HP), imágenes, diagnóstico
7. **OBSERVACIONES:** comentarios, recomendaciones
8. Firma digital (derecha) + bloque institucional
9. Banner de pie (dirección / teléfono)

## Mapeo de campos

Ver plan 3.1 en el roadmap y `build_report_context()` en
`src/protocols/services/report_pdf_builder.py`.

## Motor

ReportLab (`BaseDocTemplate` + callbacks de página). No se renderiza el `.docx`
en producción.
