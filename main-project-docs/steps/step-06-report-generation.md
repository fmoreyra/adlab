# Step 06: Report Generation & PDF Creation

## Problem Statement

Histopathologists currently write reports by hand, which are then manually transcribed into digital format, leading to transcription errors, time waste, and inconsistent formatting. The system needs to automatically generate pre-filled report templates with all case information, allow histopathologists to add their observations and diagnosis, and produce professional PDF reports with digital signatures that can be immediately sent to veterinarians.

## Requirements

### Functional Requirements (RF07)

- **RF07.1**: Auto-generate report template with pre-filled data:
  - Protocol information (species, breed, age, presumptive diagnosis)
  - Processing data (slides, cassettes, material included)
  - Client data (veterinarian contact information)
  - Histopathologist data (name, license number, digital signature)
- **RF07.2**: Rich text editor for observations by cassette
- **RF07.3**: PDF generation with institutional format/branding
- **RF07.4**: One-click email delivery to veterinarian
- **RF07.5**: Simultaneous generation of Work Order (OT)
- **RF07.6**: Archive of sent documents
- Support for multiple report revisions
- Report preview before sending
- Ability to attach images (microscopy photos)

### Non-Functional Requirements

- **PDF Quality**: Professional formatting, consistent branding
- **Generation Speed**: PDF generated in < 10 seconds
- **Reliability**: 100% PDF generation success rate
- **Deliverability**: 98%+ email delivery success
- **Audit**: All reports logged with timestamp and recipient

## Data Model

### Informe_Resultados Table
```sql
informe_resultados (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  protocolo_id: INTEGER NOT NULL,
  histopatologo_id: INTEGER NOT NULL,
  veterinario_id: INTEGER NOT NULL,
  
  -- Content
  observaciones_macro: TEXT, -- Macroscopic observations
  observaciones_micro: TEXT, -- Microscopic observations (per cassette)
  diagnostico: TEXT NOT NULL,
  comentarios: TEXT,
  recomendaciones: TEXT,
  
  -- Metadata
  fecha_informe: DATE NOT NULL,
  version: INTEGER DEFAULT 1,
  estado: ENUM('borrador', 'finalizado', 'enviado') DEFAULT 'borrador',
  
  -- Files
  pdf_path: VARCHAR(500),
  pdf_hash: VARCHAR(64), -- SHA-256 for integrity
  
  -- Sending info
  fecha_envio: DATETIME,
  email_enviado_a: VARCHAR(255),
  email_estado: ENUM('pendiente', 'enviado', 'fallido', 'rebotado'),
  email_error: TEXT,
  
  created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  FOREIGN KEY (protocolo_id) REFERENCES protocolo(id),
  FOREIGN KEY (histopatologo_id) REFERENCES histopatologo(id),
  FOREIGN KEY (veterinario_id) REFERENCES veterinario(id)
)
```

### Informe_Observaciones_Cassette Table
```sql
informe_observaciones_cassette (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  informe_id: INTEGER NOT NULL,
  cassette_id: INTEGER NOT NULL,
  observaciones: TEXT NOT NULL,
  diagnostico_parcial: TEXT,
  orden: INTEGER DEFAULT 0, -- Display order
  
  FOREIGN KEY (informe_id) REFERENCES informe_resultados(id) ON DELETE CASCADE,
  FOREIGN KEY (cassette_id) REFERENCES cassette(id)
)
```

### Informe_Imagenes Table (optional, for microscopy photos)
```sql
informe_imagenes (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  informe_id: INTEGER NOT NULL,
  cassette_id: INTEGER,
  portaobjetos_id: INTEGER,
  imagen_path: VARCHAR(500) NOT NULL,
  descripcion: TEXT,
  magnificacion: VARCHAR(50), -- e.g., "400x"
  tecnica: VARCHAR(100), -- e.g., "H&E", "PAS"
  orden: INTEGER DEFAULT 0,
  
  FOREIGN KEY (informe_id) REFERENCES informe_resultados(id) ON DELETE CASCADE,
  FOREIGN KEY (cassette_id) REFERENCES cassette(id),
  FOREIGN KEY (portaobjetos_id) REFERENCES portaobjetos(id)
)
```

