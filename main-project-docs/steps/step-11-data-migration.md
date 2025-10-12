# Step 11: Data Migration

> ⚠️ **STATUS: DEFERRED / NOT TO BE IMPLEMENTED**
>
> **Date:** October 12, 2025  
> **Reason:** Unclear requirements for legacy system data usage. The laboratory will evaluate whether historical data migration is necessary after the new system is in production.
>
> **Alternative Approach:** If needed, an initial manual SQL insert can be performed for critical historical records. However, a full automated migration from the Clarion system is not currently planned.
>
> **Future Consideration:** This step can be revisited if:
> - There's a clear business need for 10+ years of historical data
> - The laboratory identifies specific use cases requiring legacy data
> - Resources are allocated for the migration effort (3 weeks estimated)

---

## Problem Statement

The laboratory has 10+ years of historical data in the legacy Clarion system (version 2.0, running on Windows XP). This data must be migrated to the new system to maintain continuity, enable historical analysis, and provide complete client history. The migration must be accurate, verified, and allow for a transition period where both systems can coexist.

## Requirements

### Functional Requirements (RNF08)

- Extract data from legacy Clarion database
- Clean and normalize extracted data
- Map legacy schema to new schema
- Import data into new system
- Validate data integrity post-migration
- Handle data inconsistencies and errors
- Support for partial/incremental migration
- Rollback capability
- Coexistence period (dual-entry if needed)
- Complete audit trail of migration

### Non-Functional Requirements

- **Data Integrity**: 100% accuracy, zero data loss
- **Completeness**: All historical protocols migrated
- **Performance**: Migration of 10,000 records in < 1 hour
- **Reversibility**: Ability to rollback migration
- **Auditability**: Complete log of migration process

## Data Model

