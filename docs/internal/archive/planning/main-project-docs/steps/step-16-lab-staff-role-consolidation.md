# Step 16: Laboratory Staff Role Consolidation

## Problem Statement

The current system maintains separate roles for PERSONAL_LAB (Laboratory Staff) and HISTOPATOLOGO (Histopathologist), creating artificial separation between team members who work in the same laboratory environment. This separation adds complexity to the codebase, results in duplicate dashboards, restricts collaboration, and creates maintenance overhead for managing two similar but distinct user types. The system needs to consolidate these roles into a single unified Laboratory Staff role with granular permissions for report creation while preserving all existing functionality and professional data.

## Requirements

### Functional Requirements (RF16)

- **RF16.1**: Merge PERSONAL_LAB and HISTOPATOLOGO into unified PERSONAL_LAB role
- **RF16.2**: Preserve all existing professional fields from Histopathologist model (license_number, position, specialty, signature_image)
- **RF16.3**: Add granular permission for report creation (can_create_reports boolean, default=True)
- **RF16.4**: Administrative interface to toggle report creation permission per lab staff member
- **RF16.5**: Preserve digital signature functionality for reports
- **RF16.6**: Maintain existing workflow functionality (reception, processing, reporting)
- **RF16.7**: Redirect all histopathologists to merged laboratory staff dashboard
- **RF16.8**: Migrate all existing Histopathologist data to new LaboratoryStaff model
- **RF16.9**: Provide bulk editing capabilities for report creation permissions in admin interface
- **RF16.10**: Implement audit logging for all permission changes made by administrators

### Non-Functional Requirements

- **Data Integrity**: No data loss during migration, preserve all existing report assignments
- **Security**: Permission system must maintain existing access controls, no privilege escalation
- **Performance**: No degradation in dashboard or view performance after consolidation
- **Audit Trail**: All role changes and permission modifications must be logged
- **Backward Compatibility**: Existing reports must remain accessible with correct author attribution
- **Migration Safety**: No maintenance window required, migration can be performed during normal operations

## Data Model Changes

### User Model Updates
```python
class User(AbstractUser):
    class Role(models.TextChoices):
        VETERINARIO = "veterinario", _("Veterinario Cliente")
        PERSONAL_LAB = "personal_lab", _("Personal de Laboratorio")  # Now includes histopathologists
        ADMIN = "admin", _("Administrador")
        # REMOVE: HISTOPATOLOGO = "histopatologo", _("Histopatólogo")

    @property
    def is_lab_staff(self):
        """Check if user is laboratory staff."""
        return self.role == self.Role.PERSONAL_LAB

    # REMOVE: is_histopathologist property completely
```

### New LaboratoryStaff Model
```python
class LaboratoryStaff(models.Model):
    """
    Unified laboratory staff profile replacing Histopathologist.
    Contains all professional information and permissions.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="lab_staff_profile",
        verbose_name=_("usuario"),
    )
    
    # Core fields (from Histopathologist)
    first_name = models.CharField(_("nombre"), max_length=100)
    last_name = models.CharField(_("apellido"), max_length=100)
    license_number = models.CharField(
        _("número de matrícula"),
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_("Número de matrícula profesional"),
    )
    position = models.CharField(
        _("cargo"),
        max_length=100,
        blank=True,
        help_text=_("Ej: Profesor Titular, Profesor Asociado, Jefe de TP"),
    )
    specialty = models.CharField(
        _("especialidad"),
        max_length=200,
        blank=True,
        help_text=_("Especialidad o área de expertise"),
    )
    signature_image = models.ImageField(
        _("firma digital"),
        upload_to="signatures/lab_staff/",
        blank=True,
        null=True,
        help_text=_("Imagen de la firma para incluir en informes"),
    )
    phone_number = models.CharField(
        _("teléfono"),
        max_length=20,
        blank=True,
        help_text=_("Número de teléfono de contacto"),
    )
    
    # Permission fields (NEW)
    can_create_reports = models.BooleanField(
        _("puede crear informes"),
        default=True,
        help_text=_("Si el personal puede crear y firmar informes"),
    )
    
    # Professional info
    is_active = models.BooleanField(
        _("activo"),
        default=True,
        help_text=_("Si el personal está activo para trabajar en el laboratorio"),
    )
    
    # Timestamps
    created_at = models.DateTimeField(_("creado el"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizado el"), auto_now=True)

    class Meta:
        verbose_name = _("personal de laboratorio")
        verbose_name_plural = _("personal de laboratorio")
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["license_number"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["can_create_reports"]),
        ]

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        """Return full name."""
        return f"{self.first_name} {self.last_name}".strip()

    def get_formal_name(self):
        """Return formal name with title."""
        return f"Dr./Dra. {self.get_full_name()}"

    def has_signature(self):
        """Check if staff has uploaded signature."""
        return bool(self.signature_image)

    def can_sign_reports(self):
        """Check if staff can create and sign reports."""
        return self.is_active and self.can_create_reports and self.has_signature()
```

