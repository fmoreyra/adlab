# Step 03: Protocol Submission

## Problem Statement

Veterinarians currently submit physical paper protocols along with samples, leading to inefficiencies, data entry errors, incomplete information, and delays in sample processing. The laboratory needs a digital system that allows veterinarians to submit protocol information online before or during sample shipment, ensuring all required data is captured upfront and enabling better tracking and communication throughout the sample analysis process.

## Requirements

### Functional Requirements (RF02)

- **RF02.1**: Differentiated forms for cytology and histopathology analyses
- **RF02.2**: Validation of all required fields according to analysis type
- **RF02.3**: Generation of temporary tracking code pre-reception
- **RF02.4**: Automatic protocol numbering upon sample reception (format "HP AA/NRO" or "CT AA/NRO")
- **RF02.5**: Storage of animal patient data without creating separate entity (design decision IV.3.3)
- Support for multiple samples from same animal (each gets unique protocol)
- Draft saving capability for incomplete protocols
- Protocol history and status tracking

### Non-Functional Requirements

- **Usability**: Form completion in < 5 minutes
- **Validation**: Real-time field validation
- **Data Integrity**: All required clinical information captured
- **Accessibility**: Form accessible from mobile devices

## Data Model

### Protocolo Table
```sql
protocolo (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  codigo_temporal: VARCHAR(50) UNIQUE, -- Pre-reception tracking code
  numero_protocolo: VARCHAR(50) UNIQUE, -- Final: HP 24/001 or CT 24/001
  tipo_analisis: ENUM('citologia', 'histopatologia') NOT NULL,
  veterinario_id: INTEGER NOT NULL,
  orden_trabajo_id: INTEGER,
  
  -- Animal/Patient data (no separate entity)
  especie: VARCHAR(100) NOT NULL,
  raza: VARCHAR(100),
  sexo: ENUM('macho', 'hembra', 'indeterminado'),
  edad: VARCHAR(50), -- "2 años", "6 meses", etc.
  identificacion_animal: VARCHAR(200), -- Name, tag number, etc.
  apellido_propietario: VARCHAR(100),
  nombre_propietario: VARCHAR(100),
  
  -- Clinical information
  diagnostico_presuntivo: TEXT NOT NULL,
  historia_clinica: TEXT,
  interes_academico: BOOLEAN DEFAULT FALSE,
  
  -- Dates and status
  fecha_remision: DATE NOT NULL,
  fecha_recepcion: DATE,
  estado: ENUM('borrador', 'enviado', 'recibido', 'procesando', 'listo', 'enviado_informe') 
         DEFAULT 'borrador',
  
  -- Metadata
  created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  FOREIGN KEY (veterinario_id) REFERENCES veterinario(id),
  FOREIGN KEY (orden_trabajo_id) REFERENCES orden_trabajo(id)
)
```

### Muestra_Citologia Table
```sql
muestra_citologia (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  protocolo_id: INTEGER NOT NULL,
  veterinario_id: INTEGER NOT NULL,
  tecnica_utilizada: VARCHAR(200) NOT NULL, -- Punción, hisopado, raspado, etc.
  sitio_muestreo: VARCHAR(200) NOT NULL, -- Anatomical location
  numero_portaobjetos: INTEGER DEFAULT 1,
  observaciones: TEXT,
  fecha_recepcion: DATE,
  created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (protocolo_id) REFERENCES protocolo(id) ON DELETE CASCADE,
  FOREIGN KEY (veterinario_id) REFERENCES veterinario(id)
)
```

### Muestra_Histopatologia Table
```sql
muestra_histopatologia (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  protocolo_id: INTEGER NOT NULL,
  veterinario_id: INTEGER NOT NULL,
  material_remitido: TEXT NOT NULL, -- Description of tissue/organ samples
  numero_frascos: INTEGER DEFAULT 1,
  conservacion: VARCHAR(100) DEFAULT 'Formol 10%',
  observaciones: TEXT,
  fecha_recepcion: DATE,
  created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (protocolo_id) REFERENCES protocolo(id) ON DELETE CASCADE,
  FOREIGN KEY (veterinario_id) REFERENCES veterinario(id)
)
```

