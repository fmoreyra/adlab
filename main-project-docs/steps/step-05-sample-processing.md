# Step 05: Sample Processing & Tracking

## Problem Statement

After sample reception, laboratory technicians process samples through multiple stages before they're ready for microscopic analysis. This includes cassette preparation, fixation, embedding, sectioning, slide mounting, and staining. Currently, tracking of these stages is done manually on paper, making it difficult to know the status of each sample, leading to lost cassettes, unclear processing history, and difficulty in maintaining sample traceability. A digital tracking system is needed to monitor each processing step and maintain complete traceability from sample to final slide.

## Requirements

### Functional Requirements (RF04, RF05)

**Histopathology Processing (RF04):**
- **RF04.1**: Register cassettes with unique identifiers
- **RF04.2**: Specify material included in each cassette
- **RF04.3**: Visual differentiation of cassettes (yellow=multi-cut, orange=special staining)
- **RF04.4**: Register slides (portaobjetos) with cassette associations
- **RF04.5**: Track processing stages: sectioning, fixation, embedding, cutting, mounting, staining
- **RF04.6**: Complete traceability: sample → cassette → slide

**Cytology Processing (RF05):**
- **RF05.1**: Simplified registration (staining only)
- **RF05.2**: Direct sample → slide association

**General:**
- Track processing timestamps for each stage
- Support multiple cassettes per protocol
- Support multiple slides per cassette
- Register processing technician
- Notes/observations per processing step

### Non-Functional Requirements

- **Traceability**: 100% - no sample can be lost in system
- **Speed**: Register cassette/slide in < 30 seconds
- **Accuracy**: No mislabeling or mix-ups between samples
- **Real-time**: Status updates visible immediately

## Data Model

### Cassette Table
```sql
cassette (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  muestra_histopatologia_id: INTEGER NOT NULL,
  codigo_cassette: VARCHAR(50) UNIQUE NOT NULL, -- e.g., "HP 24/123-C1"
  material_incluido: TEXT NOT NULL, -- Description of tissue in cassette
  tipo_cassette: ENUM('normal', 'multicorte', 'coloracion_especial') DEFAULT 'normal',
  color_cassette: ENUM('blanco', 'amarillo', 'naranja') DEFAULT 'blanco',
  
  -- Processing stages
  fecha_encasetado: DATETIME,
  fecha_fijacion: DATETIME,
  fecha_inclusion: DATETIME,
  fecha_entacado: DATETIME,
  
  -- Status
  estado: ENUM('pendiente', 'en_proceso', 'completado') DEFAULT 'pendiente',
  observaciones: TEXT,
  
  created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  FOREIGN KEY (muestra_histopatologia_id) REFERENCES muestra_histopatologia(id) ON DELETE CASCADE
)
```

### Portaobjetos (Slide) Table
```sql
portaobjetos (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  protocolo_id: INTEGER NOT NULL,
  codigo_portaobjetos: VARCHAR(50) UNIQUE NOT NULL, -- e.g., "HP 24/123-S1"
  
  -- For cytology (direct link to sample)
  muestra_citologia_id: INTEGER,
  
  -- Processing info
  campo: INTEGER, -- Slide number/field
  tecnica_coloracion: VARCHAR(200) DEFAULT 'Hematoxilina-Eosina',
  fecha_montaje: DATETIME,
  fecha_coloracion: DATETIME,
  calidad: ENUM('excelente', 'buena', 'aceptable', 'deficiente'),
  
  -- Status
  estado: ENUM('pendiente', 'montado', 'coloreado', 'listo') DEFAULT 'pendiente',
  observaciones: TEXT,
  
  created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  FOREIGN KEY (protocolo_id) REFERENCES protocolo(id) ON DELETE CASCADE,
  FOREIGN KEY (muestra_citologia_id) REFERENCES muestra_citologia(id) ON DELETE CASCADE
)
```

