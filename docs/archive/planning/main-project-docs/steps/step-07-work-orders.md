# Step 07: Work Order (OT) Management

## Problem Statement

The laboratory needs to generate Work Orders (Órdenes de Trabajo) that detail the services provided and amounts to be charged. These are sent to the Finance office for billing. Currently, OTs are created manually alongside reports, leading to duplication of effort and potential errors in pricing or service descriptions. The system should automatically generate OTs based on the services provided, with correct pricing, and allow grouping of multiple protocols when appropriate.

## Requirements

### Functional Requirements (RF08)

- **RF08.1**: Automatic calculation of amounts based on services
- **RF08.2**: Recording of advance payments received with sample
- **RF08.3**: Grouping multiple protocols into single OT (when from same veterinarian, same day, no special billing notes)
- **RF08.4**: Exclusion of Hospital de Salud Animal protocols (they have separate billing)
- **RF08.5**: PDF generation with Finance-required format
- Maintain pricing catalog
- Support for discounts/promotions
- Track payment status

### Non-Functional Requirements

- **Accuracy**: 100% - no pricing errors
- **Compliance**: Format must meet Finance office requirements
- **Audit**: Complete payment tracking

## Data Model

### Orden_Trabajo Table
```sql
orden_trabajo (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  numero_ot: VARCHAR(50) UNIQUE NOT NULL, -- e.g., "OT-2024-001"
  fecha_emision: DATE NOT NULL,
  veterinario_id: INTEGER NOT NULL,
  
  -- Financial
  monto_total: DECIMAL(10,2) NOT NULL,
  pago_adelantado: DECIMAL(10,2) DEFAULT 0,
  saldo_pendiente: DECIMAL(10,2) NOT NULL,
  estado_pago: ENUM('pendiente', 'pagado_parcial', 'pagado_completo') DEFAULT 'pendiente',
  
  -- Billing details
  nombre_facturacion: VARCHAR(200), -- If different from veterinarian name
  cuit_cuil: VARCHAR(20),
  condicion_iva: ENUM('responsable_inscripto', 'monotributista', 'exento'),
  
  -- Files
  pdf_path: VARCHAR(500),
  
  -- Status
  estado: ENUM('borrador', 'emitida', 'enviada', 'facturada') DEFAULT 'borrador',
  fecha_envio: DATETIME,
  fecha_facturacion: DATETIME,
  
  observaciones: TEXT,
  created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  FOREIGN KEY (veterinario_id) REFERENCES veterinario(id)
)
```

### OT_Servicios Table (line items)
```sql
ot_servicios (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  orden_trabajo_id: INTEGER NOT NULL,
  protocolo_id: INTEGER NOT NULL,
  
  descripcion: VARCHAR(500) NOT NULL,
  tipo_servicio: VARCHAR(100) NOT NULL, -- 'histopatologia', 'citologia', etc.
  cantidad: INTEGER DEFAULT 1,
  precio_unitario: DECIMAL(10,2) NOT NULL,
  subtotal: DECIMAL(10,2) NOT NULL,
  descuento: DECIMAL(10,2) DEFAULT 0,
  
  FOREIGN KEY (orden_trabajo_id) REFERENCES orden_trabajo(id) ON DELETE CASCADE,
  FOREIGN KEY (protocolo_id) REFERENCES protocolo(id)
)
```

### Catalogo_Precios Table
```sql
catalogo_precios (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  tipo_servicio: VARCHAR(100) UNIQUE NOT NULL,
  descripcion: VARCHAR(500) NOT NULL,
  precio: DECIMAL(10,2) NOT NULL,
  vigente_desde: DATE NOT NULL,
  vigente_hasta: DATE,
  observaciones: TEXT,
  created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
```

## API Design

### Work Order Endpoints

#### GET /api/work-orders/pricing
Get current pricing catalog.

**Response (200 OK):**
```json
{
  "precios": [
    {
      "tipo_servicio": "histopatologia_2a5_piezas",
      "descripcion": "Análisis histopatológico (2-5 piezas)",
      "precio": 14.04
    },
    {
      "tipo_servicio": "citologia",
      "descripcion": "Análisis citopatológico",
      "precio": 5.40
    }
  ]
}
```

#### POST /api/work-orders/calculate
Calculate OT for given protocols.

**Request:**
```json
{
  "protocolo_ids": [123, 124],
  "descuento_porcentaje": 0
}
```