## API Design

### Protocol Submission Endpoints

#### POST /api/protocols/cytology
Submit new cytology protocol.

**Request:**
```json
{
  "especie": "Canino",
  "raza": "Labrador",
  "sexo": "macho",
  "edad": "5 años",
  "identificacion_animal": "Max",
  "apellido_propietario": "García",
  "nombre_propietario": "Ana",
  "diagnostico_presuntivo": "Sospecha de linfoma",
  "historia_clinica": "Presenta linfoadenopatía generalizada",
  "interes_academico": false,
  "muestra": {
    "tecnica_utilizada": "Punción aspiración con aguja fina (PAAF)",
    "sitio_muestreo": "Linfonódulo submandibular izquierdo",
    "numero_portaobjetos": 2,
    "observaciones": "Se enviaron 2 láminas con extendido directo"
  }
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Protocolo de citología creado exitosamente",
  "protocolo": {
    "id": 456,
    "codigo_temporal": "TMP-CT-20241010-456",
    "tipo_analisis": "citologia",
    "estado": "enviado",
    "fecha_remision": "2024-10-10",
    "instrucciones": "Envíe la muestra al laboratorio con el código: TMP-CT-20241010-456"
  }
}
```

#### POST /api/protocols/histopathology
Submit new histopathology protocol.

**Request:**
```json
{
  "especie": "Felino",
  "raza": "Mestizo",
  "sexo": "hembra",
  "edad": "8 años",
  "identificacion_animal": "Luna",
  "apellido_propietario": "Rodríguez",
  "nombre_propietario": "Carlos",
  "diagnostico_presuntivo": "Tumor mamario",
  "historia_clinica": "Masa en cadena mamaria, Qx resección",
  "interes_academico": true,
  "muestra": {
    "material_remitido": "Masa de 3x2cm de cadena mamaria izquierda",
    "numero_frascos": 1,
    "conservacion": "Formol 10%",
    "observaciones": "Muestra completa en un frasco"
  }
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Protocolo de histopatología creado exitosamente",
  "protocolo": {
    "id": 457,
    "codigo_temporal": "TMP-HP-20241010-457",
    "tipo_analisis": "histopatologia",
    "estado": "enviado",
    "fecha_remision": "2024-10-10"
  }
}
```

#### GET /api/protocols/my-protocols
Get list of protocols submitted by current veterinarian.

**Query Parameters:**
- `status`: Filter by status
- `tipo`: Filter by analysis type (citologia/histopatologia)
- `desde`: Date from (YYYY-MM-DD)
- `hasta`: Date to (YYYY-MM-DD)
- `page`: Page number
- `limit`: Results per page

**Response (200 OK):**
```json
{
  "protocols": [
    {
      "id": 457,
      "codigo_temporal": "TMP-HP-20241010-457",
      "numero_protocolo": null,
      "tipo_analisis": "histopatologia",
      "identificacion_animal": "Luna",
      "especie": "Felino",
      "diagnostico_presuntivo": "Tumor mamario",
      "estado": "enviado",
      "fecha_remision": "2024-10-10",
      "fecha_recepcion": null
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 3,
    "total_records": 45
  }
}
```

#### GET /api/protocols/:id
Get specific protocol details.