### Cassette_Portaobjetos Junction Table (M:N relationship)
```sql
cassette_portaobjetos (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  cassette_id: INTEGER NOT NULL,
  portaobjetos_id: INTEGER NOT NULL,
  posicion: ENUM('superior', 'inferior', 'completo'), -- Position on slide
  coloracion: VARCHAR(200), -- Specific staining for this cassette on this slide
  requiere_multicorte: BOOLEAN DEFAULT FALSE,
  observaciones: TEXT,
  created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY (cassette_id) REFERENCES cassette(id) ON DELETE CASCADE,
  FOREIGN KEY (portaobjetos_id) REFERENCES portaobjetos(id) ON DELETE CASCADE,
  UNIQUE KEY (cassette_id, portaobjetos_id)
)
```

### Processing Log Table
```sql
procesamiento_log (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  protocolo_id: INTEGER NOT NULL,
  cassette_id: INTEGER,
  portaobjetos_id: INTEGER,
  etapa: VARCHAR(100) NOT NULL, -- 'encasetado', 'fijacion', 'corte', 'montaje', 'coloracion'
  usuario_id: INTEGER NOT NULL,
  fecha_inicio: DATETIME NOT NULL,
  fecha_fin: DATETIME,
  observaciones: TEXT,
  created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY (protocolo_id) REFERENCES protocolo(id),
  FOREIGN KEY (cassette_id) REFERENCES cassette(id),
  FOREIGN KEY (portaobjetos_id) REFERENCES portaobjetos(id),
  FOREIGN KEY (usuario_id) REFERENCES users(id)
)
```

## API Design

### Processing Endpoints

#### POST /api/processing/cassettes
Register new cassettes for a protocol.

**Request:**
```json
{
  "muestra_histopatologia_id": 123,
  "cassettes": [
    {
      "material_incluido": "Fragmento de hígado con lesión nodular",
      "tipo_cassette": "normal",
      "color_cassette": "blanco"
    },
    {
      "material_incluido": "Fragmento de bazo",
      "tipo_cassette": "multicorte",
      "color_cassette": "amarillo"
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "cassettes": [
    {
      "id": 456,
      "codigo_cassette": "HP 24/123-C1",
      "material_incluido": "Fragmento de hígado con lesión nodular"
    },
    {
      "id": 457,
      "codigo_cassette": "HP 24/123-C2",
      "material_incluido": "Fragmento de bazo"
    }
  ]
}
```

#### PUT /api/processing/cassettes/:id/stage
Update cassette processing stage.

**Request:**
```json
{
  "etapa": "fijacion",
  "observaciones": "Iniciada fijación en formol 10%"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "cassette": {
    "id": 456,
    "codigo_cassette": "HP 24/123-C1",
    "estado": "en_proceso",
    "fecha_fijacion": "2024-10-12T10:00:00Z"
  }
}
```

#### POST /api/processing/slides
Register new slides.

**Request:**
```json
{
  "protocolo_id": 123,
  "tipo": "histopatologia",
  "slides": [
    {
      "cassettes": [456, 457], -- Two cassettes on one slide
      "tecnica_coloracion": "Hematoxilina-Eosina",
      "campo": 1
    },
    {
      "cassettes": [456], -- Same cassette, different staining
      "tecnica_coloracion": "PAS",
      "campo": 2
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "slides": [
    {
      "id": 789,
      "codigo_portaobjetos": "HP 24/123-S1",
      "cassettes": ["HP 24/123-C1", "HP 24/123-C2"],
      "tecnica_coloracion": "Hematoxilina-Eosina"
    },
    {
      "id": 790,
      "codigo_portaobjetos": "HP 24/123-S2",
      "cassettes": ["HP 24/123-C1"],
      "tecnica_coloracion": "PAS"
    }
  ]
}
```

#### POST /api/processing/slides/cytology
Register cytology slides (simplified).

**Request:**
```json
{
  "muestra_citologia_id": 124,
  "numero_slides": 2,
  "tecnica_coloracion": "Diff-Quick"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "slides": [
    {
      "id": 791,
      "codigo_portaobjetos": "CT 24/089-S1"
    },
    {
      "id": 792,
      "codigo_portaobjetos": "CT 24/089-S2"
    }
  ]
}
```

#### GET /api/processing/protocol/:id/status
Get complete processing status for a protocol.