**Response (200 OK):**
```json
{
  "servicios": [
    {
      "protocolo_id": 123,
      "protocolo_numero": "HP 24/123",
      "descripcion": "Histopatología - Luna (Felino)",
      "tipo_servicio": "histopatologia_2a5_piezas",
      "cantidad": 1,
      "precio_unitario": 14.04,
      "subtotal": 14.04
    }
  ],
  "subtotal": 14.04,
  "descuento": 0,
  "total": 14.04
}
```

#### POST /api/work-orders
Create new work order.

**Request:**
```json
{
  "veterinario_id": 123,
  "protocolo_ids": [123],
  "pago_adelantado": 0,
  "nombre_facturacion": "Carlos Rodríguez",
  "cuit_cuil": "20-12345678-9",
  "condicion_iva": "responsable_inscripto",
  "observaciones": ""
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "orden_trabajo": {
    "id": 456,
    "numero_ot": "OT-2024-123",
    "monto_total": 14.04,
    "estado": "emitida",
    "pdf_url": "/api/work-orders/456/pdf"
  }
}
```

#### GET /api/work-orders/:id/pdf
Download OT PDF.

**Response:** PDF file

#### POST /api/work-orders/:id/send
Send OT to Finance office (and optionally to veterinarian).

**Request:**
```json
{
  "enviar_a_veterinario": true,
  "email_finanzas": "finanzas@veterinaria.unl.edu.ar"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "enviado_a": ["finanzas@veterinaria.unl.edu.ar", "vet@example.com"]
}
```

## Business Logic

### Pricing Rules

**Base Prices (from document Figure 6.4):**
- Histopathology (2-5 pieces): $14.04 USD
- Cytology: $5.40 USD
- Additional services priced separately

**Quantity Calculation:**
- 1 protocol = 1 service line item
- Exception: If multiple analyses from same sample, may combine

### Grouping Logic

**Can group into single OT when:**
- Same veterinarian
- Submitted on same date
- No special billing instructions per protocol
- Not from Hospital de Salud Animal

**Cannot group when:**
- Different veterinarians
- Different dates
- Special billing notes on any protocol
- HSA protocols (use their own billing system)

### OT Numbering

Format: `OT-YYYY-NNN`
- Sequential per year
- Examples: `OT-2024-001`, `OT-2024-002`

### Payment Tracking

- **Pendiente**: No payment received
- **Pagado Parcial**: Advance payment < total
- **Pagado Completo**: Full payment received

Advance payments are recorded when sample arrives with cash/check.

## Acceptance Criteria

1. ✅ System calculates service costs from pricing catalog
2. ✅ OT includes all protocol details
3. ✅ Multiple protocols can be grouped into one OT
4. ✅ HSA protocols excluded from OT generation
5. ✅ Advance payments are recorded and subtracted
6. ✅ PDF generated with Finance-required format
7. ✅ OT numbers are sequential and unique
8. ✅ Payment status is tracked
9. ✅ OTs can be sent to Finance office
10. ✅ Pricing catalog is maintainable

## Testing Approach

### Unit Tests
- Price calculation logic
- Grouping eligibility rules
- OT number generation
- Payment status calculation

### Integration Tests
- Create OT for single protocol
- Create OT for multiple grouped protocols
- HSA protocol exclusion
- PDF generation

### E2E Tests
- Complete flow: protocol → report → OT → send to Finance
- Advance payment recording and balance calculation
- Grouped OT with multiple protocols

## Technical Considerations

### 🔧 Pending Technical Decisions

1. **PDF Template**: Finance office format requirements
2. **Integration with Finance System**: API or manual process?
3. **Payment Tracking**: Link to actual payment system?

## Dependencies

### Must be completed first:
- Step 03: Protocol Submission
- Step 06: Report Generation (often sent together)

### Estimated Effort

**Time**: 0.5 week (part of Sprint 9-10)

**Breakdown**:
- Database schema: 0.5 days
- Pricing catalog: 0.5 days
- OT generation API: 1 day
- PDF generation: 1 day
- Testing: 0.5 days

## Implementation Notes

### OT PDF Template Structure
```
ORDEN DE TRABAJO N° OT-2024-123
Fecha: 15/10/2024

Cliente: Dr. Carlos Rodríguez
CUIT/CUIL: 20-12345678-9
Condición IVA: Responsable Inscrito

SERVICIOS:
Protocolo HP 24/123 - Histopatología (Luna - Felino)  $14.04

SUBTOTAL:                                              $14.04
PAGO ADELANTADO:                                       $0.00
SALDO PENDIENTE:                                       $14.04
```