**Response (200 OK):**
```json
{
  "protocolo": {
    "id": 457,
    "codigo_temporal": "TMP-HP-20241010-457",
    "numero_protocolo": "HP 24/123",
    "tipo_analisis": "histopatologia",
    "estado": "procesando",
    "especie": "Felino",
    "raza": "Mestizo",
    "sexo": "hembra",
    "edad": "8 años",
    "identificacion_animal": "Luna",
    "propietario": "Carlos Rodríguez",
    "diagnostico_presuntivo": "Tumor mamario",
    "historia_clinica": "Masa en cadena mamaria, Qx resección",
    "fecha_remision": "2024-10-10",
    "fecha_recepcion": "2024-10-11",
    "muestra": {
      "material_remitido": "Masa de 3x2cm de cadena mamaria izquierda",
      "numero_frascos": 1,
      "conservacion": "Formol 10%"
    },
    "timeline": [
      {
        "estado": "enviado",
        "fecha": "2024-10-10T14:30:00Z",
        "descripcion": "Protocolo enviado por veterinario"
      },
      {
        "estado": "recibido",
        "fecha": "2024-10-11T09:15:00Z",
        "descripcion": "Muestra recibida en laboratorio"
      },
      {
        "estado": "procesando",
        "fecha": "2024-10-11T10:00:00Z",
        "descripcion": "Iniciado procesamiento de muestra"
      }
    ]
  }
}
```

#### PUT /api/protocols/:id (Only for drafts)
Update draft protocol.

**Request:** Same as create
**Response (200 OK):** Updated protocol data

#### DELETE /api/protocols/:id (Only for drafts)
Delete draft protocol.

**Response (204 No Content)**

#### POST /api/protocols/:id/submit
Submit a draft protocol.

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Protocolo enviado exitosamente",
  "codigo_temporal": "TMP-HP-20241010-457"
}
```

## Business Logic

### Temporary Code Generation
- Format: `TMP-{TYPE}-{YYYYMMDD}-{ID}`
- Examples:
  - `TMP-CT-20241010-456` (Cytology)
  - `TMP-HP-20241010-457` (Histopathology)
- Unique per protocol
- Used for tracking before sample reception
- Veterinarian prints/writes this code on sample label

### Protocol Numbering (Upon Reception)
- Format: `{TYPE} {YY}/{NRO}`
- Examples:
  - `CT 24/001` (First cytology of 2024)
  - `HP 24/123` (123rd histopathology of 2024)
- Sequential numbering per year and type
- Numbering resets each year
- Assigned when laboratory receives physical sample

### Field Validations

**Cytology Required Fields:**
- Especie, identificacion_animal
- Diagnóstico presuntivo
- Técnica utilizada, sitio de muestreo

**Histopathology Required Fields:**
- Especie, identificacion_animal
- Diagnóstico presuntivo
- Material remitido

**Optional Fields:**
- Raza, sexo, edad
- Apellido/nombre propietario
- Historia clínica
- Observaciones

### Draft vs Submitted States
- **Borrador**: Can be edited/deleted by veterinarian
- **Enviado**: Locked for editing, awaiting sample reception
- **Recibido**: Sample received, protocol assigned final number
- **Procesando**: Sample in processing stages
- **Listo**: Ready for diagnosis
- **Enviado_informe**: Report sent to veterinarian

### Multiple Samples per Animal
- Each analysis gets separate protocol
- Example: Same dog, two different masses → 2 histopathology protocols
- Protocols can reference each other (future feature)

## Acceptance Criteria

1. ✅ Veterinarians can submit cytology protocols with all required fields
2. ✅ Veterinarians can submit histopathology protocols with all required fields
3. ✅ System validates all required fields before submission
4. ✅ Temporary tracking code is generated upon submission
5. ✅ Veterinarians receive confirmation with tracking code
6. ✅ Protocols can be saved as drafts
7. ✅ Draft protocols can be edited and deleted
8. ✅ Submitted protocols cannot be edited by veterinarian
9. ✅ Veterinarians can view list of their protocols
10. ✅ Protocols can be filtered by status, type, and date
11. ✅ Protocol details include complete timeline/history
12. ✅ System enforces one protocol per sample rule

## Testing Approach

### Unit Tests
- Temporary code generation uniqueness
- Protocol numbering logic
- Field validation rules (required/optional)
- State transition validation
- Species/breed validation

### Integration Tests
- Complete protocol submission flow (draft → submit)
- Protocol listing with filters
- Protocol detail retrieval
- Status update workflow
- Veterinarian can only access own protocols

### E2E Tests
- Veterinarian logs in → creates cytology protocol → submits → receives code
- Veterinarian creates histopathology protocol → saves draft → edits → submits
- Veterinarian views protocol list → filters by date → views details
- Veterinarian submits protocol → laboratory receives sample → sees status update

### Validation Tests
- Submit with missing required fields → error
- Submit with invalid species → error
- Edit submitted protocol → error
- Delete submitted protocol → error
- Non-owner access protocol → forbidden

## Technical Considerations

### 🔧 Pending Technical Decisions

1. **Species/Breed Lists**:
   - Use predefined dropdown lists
   - Allow free text entry
   - Combination (dropdown + "Other" option)

2. **File Attachments** (future):
   - Allow attaching clinical images
   - Pre-operative photos
   - Previous analysis results

3. **Auto-save Functionality**:
   - Auto-save drafts every N seconds
   - Local storage backup
   - Warning on navigate away

### Performance Optimization
- Index on `codigo_temporal` for quick lookup
- Index on `veterinario_id` + `fecha_remision` for listing
- Paginate protocol lists
- Cache species/breed lists

### Data Validation
```javascript
const ESPECIES_VALIDAS = [
  'Canino', 'Felino', 'Bovino', 'Equino', 
  'Ovino', 'Caprino', 'Porcino', 'Aviar', 'Otro'
];

