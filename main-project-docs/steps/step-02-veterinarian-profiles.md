# Step 02: Veterinarian Registration & Profiles

## Problem Statement

Veterinarians need to maintain complete and accurate profile information in the system to enable proper identification, communication, and billing. The current system lacks structured veterinarian data, leading to inconsistencies in contact information, difficulty in tracking client history, and problems with invoicing. A comprehensive profile system is needed to store veterinarian credentials, contact details, address information, and maintain a complete history of their interactions with the laboratory.

## Requirements

### Functional Requirements

- **Profile Creation**: Veterinarians complete detailed profile during registration
- **Profile Management**: Veterinarians can view and update their profile information
- **Matrícula Validation**: System validates professional license number format
- **Address Management**: Store complete address including province, locality, street, postal code
- **Contact Information**: Email and phone number with validation
- **Profile Verification**: Laboratory staff can verify veterinarian credentials
- **Profile Search**: Laboratory staff can search veterinarians by name, email, or matrícula

### Non-Functional Requirements

- **Data Validation**: All fields validated on client and server side
- **Data Privacy**: Personal information protected according to Argentine data protection laws
- **Audit Trail**: Changes to profiles logged for compliance
- **Performance**: Profile lookup < 500ms

## Data Model

### Veterinario Table
```sql
veterinario (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  user_id: INTEGER UNIQUE NOT NULL,
  apellido: VARCHAR(100) NOT NULL,
  nombre: VARCHAR(100) NOT NULL,
  nro_matricula: VARCHAR(50) UNIQUE NOT NULL,
  telefono: VARCHAR(50) NOT NULL,
  email: VARCHAR(255) NOT NULL, -- denormalized for quick access
  is_verified: BOOLEAN DEFAULT FALSE,
  verified_by: INTEGER, -- admin user who verified
  verified_at: TIMESTAMP,
  created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (verified_by) REFERENCES users(id)
)
```

### Domicilio Table
```sql
domicilio (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  veterinario_id: INTEGER UNIQUE NOT NULL,
  provincia: VARCHAR(100) NOT NULL,
  localidad: VARCHAR(100) NOT NULL,
  calle: VARCHAR(200) NOT NULL,
  numero: VARCHAR(20) NOT NULL,
  codigo_postal: VARCHAR(20),
  piso: VARCHAR(10),
  departamento: VARCHAR(10),
  observaciones: TEXT,
  created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (veterinario_id) REFERENCES veterinario(id) ON DELETE CASCADE
)
```

### Profile Change Log Table (for audit)
```sql
veterinario_changes (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  veterinario_id: INTEGER NOT NULL,
  changed_by: INTEGER NOT NULL,
  field_name: VARCHAR(50) NOT NULL,
  old_value: TEXT,
  new_value: TEXT,
  changed_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (veterinario_id) REFERENCES veterinario(id),
  FOREIGN KEY (changed_by) REFERENCES users(id)
)
```

## API Design

### Profile Management Endpoints

#### GET /api/veterinarians/profile
Get current veterinarian's profile.

**Response (200 OK):**
```json
{
  "veterinario": {
    "id": 123,
    "nombre": "Juan",
    "apellido": "Pérez",
    "nro_matricula": "MP-12345",
    "telefono": "+54 342 1234567",
    "email": "vet@example.com",
    "is_verified": true,
    "domicilio": {
      "provincia": "Santa Fe",
      "localidad": "Esperanza",
      "calle": "San Martín",
      "numero": "1234",
      "codigo_postal": "3080"
    }
  }
}
```

#### PUT /api/veterinarians/profile
Update current veterinarian's profile.

**Request:**
```json
{
  "nombre": "Juan Carlos",
  "apellido": "Pérez",
  "telefono": "+54 342 1234567",
  "domicilio": {
    "provincia": "Santa Fe",
    "localidad": "Esperanza",
    "calle": "San Martín",
    "numero": "1234",
    "piso": "2",
    "departamento": "A",
    "codigo_postal": "3080"
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Perfil actualizado exitosamente",
  "veterinario": { /* updated profile */ }
}
```

#### GET /api/veterinarians/:id (Admin/Lab Staff only)
Get specific veterinarian's profile.

**Response (200 OK):**
```json
{
  "veterinario": { /* profile data */ },
  "stats": {
    "total_protocolos": 45,
    "last_protocol_date": "2024-10-01",
    "total_gastado": 25000
  }
}
```

#### GET /api/veterinarians (Admin/Lab Staff only)
Search and list veterinarians.

**Query Parameters:**
- `search`: Search by name, email, or matrícula
- `verified`: Filter by verification status (true/false)
- `page`: Page number (default: 1)
- `limit`: Results per page (default: 20)

**Response (200 OK):**
```json
{
  "veterinarians": [
    {
      "id": 123,
      "nombre": "Juan",
      "apellido": "Pérez",
      "email": "vet@example.com",
      "nro_matricula": "MP-12345",
      "is_verified": true,
      "total_protocolos": 45
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_records": 98,
    "limit": 20
  }
}
```

#### POST /api/veterinarians/:id/verify (Admin only)
Verify a veterinarian's credentials.

**Request:**
```json
{
  "verification_notes": "Verified matrícula with CMVP Santa Fe"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Veterinario verificado exitosamente"
}
```

#### GET /api/veterinarians/profile/history
Get change history for current veterinarian's profile.

**Response (200 OK):**
```json
{
  "changes": [
    {
      "field_name": "telefono",
      "old_value": "+54 342 1111111",
      "new_value": "+54 342 1234567",
      "changed_at": "2024-09-15T10:30:00Z",
      "changed_by": "self"
    }
  ]
}
```

