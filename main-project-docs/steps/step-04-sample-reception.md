# Step 04: Sample Reception & Protocol Assignment

## Problem Statement

When physical samples arrive at the laboratory, they need to be matched with their corresponding digital protocols, verified for completeness, assigned final protocol numbers, and properly labeled for tracking throughout the analysis process. Currently, this is done manually with paper records, leading to potential mismatches, mislabeling, and lost samples. A digital reception system is needed to streamline this critical handoff point and ensure accurate tracking.

## Requirements

### Functional Requirements (RF03)

- **RF03.1**: Search and retrieve protocols by temporary tracking code
- **RF03.2**: Confirm physical arrival of sample and match to protocol
- **RF03.3**: Generate printable labels with final protocol number
- **RF03.4**: Record date and time of reception
- **RF03.5**: Send automatic email notification to veterinarian confirming reception
- Verify sample condition and completeness
- Handle discrepancies between protocol and physical sample
- Batch reception processing for multiple samples
- Reception history and audit trail

### Non-Functional Requirements

- **Speed**: Reception process < 2 minutes per sample
- **Accuracy**: Zero tolerance for sample mislabeling
- **Reliability**: 100% email delivery success rate
- **Usability**: Interface optimized for quick data entry

## Data Model

### Updates to Existing Tables

```sql
-- Add to protocolo table
ALTER TABLE protocolo ADD COLUMN:
  fecha_recepcion: DATETIME,
  recibido_por: INTEGER, -- User who received the sample
  condicion_muestra: ENUM('optima', 'aceptable', 'suboptima', 'rechazada'),
  observaciones_recepcion: TEXT,
  discrepancias: TEXT, -- Notes on any mismatches
  
FOREIGN KEY (recibido_por) REFERENCES users(id)

-- Update muestra_citologia
ALTER TABLE muestra_citologia ADD COLUMN:
  fecha_recepcion: DATETIME,
  numero_portaobjetos_recibidos: INTEGER, -- May differ from expected
  
-- Update muestra_histopatologia
ALTER TABLE muestra_histopatologia ADD COLUMN:
  fecha_recepcion: DATETIME,
  numero_frascos_recibidos: INTEGER, -- May differ from expected
```

### Reception Log Table
```sql
recepcion_log (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  protocolo_id: INTEGER NOT NULL,
  accion: VARCHAR(100) NOT NULL, -- 'recibido', 'rechazado', 'discrepancia_reportada'
  usuario_id: INTEGER NOT NULL,
  observaciones: TEXT,
  created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (protocolo_id) REFERENCES protocolo(id),
  FOREIGN KEY (usuario_id) REFERENCES users(id)
)
```

### Protocol Numbering Counter Table
```sql
protocolo_contador (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  tipo_analisis: ENUM('citologia', 'histopatologia') NOT NULL,
  año: INTEGER NOT NULL,
  ultimo_numero: INTEGER NOT NULL DEFAULT 0,
  UNIQUE KEY (tipo_analisis, año)
)
```

## API Design

### Sample Reception Endpoints

#### GET /api/reception/search
Search for protocol by temporary code.

**Query Parameters:**
- `codigo`: Temporary tracking code (e.g., "TMP-HP-20241010-457")

**Response (200 OK):**
```json
{
  "protocolo": {
    "id": 457,
    "codigo_temporal": "TMP-HP-20241010-457",
    "tipo_analisis": "histopatologia",
    "estado": "enviado",
    "veterinario": {
      "nombre": "Carlos Rodríguez",
      "email": "carlos@vet.com",
      "telefono": "+54 342 1234567"
    },
    "animal": {
      "especie": "Felino",
      "identificacion": "Luna"
    },
    "muestra": {
      "material_remitido": "Masa de 3x2cm de cadena mamaria izquierda",
      "numero_frascos": 1
    },
    "fecha_remision": "2024-10-10"
  }
}
```

#### POST /api/reception/receive
Register sample reception and assign final protocol number.

**Request:**
```json
{
  "codigo_temporal": "TMP-HP-20241010-457",
  "condicion_muestra": "optima",
  "numero_frascos_recibidos": 1,
  "observaciones_recepcion": "Muestra en buen estado, formol suficiente",
  "discrepancias": null
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Muestra recibida exitosamente",
  "protocolo": {
    "id": 457,
    "numero_protocolo": "HP 24/123",
    "codigo_temporal": "TMP-HP-20241010-457",
    "estado": "recibido",
    "fecha_recepcion": "2024-10-11T09:15:00Z",
    "etiquetas": {
      "url_pdf": "/api/reception/457/labels",
      "codigo_qr": "/api/reception/457/qr"
    }
  }
}
```

#### GET /api/reception/:id/labels
Generate printable labels for sample.

**Response:** PDF file with labels
- Contains protocol number in large text
- QR code with protocol number
- Animal identification
- Date of reception
- Laboratory logo

#### POST /api/reception/:id/report-discrepancy
Report discrepancy between protocol and physical sample.