const SEXO_VALIDO = ['macho', 'hembra', 'indeterminado'];

const TECNICAS_CITOLOGIA = [
  'Punción aspiración con aguja fina (PAAF)',
  'Hisopado',
  'Raspado',
  'Impronta',
  'Lavado',
  'Otro'
];
```

## Dependencies

### Must be completed first:
- Step 01: Authentication & User Management
- Step 02: Veterinarian Profiles

### Enables these steps:
- Step 04: Sample Reception (needs protocols to receive)
- Step 05: Sample Processing (needs received samples)

## Estimated Effort

**Time**: 1-1.5 weeks (Sprint 3-4)

**Breakdown**:
- Database schema: 0.5 days
- Backend API implementation: 3 days
- Frontend forms (cytology + histopathology): 3 days
- Validation logic: 1 day
- Draft functionality: 1 day
- Protocol listing/filtering: 1 day
- Testing: 2 days

## Implementation Notes

### Development Phases
1. **Phase 1**: Basic protocol creation (histopathology)
2. **Phase 2**: Cytology protocol support
3. **Phase 3**: Draft save/edit/delete functionality
4. **Phase 4**: Protocol listing and filtering
5. **Phase 5**: Timeline/status tracking

### Form Design Considerations
- Progressive disclosure: Show relevant fields based on analysis type
- Smart defaults: Pre-fill based on previous submissions
- Validation feedback: Real-time, inline validation
- Mobile-friendly: Forms work on tablets/phones
- Help text: Explain clinical terminology

### Testing Checklist
- [ ] Create cytology protocol with all required fields
- [ ] Create histopathology protocol with all required fields
- [ ] Validation prevents submission with missing fields
- [ ] Temporary code generated and unique
- [ ] Draft save/edit/delete functionality
- [ ] Protocol listing with filters
- [ ] Status updates visible to veterinarian
- [ ] Access control (veterinarian sees only own protocols)

### Sample Test Data
```json
{
  "cytology": {
    "especie": "Canino",
    "raza": "Golden Retriever",
    "sexo": "hembra",
    "edad": "7 años",
    "identificacion_animal": "Bella",
    "diagnostico_presuntivo": "Mastocitoma",
    "tecnica_utilizada": "PAAF",
    "sitio_muestreo": "Masa subcutánea en flanco derecho"
  },
  "histopathology": {
    "especie": "Bovino",
    "raza": "Holando",
    "sexo": "hembra",
    "edad": "4 años",
    "identificacion_animal": "Caravana 1234",
    "diagnostico_presuntivo": "Neoplasia hepática",
    "material_remitido": "Fragmento de hígado de 5x3x2 cm con masa nodular blanquecina"
  }
}
```