### Report Model Updates
```python
class Report(models.Model):
    # REMOVE: histopathologist = models.ForeignKey(Histopathologist, ...)
    # REPLACE WITH:
    lab_staff = models.ForeignKey(
        'accounts.LaboratoryStaff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports",
        verbose_name=_("personal de laboratorio"),
        help_text=_("Personal que creó el informe"),
    )
```

## API Design Updates

### Dashboard Routing Changes

#### GET /dashboard/
**Behavior Change:**
- Histopathologist users now redirect to lab staff dashboard
- Single unified dashboard for all laboratory staff

**Updated Response (200 OK):**
```python
# For User.role == 'personal_lab' (includes former histopathologists)
return LabStaffDashboardView.as_view()(request)
# REMOVE: HistopathologistDashboardView routing completely
```

### Permission Check Updates

#### POST /api/reports/
**Request:** (requires authentication)

```json
{
  "protocol_id": 123,
  "diagnosis": "Diagnóstico detallado...",
  "microscopic_findings": "Hallazgos microscópicos..."
}
```

**Permission Logic:**
```python
# OLD: Check if user.is_histopathologist
# NEW: Check if user.is_lab_staff and user.lab_staff_profile.can_create_reports
if not (request.user.is_lab_staff and 
        request.user.lab_staff_profile.can_create_reports):
    raise Http404()  # 404 fallback as requested
```

### Admin Permission Management

#### POST /admin/accounts/laboratorystaff/{id}/change-permission/
**Request:** (admin authentication required)

```json
{
  "can_create_reports": false
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Report creation permission updated",
  "audit_log_id": "uuid-for-tracking"
}
```

## Business Logic Changes

### Role Consolidation Logic

1. **User Creation**: New lab staff created directly as `role='personal_lab'`
2. **Permission Check**: `user.is_lab_staff` now includes all laboratory personnel
3. **Report Creation**: Check `lab_staff_profile.can_create_reports` permission
4. **Dashboard Access**: Single dashboard for all lab staff with permission-based UI
5. **Admin Management**: Bulk permission editing with audit logging for all changes

### Data Migration Strategy

#### Migration Execution (Single Operation)
```python
def migrate_histopathologists_to_lab_staff(apps, schema_editor):
    LaboratoryStaff = apps.get_model('accounts', 'LaboratoryStaff')
    Histopathologist = apps.get_model('accounts', 'Histopathologist')
    User = apps.get_model('auth', 'User')
    Report = apps.get_model('protocols', 'Report')
    AuthAuditLog = apps.get_model('accounts', 'AuthAuditLog')
    
    from django.core.files.base import ContentFile
    import os
    
    for histo in Histopathologist.objects.all():
        # Update user role
        histo.user.role = User.Role.PERSONAL_LAB
        histo.user.save(update_fields=['role'])
        
        # Migrate signature image if exists
        signature_image = None
        if histo.signature_image:
            try:
                # Read old image
                old_path = histo.signature_image.path
                with open(old_path, 'rb') as f:
                    content = f.read()
                
                # Create new file with same content in new location
                filename = os.path.basename(old_path)
                signature_image = ContentFile(content, filename)
            except Exception:
                pass  # Handle gracefully
        
        # Create new LaboratoryStaff profile with preserved timestamps
        lab_staff = LaboratoryStaff.objects.create(
            user=histo.user,
            first_name=histo.first_name,
            last_name=histo.last_name,
            license_number=histo.license_number,
            position=histo.position,
            specialty=histo.specialty,
            signature_image=signature_image,
            phone_number=histo.phone_number,
            can_create_reports=True,  # Default True for all existing histopathologists
            is_active=histo.is_active,
            created_at=histo.created_at,  # Preserve original timestamps
            updated_at=histo.updated_at,
        )
        
        # Update report assignments
        Report.objects.filter(histopathologist=histo).update(lab_staff=lab_staff)
        
        # Log migration for audit trail
        AuthAuditLog.log(
            action=AuthAuditLog.Action.USER_CREATED,
            email=histo.user.email,
            user=None,  # System migration
            details=f"Migrated from Histopathologist to LaboratoryStaff: {lab_staff.get_full_name()}, license: {lab_staff.license_number}"
        )
```