**Request:**
```json
{
  "tipo_discrepancia": "cantidad_frascos",
  "esperado": 2,
  "recibido": 1,
  "descripcion": "Se esperaban 2 frascos según protocolo, solo llegó 1",
  "accion_tomada": "notificar_veterinario"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Discrepancia registrada",
  "notificacion_enviada": true
}
```

#### POST /api/reception/batch
Receive multiple samples in batch.

**Request:**
```json
{
  "recepciones": [
    {
      "codigo_temporal": "TMP-CT-20241010-456",
      "condicion_muestra": "optima",
      "numero_portaobjetos_recibidos": 2
    },
    {
      "codigo_temporal": "TMP-HP-20241010-457",
      "condicion_muestra": "optima",
      "numero_frascos_recibidos": 1
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "recibidos": 2,
  "errores": 0,
  "protocolos": [
    {
      "numero_protocolo": "CT 24/089",
      "codigo_temporal": "TMP-CT-20241010-456"
    },
    {
      "numero_protocolo": "HP 24/123",
      "codigo_temporal": "TMP-HP-20241010-457"
    }
  ]
}
```

#### GET /api/reception/pending
Get list of protocols awaiting reception.

**Query Parameters:**
- `tipo`: Filter by analysis type
- `fecha_desde`: Date from
- `fecha_hasta`: Date to

**Response (200 OK):**
```json
{
  "pending": [
    {
      "id": 458,
      "codigo_temporal": "TMP-HP-20241012-458",
      "veterinario": "Ana García",
      "animal": "Max - Canino",
      "fecha_remision": "2024-10-12",
      "dias_pendiente": 2
    }
  ],
  "total": 15
}
```

#### GET /api/reception/history
Get reception history/log.

**Query Parameters:**
- `fecha_desde`, `fecha_hasta`, `usuario_id`, `page`, `limit`

**Response (200 OK):**
```json
{
  "recepciones": [
    {
      "protocolo_numero": "HP 24/123",
      "animal": "Luna - Felino",
      "fecha_recepcion": "2024-10-11T09:15:00Z",
      "recibido_por": "María López",
      "condicion": "optima"
    }
  ],
  "pagination": { /* ... */ }
}
```

## Business Logic

### Protocol Numbering Logic

**Sequential Numbering per Type and Year:**
```javascript
function generateProtocolNumber(tipo, año) {
  // Get or create counter for type and year
  let counter = getCounter(tipo, año);
  
  // Increment counter
  counter.ultimo_numero += 1;
  
  // Format: TYPE YY/NNN
  const prefix = tipo === 'citologia' ? 'CT' : 'HP';
  const yearShort = año.toString().slice(-2);
  const number = counter.ultimo_numero.toString().padStart(3, '0');
  
  return `${prefix} ${yearShort}/${number}`;
}

// Examples:
// generateProtocolNumber('histopatologia', 2024) -> "HP 24/001"
// generateProtocolNumber('citologia', 2024) -> "CT 24/001"
```

**Numbering Rules:**
- Reset counter to 0 on January 1st each year
- Separate counters for cytology and histopathology
- Numbers are never reused
- Gaps in numbering are acceptable (e.g., if protocol is cancelled)

### Sample Verification Checklist

**For Histopathology:**
- ✅ Physical jars match number in protocol
- ✅ Each jar is properly labeled with temporary code
- ✅ Formol level is adequate (tissue fully submerged)
- ✅ No leakage or container damage
- ✅ Tissue sample matches description in protocol

**For Cytology:**
- ✅ Slide count matches protocol
- ✅ Slides properly labeled with temporary code
- ✅ Slides are intact (not broken)
- ✅ Sample quality is adequate for analysis

### Condition Assessment
- **Óptima**: Perfect condition, ready for processing
- **Aceptable**: Minor issues but processable
- **Subóptima**: Significant issues, quality may be compromised
- **Rechazada**: Cannot be processed, must contact veterinarian

### Discrepancy Handling

**Common Discrepancies:**
1. **Quantity mismatch**: Expected N samples, received M
2. **Missing identification**: Sample not labeled with code
3. **Damaged sample**: Broken slides, leaked jars
4. **Wrong sample**: Physical sample doesn't match description

**Resolution Process:**
1. Document discrepancy in system
2. Photograph sample if needed
3. Contact veterinarian immediately
4. Update protocol status to "en_espera" (on hold)
5. Await veterinarian response/action
6. Proceed or reject sample based on resolution

### Email Notification Content
```
Subject: Muestra recibida - Protocolo HP 24/123

Estimado/a Dr./Dra. [Veterinario],

Confirmamos la recepción de la muestra correspondiente al protocolo:

Número de Protocolo: HP 24/123
Código temporal: TMP-HP-20241010-457
Animal: Luna (Felino)
Fecha de recepción: 11/10/2024 09:15

Puede consultar el estado de su protocolo en:
[link to portal]

Saludos cordiales,
Laboratorio de Anatomía Patológica Veterinaria
```

## Acceptance Criteria