**Response (200 OK):**
```json
{
  "protocolo": {
    "numero": "HP 24/123",
    "tipo": "histopatologia",
    "estado": "procesando"
  },
  "cassettes": [
    {
      "codigo": "HP 24/123-C1",
      "material": "Fragmento de hígado con lesión nodular",
      "estado": "completado",
      "timeline": [
        {"etapa": "encasetado", "fecha": "2024-10-11T14:00:00Z"},
        {"etapa": "fijacion", "fecha": "2024-10-12T10:00:00Z"},
        {"etapa": "inclusion", "fecha": "2024-10-13T09:00:00Z"},
        {"etapa": "entacado", "fecha": "2024-10-13T15:00:00Z"}
      ]
    }
  ],
  "slides": [
    {
      "codigo": "HP 24/123-S1",
      "cassettes": ["HP 24/123-C1", "HP 24/123-C2"],
      "tecnica": "Hematoxilina-Eosina",
      "estado": "listo",
      "calidad": "excelente"
    }
  ]
}
```

#### GET /api/processing/queue
Get processing queue (samples pending processing).

**Query Parameters:**
- `etapa`: Filter by stage (encasetado, fijacion, corte, etc.)
- `tipo`: Filter by type (citologia, histopatologia)

**Response (200 OK):**
```json
{
  "queue": [
    {
      "protocolo_numero": "HP 24/124",
      "animal": "Rex - Canino",
      "fecha_recepcion": "2024-10-13",
      "etapa_actual": "pendiente_encasetado",
      "prioridad": "normal"
    }
  ],
  "total": 12
}
```

#### PUT /api/processing/slides/:id/quality
Assess slide quality.

**Request:**
```json
{
  "calidad": "excelente",
  "observaciones": "Corte uniforme, coloración óptima"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "slide": {
    "codigo": "HP 24/123-S1",
    "calidad": "excelente"
  }
}
```

## Business Logic

### Cassette Coding Logic
```javascript
function generateCassetteCode(protocolNumber, cassette Number) {
  // protocolNumber: "HP 24/123"
  // cassetteNumber: 1, 2, 3, ...
  return `${protocolNumber}-C${cassetteNumber}`;
}
// Examples:
// "HP 24/123-C1", "HP 24/123-C2", ...
```

### Slide Coding Logic
```javascript
function generateSlideCode(protocolNumber, slideNumber) {
  // protocolNumber: "HP 24/123" or "CT 24/089"
  // slideNumber: 1, 2, 3, ...
  return `${protocolNumber}-S${slideNumber}`;
}
// Examples:
// "HP 24/123-S1", "HP 24/123-S2", ...
// "CT 24/089-S1", "CT 24/089-S2", ...
```

### Cassette Color Rules
- **White (Blanco)**: Normal cassettes - standard processing
- **Yellow (Amarillo)**: Multi-cut required - multiple sections needed
- **Orange (Naranja)**: Special staining required - immunohistochemistry, special techniques

### Processing Workflow

**Histopathology Standard Workflow:**
1. **Encasetado** (Cassetting): Place tissue fragments in cassettes
2. **Fijación** (Fixation): Immerse in fixative (formol, alcohols, xylol)
3. **Inclusión** (Embedding): Immerse in liquid paraffin
4. **Entacado** (Blocking): Create paraffin blocks
5. **Corte** (Sectioning): Cut thin sections with microtome
6. **Montaje** (Mounting): Mount sections on slides
7. **Coloración** (Staining): Apply staining technique

**Cytology Simplified Workflow:**
1. **Coloración** (Staining): Apply cytological stain (Diff-Quick, Papanicolau, etc.)
2. Ready for analysis

### Multiple Cassettes on One Slide
- Common practice to save resources
- Typically 2 cassettes per slide
- Each cassette occupies a defined position (superior/inferior)
- Clear labeling of which cassettes are on which slide

### Special Processing Notes
- **Small samples**: Require special handling (see document section III.4)
- **Multicorte**: Same cassette cut multiple times for different staining
- **Special stains**: PAS, Masson, Reticulin, Immunohistochemistry, etc.

## Acceptance Criteria