### Migration_Log Table
```sql
migration_log (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  batch_id: VARCHAR(50) NOT NULL,
  tipo: ENUM('protocolo', 'veterinario', 'informe', 'otro') NOT NULL,
  legacy_id: VARCHAR(100),
  new_id: INTEGER,
  estado: ENUM('pendiente', 'exitoso', 'fallido', 'omitido') NOT NULL,
  error_mensaje: TEXT,
  datos_legacy: JSON, -- Original data for reference
  created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Migration_Stats Table
```sql
migration_stats (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  batch_id: VARCHAR(50) UNIQUE NOT NULL,
  fecha_inicio: DATETIME NOT NULL,
  fecha_fin: DATETIME,
  total_registros: INTEGER,
  exitosos: INTEGER DEFAULT 0,
  fallidos: INTEGER DEFAULT 0,
  omitidos: INTEGER DEFAULT 0,
  estado: ENUM('en_progreso', 'completado', 'fallido', 'revertido') NOT NULL,
  created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### ID Mapping Tables (for reference during transition)
```sql
legacy_mapping (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  tipo_entidad: VARCHAR(50) NOT NULL, -- 'protocolo', 'veterinario', etc.
  legacy_id: VARCHAR(100) NOT NULL,
  new_id: INTEGER NOT NULL,
  UNIQUE KEY (tipo_entidad, legacy_id)
)
```

## Migration Strategy

### Phase 1: Analysis & Planning

**Tasks:**
1. **Schema Analysis**
   - Document Clarion database schema
   - Identify all tables and relationships
   - Map fields to new schema

2. **Data Quality Assessment**
   - Count total records
   - Identify duplicates
   - Find incomplete records
   - Analyze data formats

3. **Gap Analysis**
   - Identify fields in legacy not in new system
   - Identify new required fields missing in legacy
   - Define transformation rules

### Phase 2: Extraction

**Connection to Clarion Database:**
- Clarion uses proprietary file format (.DAT files)
- Options:
  - Use Clarion SDK to read files
  - Export to intermediate format (CSV, XML)
  - ODBC driver if available

**Extraction Process:**
```python
# Pseudocode
def extract_legacy_data():
    protocols = extract_table('PROTOCOLOS')
    veterinarios = extract_table('VETERINARIOS')
    informes = extract_table('INFORMES')
    
    # Export to JSON for processing
    save_json('legacy_protocols.json', protocols)
    save_json('legacy_veterinarios.json', veterinarios)
    save_json('legacy_informes.json', informes)
```

### Phase 3: Transformation & Cleaning

**Data Cleaning:**
1. **Normalize Text**
   - Trim whitespace
   - Standardize capitalization
   - Fix encoding issues (CP437 → UTF-8)

2. **Validate Data**
   - Email format validation
   - Phone number formatting
   - Date format standardization

3. **Handle Missing Data**
   - Set defaults for required fields
   - Flag incomplete records

4. **Deduplication**
   - Identify duplicate veterinarians (by email/matrícula)
   - Merge duplicate records

**Field Mapping Example:**
```javascript
// Legacy → New mapping
const FIELD_MAPPING = {
  protocols: {
    'ID_PROTOCOLO': 'codigo_temporal', // Keep as reference
    'TIPO': 'tipo_analisis', // Map 'HP'→'histopatologia', 'CT'→'citologia'
    'FECHA_INGRESO': 'fecha_recepcion',
    'ESPECIE': 'especie',
    'RAZA': 'raza',
    'NOMBRE_ANIMAL': 'identificacion_animal',
    'DIAGNOSTICO': 'diagnostico_presuntivo'
  },
  veterinarios: {
    'ID_VET': 'legacy_id',
    'APELLIDO': 'apellido',
    'NOMBRE': 'nombre',
    'MATRICULA': 'nro_matricula',
    'EMAIL': 'email',
    'TELEFONO': 'telefono'
  }
};
```

### Phase 4: Loading

**Load Order (respect dependencies):**
1. Veterinarios → veterinario table
2. Protocolos → protocolo table
3. Muestras → muestra_citologia / muestra_histopatologia
4. Informes → informe_resultados

**Loading Process:**
```python
def load_data(cleaned_data):
    batch_id = generate_batch_id()
    stats = initialize_stats(batch_id)
    
    for record in cleaned_data:
        try:
            new_id = insert_into_new_db(record)
            log_success(batch_id, record.legacy_id, new_id)
            stats.exitosos += 1
        except Exception as e:
            log_failure(batch_id, record.legacy_id, str(e))
            stats.fallidos += 1
    
    finalize_stats(batch_id, stats)
```

### Phase 5: Validation

**Post-Migration Checks:**
1. **Count Verification**
   ```sql
   -- Verify all records migrated
   SELECT COUNT(*) FROM legacy_protocols;
   SELECT COUNT(*) FROM migration_log WHERE tipo='protocolo' AND estado='exitoso';
   ```

2. **Sample Verification**
   - Select random 100 records
   - Compare legacy vs new data
   - Verify relationships (veterinario → protocolos)

3. **Data Integrity**
   - Check foreign key constraints
   - Verify required fields populated
   - Test queries on migrated data

4. **Business Rules**
   - Verify protocol numbering doesn't conflict
   - Check date ranges make sense
   - Validate calculated fields

## Coexistence Strategy

### Dual-Entry Period (4-6 weeks)

**Option A: Parallel Systems**
- Continue using Clarion for new protocols
- Also enter into new system
- Compare for accuracy

**Option B: New System Primary**
- New protocols go to new system only
- Clarion remains for historical queries
- Gradual transition

**Recommended: Option B**
- Immediate benefits of new system
- Clarion data migrated and accessible
- Clean cutover point

## Rollback Plan

**If Migration Fails:**
1. Stop migration process
2. Mark batch as 'revertido'
3. Delete migrated records (use migration_log to identify)
4. Analyze failures
5. Fix issues and retry

**Rollback Script:**
```sql
-- Delete migrated data for a batch
DELETE FROM protocolo WHERE id IN (
  SELECT new_id FROM migration_log 
  WHERE batch_id = ? AND tipo = 'protocolo'
);

-- Update stats
UPDATE migration_stats 
SET estado = 'revertido' 
WHERE batch_id = ?;
```

## Acceptance Criteria

> **Note:** These criteria are preserved for reference but are **NOT ACTIVE** since this step is deferred.

1. ⏸️ All historical protocols extracted from Clarion
2. ⏸️ Data cleaned and normalized
3. ⏸️ Veterinarian data migrated and deduplicated
4. ⏸️ Protocol data migrated with correct relationships
5. ⏸️ Report data migrated where available
6. ⏸️ Sample verification passes (100 random records)
7. ⏸️ Count verification matches
8. ⏸️ No orphaned records
9. ⏸️ Complete migration log
10. ⏸️ Rollback procedure tested and documented

## Testing Approach

### Pre-Migration Tests
- Test extraction from Clarion
- Test transformation logic
- Test loading to test database
- Verify data quality

### Migration Tests
- Dry run on copy of production
- Validate counts and relationships
- Test random sampling
- Performance testing

### Post-Migration Tests
- Data integrity checks
- Application functionality with migrated data
- Historical query performance
- User acceptance testing

## Technical Considerations

### 🔧 Pending Technical Decisions

1. **Clarion Data Access Method**:
   - Direct file reading (requires Clarion SDK)
   - Export to CSV/XML first
   - ODBC if available

2. **Migration Timing**:
   - Weekend migration (minimal disruption)
   - Off-hours migration
   - Gradual migration (batch by year)

3. **Data Retention**:
   - Keep Clarion database as archive
   - How long to maintain legacy_mapping tables
   - When to purge migration logs

### Known Challenges

**Challenge 1: Character Encoding**
- Clarion uses CP437/CP850 encoding
- Need conversion to UTF-8
- Special characters (ñ, á, etc.) may corrupt

**Solution:** Use iconv or similar tools for encoding conversion

**Challenge 2: Missing Data**
- Some legacy records incomplete
- New system has stricter validation

**Solution:** 
- Allow import with warnings
- Flag for review
- Manual completion later

**Challenge 3: Date Formats**
- Clarion stores dates in proprietary format
- Need accurate conversion

**Solution:** Test date conversion extensively with known values

## Dependencies

### Must be completed first:
- All other steps (migration happens last)
- System fully functional and tested

### Estimated Effort

**Time**: 3 weeks (Sprint 14-16)

**Breakdown:**
- Week 1: Analysis, extraction, transformation logic
- Week 2: Loading, validation, testing on copy
- Week 3: Production migration, validation, transition support

## Implementation Notes

### Migration Checklist
- [ ] Analyze Clarion schema
- [ ] Develop extraction scripts
- [ ] Develop transformation/cleaning scripts
- [ ] Create mapping tables
- [ ] Test on small dataset (100 records)
- [ ] Test on larger dataset (1000 records)
- [ ] Dry run on full copy
- [ ] Validate dry run results
- [ ] Schedule production migration
- [ ] Backup everything
- [ ] Execute production migration
- [ ] Validate production migration
- [ ] Mark Clarion as read-only
- [ ] Train users on new system
- [ ] Monitor for issues
- [ ] Archive Clarion database

### Sample Extraction Script
```python
import clarion_sdk # hypothetical

def extract_protocols():
    db = clarion_sdk.open('HISTOPAT.DAT')
    protocols = []
    
    for record in db.table('PROTOCOLOS'):
        protocols.append({
            'legacy_id': record['ID_PROTOCOLO'],
            'tipo': record['TIPO'],
            'fecha': convert_clarion_date(record['FECHA']),
            'especie': decode_text(record['ESPECIE']),
            # ... more fields
        })
    
    return protocols

def decode_text(text):
    """Convert CP437 to UTF-8"""
    return text.decode('cp437').encode('utf-8')
```

### Validation Report Template
```
MIGRATION VALIDATION REPORT
Date: 2024-10-15
Batch ID: MIG-20241015-001

COUNTS:
  Legacy Protocols: 8,543
  Migrated Protocols: 8,543
  Match: ✓

SAMPLE VERIFICATION:
  Random samples checked: 100
  Matches: 98
  Discrepancies: 2 (see details)

DATA INTEGRITY:
  Orphaned records: 0
  Invalid foreign keys: 0
  Missing required fields: 5 (flagged for review)

STATUS: PASSED
```

---

## ⚠️ Implementation Status

**This step (Step 11: Data Migration) is currently DEFERRED and will not be implemented.**

The new laboratory system will start fresh without migrating historical data from the Clarion system. If specific historical records are needed, they can be manually inserted via SQL on a case-by-case basis.

The specification above is preserved for reference in case a future migration effort is approved.