### Histopatologo Table (if not exists from Step 01)
```sql
histopatologo (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  user_id: INTEGER UNIQUE NOT NULL,
  apellido: VARCHAR(100) NOT NULL,
  nombre: VARCHAR(100) NOT NULL,
  nro_matricula: VARCHAR(50) UNIQUE NOT NULL,
  cargo: VARCHAR(100), -- e.g., "Profesor Titular", "Profesor Asociado"
  firma_digital_path: VARCHAR(500), -- Path to signature image
  especialidad: VARCHAR(200),
  
  created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)
```

## API Design

### Report Generation Endpoints

#### GET /api/reports/template/:protocolo_id
Get pre-filled report template for a protocol.

**Response (200 OK):**
```json
{
  "template": {
    "protocolo": {
      "numero": "HP 24/123",
      "fecha_recepcion": "2024-10-11",
      "especie": "Felino",
      "raza": "Mestizo",
      "sexo": "hembra",
      "edad": "8 años",
      "identificacion": "Luna",
      "propietario": "Carlos Rodríguez",
      "diagnostico_presuntivo": "Tumor mamario",
      "historia_clinica": "Masa en cadena mamaria, Qx resección"
    },
    "veterinario": {
      "nombre": "Dr. Carlos Rodríguez",
      "email": "carlos@vet.com",
      "telefono": "+54 342 1234567",
      "matricula": "MP-12345"
    },
    "procesamiento": {
      "cassettes": [
        {
          "codigo": "HP 24/123-C1",
          "material": "Masa de 3x2cm de cadena mamaria izquierda"
        }
      ],
      "slides": [
        {
          "codigo": "HP 24/123-S1",
          "cassettes": ["HP 24/123-C1"],
          "tecnica": "Hematoxilina-Eosina"
        }
      ]
    },
    "histopatologo": {
      "nombre": "Dra. Ana López",
      "matricula": "MV-54321",
      "cargo": "Profesora Asociada",
      "firma_url": "/signatures/ana-lopez.png"
    }
  }
}
```

#### POST /api/reports
Create new report (draft).

**Request:**
```json
{
  "protocolo_id": 123,
  "observaciones_macro": "Se recibe masa nodular bien delimitada de 3x2x1.5cm",
  "observaciones_cassettes": [
    {
      "cassette_id": 456,
      "observaciones": "Se observa proliferación neoplásica de células epiteliales...",
      "diagnostico_parcial": "Carcinoma mamario"
    }
  ],
  "diagnostico": "Carcinoma mamario simple, grado II",
  "comentarios": "Márgenes quirúrgicos libres de neoplasia",
  "recomendaciones": "Control post-operatorio. Considerar estudio de metástasis"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "informe": {
    "id": 789,
    "protocolo_numero": "HP 24/123",
    "estado": "borrador",
    "fecha_informe": "2024-10-15"
  }
}
```

#### PUT /api/reports/:id
Update report (only drafts can be edited).

**Request:** Same as create
**Response (200 OK):** Updated report data

#### POST /api/reports/:id/finalize
Finalize report and generate PDF.

**Request:**
```json
{
  "incluir_imagenes": true,
  "formato": "completo" // or "resumido"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "informe": {
    "id": 789,
    "estado": "finalizado",
    "pdf_url": "/api/reports/789/pdf",
    "pdf_size": "245KB"
  }
}
```

#### GET /api/reports/:id/pdf
Download report PDF.

**Response:** PDF file with appropriate headers
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="Informe_HP_24_123.pdf"
```

#### POST /api/reports/:id/send
Send report via email to veterinarian.

**Request:**
```json
{
  "email_adicional": "otro@email.com", // Optional additional recipient
  "mensaje_personalizado": "Adjunto encontrará el informe solicitado...", // Optional
  "incluir_ot": true // Include Work Order in same email
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Informe enviado exitosamente",
  "enviado_a": ["carlos@vet.com"],
  "fecha_envio": "2024-10-15T14:30:00Z",
  "informe": {
    "estado": "enviado"
  }
}
```

#### GET /api/reports/pending
Get list of protocols pending report generation.

**Response (200 OK):**
```json
{
  "pending": [
    {
      "protocolo_id": 124,
      "protocolo_numero": "HP 24/124",
      "animal": "Max - Canino",
      "fecha_recepcion": "2024-10-12",
      "dias_pendiente": 3,
      "slides_listos": 3
    }
  ],
  "total": 8
}
```

#### GET /api/reports/history
Get history of sent reports.

**Query Parameters:**
- `fecha_desde`, `fecha_hasta`, `veterinario_id`, `histopatologo_id`

**Response (200 OK):**
```json
{
  "reports": [
    {
      "id": 789,
      "protocolo_numero": "HP 24/123",
      "animal": "Luna - Felino",
      "veterinario": "Dr. Carlos Rodríguez",
      "diagnostico": "Carcinoma mamario simple, grado II",
      "fecha_envio": "2024-10-15T14:30:00Z",
      "pdf_url": "/api/reports/789/pdf"
    }
  ],
  "pagination": { /* ... */ }
}
```

#### POST /api/reports/:id/resend
Resend report email (in case of delivery failure).

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Informe reenviado exitosamente"
}
```