### Dashboard Consolidation Logic

#### Merged Lab Staff Dashboard Features

**Quick Actions Section:**
- Sample reception (former lab staff functionality)
- Processing management (former lab staff functionality)
- Work order creation (former lab staff functionality)
- Report creation (former histopathologist functionality, shown only if can_create_reports=True)
- Report history (merged functionality)

**Statistics Widgets:**
- Pending reception (samples waiting for processing)
- Processing count (currently active samples)
- Pending reports (reports needing creation, shown only if can_create_reports=True)
- Monthly reports completed (productivity metrics, shown only if can_create_reports=True)
- Today's received samples (daily statistics)

**Processing Queue:**
- Unified view showing all protocols in various stages
- Combined management interface for all lab staff
- Permission-based action buttons (report creation only if permitted)

**Feature Discovery Section:**
- All laboratory tools accessible based on permissions
- Report creation tools only shown if can_create_reports=True
- Processing tools always available for all lab staff
- Administrative functions based on user permissions

### Permission Management Logic

#### Admin Interface Features
```python
@admin.register(LaboratoryStaff)
class LaboratoryStaffAdmin(admin.ModelAdmin):
    list_display = [
        'get_full_name', 
        'license_number', 
        'can_create_reports', 
        'is_active',
        'position'
    ]
    list_filter = [
        'can_create_reports', 
        'is_active', 
        'position',
        'specialty'
    ]
    search_fields = [
        'first_name', 
        'last_name', 
        'license_number',
        'user__email'
    ]
    
    actions = [
        'enable_report_creation', 
        'disable_report_creation',
        'bulk_activate',
        'bulk_deactivate'
    ]
    
    def enable_report_creation(self, request, queryset):
        updated = queryset.update(can_create_reports=True)
        # Log each permission change
        for staff in queryset:
            AuthAuditLog.log(
                action=AuthAuditLog.Action.USER_CREATED,  # Reuse for permission changes
                email=staff.user.email,
                user=request.user,
                details=f"Report creation permission ENABLED for {staff.get_full_name()}"
            )
        self.message_user(request, f"{updated} staff members can now create reports.")
    
    def disable_report_creation(self, request, queryset):
        updated = queryset.update(can_create_reports=False)
        # Log each permission change
        for staff in queryset:
            AuthAuditLog.log(
                action=AuthAuditLog.Action.USER_CREATED,  # Reuse for permission changes
                email=staff.user.email,
                user=request.user,
                details=f"Report creation permission DISABLED for {staff.get_full_name()}"
            )
        self.message_user(request, f"{updated} staff members cannot create reports.")
    
    enable_report_creation.short_description = "Enable report creation for selected staff"
    disable_report_creation.short_description = "Disable report creation for selected staff"
```

## Acceptance Criteria

1. ✅ All existing histopathologists converted to lab staff role seamlessly
2. ✅ All professional data preserved (license, specialty, positions, signatures)
3. ✅ Existing reports remain accessible with correct author attribution
4. ✅ Report creation permission toggle works correctly in admin interface
5. ✅ Admin can manage report creation permissions per staff member with bulk operations
6. ✅ Digital signature functionality preserved and working with new model
7. ✅ Merged dashboard shows both processing and reporting features appropriately
8. ✅ Histopathologists redirected to lab staff dashboard seamlessly without user notification
9. ✅ All laboratory workflows (reception → processing → reporting) work end-to-end
10. ✅ No data loss during migration process
11. ✅ All permission checks updated to use new model structure
12. ✅ Email notifications continue to work correctly after role consolidation
13. ✅ Audit logging captures all permission changes by administrators
14. ✅ Users with can_create_reports=False receive 404 when accessing report creation
15. ✅ License number uniqueness maintained across all lab staff
16. ✅ Signature image files migrated from histopathologists/ to lab_staff/ paths

## Testing Approach

### Unit Tests
- LaboratoryStaff model creation, validation, and property methods
- Permission checking logic for can_create_reports
- Role property updates (is_lab_staff, removal of is_histopathologist)
- Data migration functions with edge cases (missing signatures, duplicate licenses)
- Dashboard routing changes and permission-based UI display

### Integration Tests
- Complete workflow: reception → processing → reporting with new permissions
- Permission-based access control for report creation functionality
- Dashboard functionality for different permission levels (can_create_reports True/False)
- Report creation with valid permissions and 404 behavior for invalid permissions
- Digital signature handling and PDF generation with new model
- Admin permission management with bulk operations and audit logging