## Business Logic

### Matrícula Validation
- Format validation: Must match provincial pattern (e.g., "MP-XXXXX" for Santa Fe)
- Uniqueness check: No two veterinarians can have same matrícula
- Optional: Integration with professional registry API for real-time validation

### Profile Completeness
- Required fields for account activation:
  - Nombre, Apellido
  - Matrícula
  - Teléfono
  - Email (from user account)
  - Full address (provincia, localidad, calle, número)
- Optional fields:
  - Piso, Departamento
  - Código Postal
  - Observaciones

### Data Privacy Rules
- Veterinarians can only view/edit their own profile
- Laboratory staff can view all profiles (read-only)
- Only administrators can verify credentials
- Profile data used for:
  - Communication (emails, SMS notifications)
  - Billing and invoicing
  - Sample tracking and ownership
  - Reporting and analytics (anonymized)

### Profile Verification Workflow
1. Veterinarian registers and completes profile
2. System marks profile as "unverified"
3. Administrator reviews credentials
4. Administrator verifies matrícula with professional registry
5. Administrator marks profile as "verified"
6. Verified veterinarians may receive benefits (priority processing, discounts)

## Acceptance Criteria

1. ✅ Veterinarians can complete profile during registration
2. ✅ All required fields are validated
3. ✅ Matrícula format is validated
4. ✅ Duplicate matrícula is rejected
5. ✅ Veterinarians can update their own profile
6. ✅ Email change requires re-verification
7. ✅ Address is stored in structured format
8. ✅ Laboratory staff can search veterinarians
9. ✅ Administrators can verify veterinarian credentials
10. ✅ Profile changes are logged in audit table
11. ✅ Profile data is protected and only accessible to authorized users
12. ✅ Deleted user accounts cascade delete profile data

## Testing Approach

### Unit Tests
- Matrícula format validation
- Phone number validation
- Required field validation
- Address parsing and storage
- Profile completeness calculation

### Integration Tests
- Complete registration with profile creation
- Profile update with address change
- Search functionality with various filters
- Verification workflow
- Profile change logging
- Cascading deletes on user account deletion

### E2E Tests
- User registers → completes profile → can submit protocols
- User updates phone → change is logged → reflected in all views
- Admin searches veterinarian → views profile → verifies credentials
- User with incomplete profile → prompted to complete → gains full access

### Data Validation Tests
- Invalid matrícula format rejection
- Duplicate matrícula rejection
- Missing required fields rejection
- Invalid email format rejection
- Invalid phone number format rejection

## Technical Considerations

### 🔧 Pending Technical Decisions

1. **Matrícula Validation**:
   - Use regex patterns for each province
   - Integrate with external professional registry API
   - Manual verification only

2. **Address Autocomplete**:
   - Google Maps API integration
   - Local Argentine postal service API
   - Simple dropdown lists

3. **Profile Photos**:
   - Allow profile photos (future feature)
   - Storage location (local/S3/CDN)

### Data Protection Compliance
- **Ley 25.326 (Argentina)**: Personal data protection
- **Right to Access**: Veterinarians can download their data
- **Right to Rectification**: Veterinarians can update their data
- **Right to Deletion**: Veterinarians can request account deletion
- **Data Retention**: Retain profile data for 5 years after last activity

### Performance Optimization
- Index on frequently searched fields:
  - `veterinario.nro_matricula`
  - `veterinario.apellido`
  - `veterinario.email`
  - `domicilio.provincia`
- Caching of veterinarian list for admin panel
- Pagination on search results

## Dependencies

### Must be completed first:
- Step 01: Authentication & User Management

### Enables these steps:
- Step 03: Protocol Submission (requires complete veterinarian profile)
- Step 07: Work Order Management (requires address for invoicing)

## Estimated Effort

**Time**: 0.5-1 week (part of Sprint 1-2)

**Breakdown**:
- Database schema: 0.5 days
- Backend API implementation: 2 days
- Frontend profile forms: 2 days
- Validation logic: 1 day
- Search functionality: 1 day
- Testing: 1 day

## Implementation Notes

### Development Phases
1. **Phase 1**: Basic profile CRUD operations
2. **Phase 2**: Address management
3. **Phase 3**: Search and filtering
4. **Phase 4**: Verification workflow
5. **Phase 5**: Audit logging

### Validation Rules
```javascript
// Matrícula validation example (Santa Fe)
const MATRICULA_REGEX = /^MP-\d{4,6}$/;

// Phone validation (Argentine format)
const PHONE_REGEX = /^\+54\s\d{2,4}\s\d{6,8}$/;

// Required fields
const REQUIRED_FIELDS = [
  'nombre', 'apellido', 'nro_matricula', 
  'telefono', 'email', 
  'domicilio.provincia', 'domicilio.localidad', 
  'domicilio.calle', 'domicilio.numero'
];
```

### Testing Checklist
- [ ] Profile creation during registration
- [ ] Profile update with validation
- [ ] Matrícula uniqueness enforcement
- [ ] Search by various criteria
- [ ] Verification workflow
- [ ] Change history logging
- [ ] Data privacy controls
- [ ] Cascade delete on user deletion

### Sample Test Data
```json
{
  "nombre": "María",
  "apellido": "González",
  "nro_matricula": "MP-54321",
  "telefono": "+54 342 4567890",
  "email": "mgonzalez@veterinaria.com",
  "domicilio": {
    "provincia": "Santa Fe",
    "localidad": "Santa Fe",
    "calle": "San Jerónimo",
    "numero": "3456",
    "codigo_postal": "3000"
  }
}
```