## Business Logic

### Report Template Structure

**Header Section:**
- Laboratory logo and name
- Report date
- Protocol number
- Veterinarian information

**Case Information:**
- Animal data (species, breed, age, name)
- Owner information
- Presumptive diagnosis
- Clinical history

**Material Received:**
- Description of sample (from protocol)
- Number of jars/slides received
- Reception date

**Processing Information:**
- Cassettes created (codes and content)
- Slides prepared (codes and staining techniques)

**Macroscopic Description:**
- Histopathologist's macroscopic observations

**Microscopic Description:**
- Observations per cassette/slide
- Structured by anatomical/pathological findings

**Diagnosis:**
- Final pathological diagnosis
- Classification/grading if applicable

**Comments and Recommendations:**
- Additional clinical context
- Suggested follow-up
- Prognosis if applicable

**Signature:**
- Histopathologist name and license number
- Digital signature image
- Report date

### PDF Generation Process

1. Load report data from database
2. Load template (HTML/CSS or LaTeX)
3. Inject data into template
4. Render to PDF
5. Add digital signature image
6. Save PDF to file system
7. Calculate and store PDF hash (integrity)
8. Update report status to "finalizado"

### Email Delivery Logic

**Email Template:**
```html
Subject: Informe Histopatológico - Protocolo HP 24/123

Estimado/a Dr./Dra. Rodríguez,

Adjunto encontrará el informe histopatológico correspondiente a:

Protocolo: HP 24/123
Animal: Luna (Felino)
Fecha de recepción: 11/10/2024
Diagnóstico: Carcinoma mamario simple, grado II

Puede descargar el informe en formato PDF adjunto.

Para cualquier consulta, no dude en contactarnos.

Saludos cordiales,
Dra. Ana López
Laboratorio de Anatomía Patológica Veterinaria
```

**Attachments:**
- Report PDF (Informe_HP_24_123.pdf)
- Work Order PDF (OT_123.pdf) - if requested

**Delivery Tracking:**
- Log email send attempt
- Track delivery status (sent/failed/bounced)
- Retry failed sends (3 attempts)
- Alert on persistent failures

### Report Revisions

- Each report has a version number (starts at 1)
- If report needs correction after sending:
  - Increment version number
  - Mark previous version as "superseded"
  - Generate new PDF with "VERSIÓN 2" watermark
  - Send updated report with explanation

## Acceptance Criteria

1. ✅ Histopathologists can view pre-filled report template
2. ✅ Template includes all protocol and processing data
3. ✅ Observations can be added per cassette
4. ✅ Reports can be saved as drafts
5. ✅ Draft reports can be edited
6. ✅ Final reports generate PDF correctly
7. ✅ PDF includes all required elements (header, data, signature)
8. ✅ PDF can be previewed before sending
9. ✅ Reports can be sent via email with one click
10. ✅ Email delivery is tracked and logged
11. ✅ Sent reports are archived and downloadable
12. ✅ Report history is accessible and searchable

## Testing Approach

### Unit Tests
- Template data extraction
- PDF generation logic
- Email formatting
- Hash calculation

### Integration Tests
- Complete report creation flow
- PDF generation with all elements
- Email sending with attachments
- Report versioning

### E2E Tests
- Histopathologist views template → writes observations → finalizes → previews PDF → sends email → veterinarian receives
- Report sent → delivery fails → automatic retry → successful delivery
- Report sent → correction needed → version 2 created → sent with explanation

### PDF Tests
- Generate PDF with complete data
- Verify all sections present
- Verify signature image included
- Verify formatting is consistent
- Test with edge cases (very long text, special characters)

### Email Tests
- Send to valid email → delivered
- Send to invalid email → bounced and logged
- Send with large attachment → handled correctly
- Multiple recipients → all receive