1. ✅ Laboratory staff can search protocol by temporary code
2. ✅ System displays complete protocol information for verification
3. ✅ Staff can confirm sample reception and assign final number
4. ✅ Protocol numbering follows correct format and is sequential
5. ✅ Numbering resets annually per analysis type
6. ✅ Printable labels are generated with protocol number
7. ✅ Reception date and time are automatically recorded
8. ✅ Email notification is sent to veterinarian
9. ✅ Discrepancies can be documented and flagged
10. ✅ Sample condition is assessed and recorded
11. ✅ Multiple samples can be processed in batch mode
12. ✅ Reception history is logged and auditable

## Testing Approach

### Unit Tests
- Protocol number generation logic
- Sequential numbering enforcement
- Year rollover handling (Dec 31 → Jan 1)
- Duplicate number prevention
- Temporary code parsing and validation

### Integration Tests
- Search protocol by temporary code
- Complete reception flow with notification
- Batch reception processing
- Discrepancy reporting and handling
- Label generation (PDF)
- Counter updates after reception

### E2E Tests
- Laboratory receives sample → searches by code → confirms reception → labels print → veterinarian receives email
- Sample with discrepancy → staff reports → veterinarian notified → issue resolved → sample processed
- Batch of 10 samples received together → all processed → all notifications sent

### Edge Cases
- Protocol submitted but sample never arrives (pending queue)
- Same temporary code scanned twice (prevent duplicate reception)
- Year boundary (Dec 31 → Jan 1 numbering reset)
- Concurrent receptions (race condition on counter)
- Network failure during notification (retry mechanism)

## Technical Considerations

### 🔧 Pending Technical Decisions

1. **Label Printing**:
   - Browser-based print (HTML/CSS)
   - PDF generation with specific label dimensions
   - Integration with thermal label printers
   - QR code vs barcode

2. **QR Code Content**:
   - Just protocol number
   - Full protocol URL
   - Encrypted protocol data

3. **Email Service**:
   - Institutional SMTP
   - Third-party service (SendGrid, etc.)
   - Template engine for emails

4. **Concurrent Access**:
   - Locking mechanism for counter updates
   - Transaction isolation level
   - Retry logic on conflicts

### Performance & Reliability

**Counter Management:**
- Use database transactions for counter updates
- Implement optimistic locking to prevent race conditions
- Cache current year's counters in memory
- Periodic verification of numbering integrity

**Label Generation:**
- Pre-generate label templates
- Use efficient QR code library
- Cache common elements (logo, layout)
- Print queue for batch operations

**Email Reliability:**
- Queue system for email sending
- Retry failed sends (3 attempts)
- Log all email operations
- Alternative notification methods (SMS) if email fails

## Dependencies

### Must be completed first:
- Step 01: Authentication & User Management
- Step 02: Veterinarian Profiles
- Step 03: Protocol Submission

### Enables these steps:
- Step 05: Sample Processing (needs received samples)
- Step 06: Report Generation (needs complete workflow)

## Estimated Effort

**Time**: 1 week (Sprint 5-6)

**Breakdown**:
- Database schema updates: 0.5 days
- Protocol numbering logic: 1 day
- Backend reception API: 2 days
- Frontend reception interface: 2 days
- Label generation (PDF): 1 day
- Email notifications: 1 day
- Testing: 1.5 days

## Implementation Notes

### Development Phases
1. **Phase 1**: Basic search and reception (manual number entry)
2. **Phase 2**: Automatic protocol numbering
3. **Phase 3**: Label generation
4. **Phase 4**: Email notifications
5. **Phase 5**: Batch processing and discrepancy handling

### Label Template Example
```html
<!-- Label dimensions: 100mm x 50mm -->
<div class="label">
  <div class="header">
    <img src="lab-logo.png" class="logo">
    <h1>Laboratorio Anatomía Patológica</h1>
  </div>
  <div class="protocol-number">
    HP 24/123
  </div>
  <div class="qr-code">
    <img src="[QR_CODE_DATA_URI]">
  </div>
  <div class="details">
    <p>Animal: Luna (Felino)</p>
    <p>Recepción: 11/10/2024</p>
  </div>
</div>
```

### Testing Checklist
- [ ] Search by temporary code retrieves correct protocol
- [ ] Protocol number generated with correct format
- [ ] Numbering is sequential per type
- [ ] No duplicate protocol numbers
- [ ] Labels print correctly
- [ ] Email notifications delivered
- [ ] Batch reception processes all samples
- [ ] Discrepancies properly flagged
- [ ] Reception history accurately logged

### Sample Test Scenarios
```javascript
// Scenario 1: Normal reception
searchProtocol("TMP-HP-20241010-457")
  -> displays protocol
  -> confirm reception
  -> assigns "HP 24/123"
  -> generates labels
  -> sends email

// Scenario 2: Discrepancy
searchProtocol("TMP-HP-20241010-458")
  -> displays protocol (expects 2 jars)
  -> only 1 jar received
  -> report discrepancy
  -> notify veterinarian
  -> await resolution
```