1. ✅ Technicians can register cassettes for received samples
2. ✅ Cassette codes are generated automatically
3. ✅ Material included is documented for each cassette
4. ✅ Cassette color differentiation is supported
5. ✅ Processing stages can be updated and timestamped
6. ✅ Slides can be created with cassette associations
7. ✅ Multiple cassettes can be mounted on one slide
8. ✅ Slide codes are generated automatically
9. ✅ Complete processing timeline is visible
10. ✅ Cytology samples have simplified workflow
11. ✅ Processing queue shows pending samples
12. ✅ Complete traceability maintained: sample → cassette → slide

## Testing Approach

### Unit Tests
- Cassette code generation
- Slide code generation
- Sequential numbering per protocol
- Timeline calculation
- State transition validation

### Integration Tests
- Complete histopathology processing workflow
- Complete cytology processing workflow
- Multiple cassettes per protocol
- Multiple slides per cassette
- Processing queue updates
- Status tracking accuracy

### E2E Tests
- Sample received → cassettes created → processing stages updated → slides mounted → ready for analysis
- Cytology sample → slides created → stained → ready for analysis
- Multiple cassettes → mounted on one slide → tracked separately

### Traceability Tests
- Given slide code → trace back to cassette → trace back to sample → trace back to protocol
- Given protocol → list all cassettes → list all slides
- Verify no orphaned cassettes or slides
- Verify all processing steps logged

## Technical Considerations

### 🔧 Pending Technical Decisions

1. **Barcode/QR Code Integration**:
   - Print QR codes on cassette labels
   - Print QR codes on slide labels
   - Mobile scanning app for quick updates
   - Barcode scanner integration

2. **Batch Processing**:
   - Process multiple cassettes together
   - Group by processing stage
   - Batch status updates

3. **Image Capture**:
   - Photograph cassettes before embedding
   - Photograph slides after staining
   - Integration with microscope camera

### Performance Optimization
- Index on `codigo_cassette` and `codigo_portaobjetos`
- Index on `protocolo_id` for quick lookups
- Cache processing queue queries
- Efficient joins for traceability queries

### Data Integrity
- Foreign key constraints prevent orphaned records
- Cascade deletes maintain referential integrity
- Transactions for cassette-slide associations
- Audit log for all processing changes

## Dependencies

### Must be completed first:
- Step 01: Authentication & User Management
- Step 03: Protocol Submission
- Step 04: Sample Reception

### Enables these steps:
- Step 06: Report Generation (needs processed slides)

## Estimated Effort

**Time**: 1 week (Sprint 7-8)

**Breakdown**:
- Database schema: 1 day
- Backend API for cassettes: 2 days
- Backend API for slides: 1 day
- Frontend processing interface: 2 days
- Timeline/traceability views: 1 day
- Testing: 1 day

## Implementation Notes

### Development Phases
1. **Phase 1**: Cassette registration and coding
2. **Phase 2**: Processing stage tracking
3. **Phase 3**: Slide registration and cassette association
4. **Phase 4**: Cytology simplified workflow
5. **Phase 5**: Processing queue and timeline views

### Testing Checklist
- [ ] Create cassettes for histopathology sample
- [ ] Update processing stages with timestamps
- [ ] Create slides with multiple cassettes
- [ ] Create cytology slides (simplified)
- [ ] View complete processing timeline
- [ ] Trace slide back to original sample
- [ ] Processing queue displays pending samples
- [ ] No orphaned cassettes or slides

### Sample Test Data
```json
{
  "histopathology_cassettes": [
    {
      "material_incluido": "Hígado: Fragmento con nódulo blanquecino de 2cm",
      "tipo": "normal",
      "color": "blanco"
    },
    {
      "material_incluido": "Hígado: Tejido perilesional",
      "tipo": "multicorte",
      "color": "amarillo"
    },
    {
      "material_incluido": "Bazo: Fragmento de 1.5cm",
      "tipo": "normal",
      "color": "blanco"
    }
  ],
  "slides": [
    {
      "cassettes": [1, 3],
      "tecnica": "Hematoxilina-Eosina",
      "campo": 1
    },
    {
      "cassettes": [2],
      "tecnica": "PAS",
      "campo": 2
    }
  ]
}
```