### Migration Tests
- Data integrity verification before and after migration
- Report assignment preservation and correct author attribution
- User role updates and authentication behavior
- Foreign key relationship updates and orphaned data prevention
- Signature file migration and path verification

### Security Tests
- Permission bypass attempts for report creation without proper authorization
- Privilege escalation testing in consolidated role system
- Audit log verification for all permission changes
- Session handling across role changes
- Digital signature access control and validation

### End-to-End Tests
- Former histopathologist login → dashboard access verification
- Lab staff report creation workflow with proper permissions
- Admin permission management interface testing
- Complete protocol processing workflow from reception to report delivery
- Bulk permission operations testing

## Technical Considerations

### 🔧 Critical Technical Decisions

1. **Migration Strategy**:
   - Single migration operation (create model + migrate data + cleanup)
   - No maintenance window required during normal operations
   - Full rollback capability through standard Django migrations

2. **Database Migration**:
   - Standard Django migration with forward and backward operations
   - Preserve original timestamps from Histopathologist records
   - Migrate signature image files from histopathologists/ to lab_staff/ directory
   - Maintain license number uniqueness constraint across all lab staff

3. **Permission Granularity**:
   - Profile-level permission field for maximum flexibility
   - Default True for all existing histopathologists (preserves functionality)
   - Administrative interface with bulk editing capabilities
   - Comprehensive audit logging for all permission changes

4. **URL Structure**:
   - Remove all histopathologist-specific URLs and routing
   - Update dashboard routing to use unified lab staff view
   - Clean up old templates and remove unused code paths
   - Maintain all existing laboratory functionality URLs

### Security Considerations
- All permission checks must use new unified is_lab_staff property
- Permission changes must be logged with complete audit trail
- No privilege escalation opportunities in permission system
- Digital signature access properly controlled and validated
- Report creation properly secured with 404 fallback

### Performance Considerations
- Dashboard queries optimized for mixed permission-based access
- Database indexes updated for new LaboratoryStaff model structure
- Minimal impact on existing query patterns after migration
- Signature file migration handled efficiently without memory issues

### Migration Safety
- No maintenance window required
- Data migration operates atomically
- Existing functionality preserved during migration
- Rollback capability through standard Django migrations
- Full audit trail of migration process

## Dependencies

### Must be completed first:
- None (this is a foundational system architecture change)

### Dependencies impacted:
- Step 15: User Dashboards (requires update for merged structure)
- Step 08: Email Notifications (permission checks need updates)
- Step 09: Dashboard & Monitoring (metrics updates for unified role)
- All protocol/report workflow steps (permission system updates)

### Cross-Dependencies:
- User authentication system (step-01) - this is an evolution
- Protocol submission and processing workflows - permission checks updates

## Estimated Effort

**Time**: 3-4 days (Sprint 2)

**Breakdown**:
- Database schema and migrations: 1 day
- Backend code updates (permissions, views, decorators): 1.5 days
- Template/dashboard updates: 1 day
- Data migration script and testing: 0.5 days
- Documentation updates: 0.5 days

**Total Estimated**: 4 days

## Implementation Notes

### Development Phases
1. **Phase 1**: Create new LaboratoryStaff model and migrations
2. **Phase 2**: Update all backend code for role consolidation
3. **Phase 3**: Create merged dashboard and update templates
4. **Phase 4**: Execute data migration and cleanup
5. **Phase 5**: Testing and validation of all functionality
6. **Phase 6**: Documentation updates and final validation

### Migration Checklist
- [ ] Full database backup created and verified
- [ ] Migration script tested on staging environment
- [ ] All template changes reviewed and approved
- [ ] Permission system validation completed
- [ ] Admin interface testing finished
- [ ] Post-migration validation checklist prepared

### Risk Mitigation
- **Data Loss Risk**: Django migration atomicity + comprehensive testing
- **Permission System Risk**: Extensive testing of all permission scenarios
- **Dashboard Routing Risk**: Careful URL routing testing with all user types
- **Signature Migration Risk**: Graceful handling of missing files and path changes

### Quality Assurance
- All existing functionality must be preserved
- No regression in user experience for any role type
- Performance must not degrade after consolidation
- Audit trail must be complete and accurate

---

## Next Steps

This step provides the foundation for a more streamlined laboratory management system with unified roles and granular permissions. After completion:

- System will have simplified role structure (3 roles: Veterinario, Personal Lab, Admin)
- Unified dashboard will improve user experience and reduce maintenance
- Granular permissions will provide flexible workforce management
- Cleaner codebase will improve future development efficiency

**Implementation Status**: Ready for development
**Priority**: High (affects core system architecture)
**Dependencies**: None (foundational change)
**Blocked by**: None