## Technical Considerations

### 🔧 Pending Technical Decisions

1. **PDF Generation Library**:
   - wkhtmltopdf (HTML/CSS to PDF)
   - Puppeteer/Playwright (headless browser)
   - ReportLab (Python) / TCPDF (PHP) / PDFKit (Node)
   - LaTeX (high quality typography)

2. **Template Engine**:
   - Handlebars / Mustache
   - Jinja2 (Python)
   - Twig (PHP)
   - EJS (Node)

3. **File Storage**:
   - Local filesystem
   - AWS S3 / Google Cloud Storage
   - Database BLOB storage

4. **Email Service**:
   - Institutional SMTP
   - SendGrid
   - Amazon SES
   - Mailgun

### Performance Optimization
- Cache generated PDFs (don't regenerate on each download)
- Asynchronous PDF generation for large reports
- Queue system for email sending
- CDN for signature images and logos

### Security Considerations
- Access control: Only authorized users can view reports
- PDF encryption (optional, for sensitive cases)
- Secure file storage (proper permissions)
- Audit all report access and downloads
- Rate limiting on email sending

## Dependencies

### Must be completed first:
- Step 01: Authentication & User Management
- Step 03: Protocol Submission
- Step 04: Sample Reception
- Step 05: Sample Processing

### Enables these steps:
- Step 07: Work Order Management (sent together)
- Step 09: Dashboard (metrics on reports sent)

## Estimated Effort

**Time**: 1.5 weeks (Sprint 9-10)

**Breakdown**:
- Database schema: 0.5 days
- Template generation API: 2 days
- Report creation/editing: 2 days
- PDF generation: 2 days
- Email sending: 1 day
- Frontend report interface: 2 days
- Testing: 2 days

## Implementation Notes

### Development Phases
1. **Phase 1**: Template data extraction and display
2. **Phase 2**: Report creation and editing (drafts)
3. **Phase 3**: PDF generation
4. **Phase 4**: Email sending
5. **Phase 5**: Report history and versioning

### PDF Template Example (HTML/CSS)
```html
<!DOCTYPE html>
<html>
<head>
  <style>
    @page { margin: 2cm; }
    body { font-family: Arial, sans-serif; }
    .header { text-align: center; border-bottom: 2px solid #333; }
    .section { margin: 20px 0; }
    .signature { margin-top: 40px; text-align: right; }
  </style>
</head>
<body>
  <div class="header">
    <img src="logo.png" height="80">
    <h1>INFORME HISTOPATOLÓGICO</h1>
    <p>Protocolo: {{protocolo_numero}}</p>
  </div>
  
  <div class="section">
    <h2>DATOS DEL PACIENTE</h2>
    <p>Especie: {{especie}} | Raza: {{raza}} | Edad: {{edad}}</p>
    <p>Identificación: {{identificacion}}</p>
  </div>
  
  <!-- More sections... -->
  
  <div class="signature">
    <img src="{{firma_url}}" height="60">
    <p>{{histopatologo_nombre}}</p>
    <p>Mat. {{histopatologo_matricula}}</p>
  </div>
</body>
</html>
```

### Testing Checklist
- [ ] Template loads with all data
- [ ] Observations can be added per cassette
- [ ] Draft saves and loads correctly
- [ ] PDF generates with all sections
- [ ] PDF includes signature image
- [ ] Email sends successfully
- [ ] Email attachments are correct
- [ ] Delivery is tracked and logged
- [ ] Failed sends are retried
- [ ] Reports are archived and downloadable

### Sample Report Data
```json
{
  "observaciones_macro": "Se recibe masa nodular de 3x2x1.5cm, bien delimitada, de consistencia firme y coloración blanquecina al corte",
  "observaciones_cassettes": [
    {
      "cassette_codigo": "HP 24/123-C1",
      "observaciones": "Proliferación neoplásica de células epiteliales dispuestas en nidos y cordones. Núcleos pleomórficos con moderada actividad mitótica. Estroma desmoplásico.",
      "diagnostico": "Carcinoma mamario simple"
    }
  ],
  "diagnostico": "CARCINOMA MAMARIO SIMPLE, GRADO II DE MALIGNIDAD",
  "comentarios": "Los márgenes quirúrgicos se encuentran libres de proliferación neoplásica.",
  "recomendaciones": "Se recomienda control post-operatorio y evaluación de posibles metástasis ganglionares."
}
```

