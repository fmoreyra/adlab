# Step 20: Multi-Tenant SaaS Refactoring

**Status**: PLANNED 📋  
**Priority**: Future Enhancement  
**Estimated Effort**: 20-27 days (4-5 weeks)  
**Dependencies**: Complete current system (Steps 01-15)

## Overview

Transform the AdLab single-tenant laboratory system into a multi-tenant SaaS platform that can be sold to multiple laboratories. The refactoring will implement:

- **Shared database with tenant isolation** (tenant_id on all tables)
- **Minimal white-labeling** (logo, colors, lab name)
- **SaaS deployment model** (centralized hosting)
- **Manual invoicing** (no automated billing initially)
- **Fresh start for new labs** (no data migration tools)

## Architecture Changes

### Core Multi-Tenancy Pattern

**Tenant Model**: Create a `Laboratory` model that represents each client lab. All data models will have a foreign key to `Laboratory` to ensure complete data isolation.

**Tenant Context**: Implement middleware to set the current tenant based on subdomain/domain and store it in thread-local storage for automatic filtering.

**Query Filtering**: Create a custom model manager that automatically filters all queries by the current tenant, preventing cross-tenant data leaks.

---

## Implementation Steps

### Step 1: Create Laboratory (Tenant) Model

**File**: `src/accounts/models.py`

Add new `Laboratory` model:

```python
class Laboratory(models.Model):
    """
    Represents a laboratory tenant in the multi-tenant system.
    Each laboratory is a separate client with isolated data.
    """
    # Identification
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)
    
    # Branding (minimal white-labeling)
    logo = models.ImageField(upload_to='lab_logos/', blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#3B82F6')  # Hex color
    secondary_color = models.CharField(max_length=7, default='#1E40AF')
    
    # Contact information
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    
    # Subscription & billing
    is_active = models.BooleanField(default=True)
    subscription_start_date = models.DateField(default=date.today)
    subscription_end_date = models.DateField(null=True, blank=True)
    billing_contact_name = models.CharField(max_length=200, blank=True)
    billing_contact_email = models.EmailField(blank=True)
    billing_notes = models.TextField(blank=True)
    
    # Settings
    timezone = models.CharField(max_length=50, default='America/Argentina/Buenos_Aires')
    language = models.CharField(max_length=10, default='es-ar')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Laboratory"
        verbose_name_plural = "Laboratories"
        ordering = ['name']
```

**Migration**: Create migration for Laboratory model.

---

### Step 2: Add Tenant Foreign Keys to All Models

**Files to modify**:
- `src/accounts/models.py` - User, Veterinarian, Histopathologist, Address
- `src/protocols/models.py` - Protocol, CytologySample, HistopathologySample, Cassette, Slide, Report, WorkOrder, PricingCatalog, etc.

**Pattern for each model**:

```python
class ModelName(models.Model):
    laboratory = models.ForeignKey(
        'accounts.Laboratory',
        on_delete=models.PROTECT,
        related_name='model_names',
        verbose_name=_("laboratorio"),
        db_index=True,
    )
    # ... existing fields ...
```

**Key models requiring tenant isolation**:
1. `User` - Each user belongs to one lab
2. `Veterinarian` - Lab-specific veterinarians
3. `Histopathologist` - Lab staff
4. `Protocol` - Lab-specific protocols
5. `CytologySample` / `HistopathologySample`
6. `Cassette` / `Slide`
7. `Report`
8. `WorkOrder`
9. `PricingCatalog` - Each lab sets their own prices
10. `ProtocolCounter` / `TemporaryCodeCounter` / `WorkOrderCounter` - Per-lab counters
11. `EmailLog` / `NotificationPreference`
12. All audit logs (AuthAuditLog, VeterinarianChangeLog, etc.)

**Important**: Add `unique_together` constraints where needed:
```python
class Meta:
    unique_together = [['laboratory', 'email']]  # For User model
```

**Migration**: Create migration to add `laboratory_id` to all models.

---

### Step 3: Create Tenant-Aware Model Manager

**File**: `src/accounts/managers.py` (new file)

```python
from django.db import models
from .middleware import get_current_laboratory

class TenantManager(models.Manager):
    """
    Custom manager that automatically filters queries by current tenant.
    """
    
    def get_queryset(self):
        """Filter queryset by current laboratory."""
        queryset = super().get_queryset()
        laboratory = get_current_laboratory()
        
        if laboratory is not None:
            return queryset.filter(laboratory=laboratory)
        
        # If no laboratory context, return empty queryset (safety)
        return queryset.none()
    
    def all_tenants(self):
        """Bypass tenant filtering (for superadmin only)."""
        return super().get_queryset()
```

**Apply to all tenant-aware models**:

```python
class Protocol(models.Model):
    laboratory = models.ForeignKey('accounts.Laboratory', ...)
    # ... fields ...
    
    objects = TenantManager()  # Default manager with tenant filtering
    all_objects = models.Manager()  # Unfiltered manager for admin
```

---

### Step 4: Implement Tenant Context Middleware

**File**: `src/accounts/middleware.py` (new file)

```python
import threading
from django.shortcuts import redirect
from django.contrib import messages
from .models import Laboratory

# Thread-local storage for current laboratory
_thread_locals = threading.local()

def get_current_laboratory():
    """Get the current laboratory from thread-local storage."""
    return getattr(_thread_locals, 'laboratory', None)

def set_current_laboratory(laboratory):
    """Set the current laboratory in thread-local storage."""
    _thread_locals.laboratory = laboratory

class TenantMiddleware:
    """
    Middleware to set current laboratory based on subdomain or user.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Extract subdomain from host
        host = request.get_host().split(':')[0]  # Remove port
        subdomain = self._extract_subdomain(host)
        
        laboratory = None
        
        # Try to get laboratory from subdomain
        if subdomain:
            laboratory = Laboratory.objects.filter(
                slug=subdomain, 
                is_active=True
            ).first()
        
        # If user is authenticated and no subdomain match, use user's lab
        if not laboratory and request.user.is_authenticated:
            if hasattr(request.user, 'laboratory'):
                laboratory = request.user.laboratory
        
        # Set laboratory in thread-local storage
        set_current_laboratory(laboratory)
        
        # Store in request for easy access
        request.laboratory = laboratory
        
        # Check if laboratory is required but missing
        if not laboratory and self._requires_laboratory(request.path):
            messages.error(request, "No se pudo determinar el laboratorio.")
            return redirect('select_laboratory')
        
        response = self.get_response(request)
        
        # Clean up thread-local
        set_current_laboratory(None)
        
        return response
    
    def _extract_subdomain(self, host):
        """Extract subdomain from host."""
        parts = host.split('.')
        if len(parts) > 2:
            return parts[0]
        return None
    
    def _requires_laboratory(self, path):
        """Check if path requires laboratory context."""
        # Exclude public paths
        public_paths = ['/accounts/login/', '/accounts/register/', '/admin/', '/up/']
        return not any(path.startswith(p) for p in public_paths)
```

**Add to settings.py**:

```python
MIDDLEWARE = [
    # ... existing middleware ...
    'accounts.middleware.TenantMiddleware',  # Add after AuthenticationMiddleware
]
```

---

### Step 5: Update User Registration & Authentication

**File**: `src/accounts/views.py`

**Changes needed**:

1. **Registration**: Add laboratory selection/creation during registration
2. **Login**: Verify user belongs to the laboratory from subdomain
3. **Profile**: Show laboratory information

**New view for laboratory selection**:

```python
def select_laboratory_view(request):
    """Allow user to select their laboratory."""
    laboratories = Laboratory.objects.filter(is_active=True)
    # ... implementation
```

**Update registration form** (`src/accounts/forms.py`):

```python
class RegistrationForm(forms.ModelForm):
    laboratory = forms.ModelChoiceField(
        queryset=Laboratory.objects.filter(is_active=True),
        required=True,
        label=_("Laboratorio")
    )
    # ... existing fields ...
```

---

### Step 6: Update All Views for Tenant Isolation

**Pattern for all views**:

1. **ListView**: Queryset automatically filtered by TenantManager
2. **CreateView**: Set `laboratory` on save
3. **DetailView**: Verify object belongs to current laboratory
4. **UpdateView**: Verify object belongs to current laboratory

**Example**: `src/protocols/views.py`

```python
class ProtocolListView(ListView):
    model = Protocol  # Automatically filtered by TenantManager
    # ... existing code ...

class ProtocolCreateView(CreateView):
    def form_valid(self, form):
        form.instance.laboratory = self.request.laboratory
        form.instance.veterinarian = self.request.user.veterinarian_profile
        return super().form_valid(form)
```

**Files requiring updates**:
- `src/protocols/views.py` - All protocol views
- `src/protocols/views_reports.py` - All report views
- `src/protocols/views_workorder.py` - All work order views
- `src/pages/views.py` - Dashboard views
- `src/accounts/views.py` - Profile views

---

### Step 7: Update Services for Tenant Context

**Files to modify**:
- `src/protocols/services/protocol_service.py`
- `src/protocols/services/report_service.py`
- `src/protocols/services/workorder_service.py`
- `src/protocols/services/email_service.py`
- `src/protocols/services/pdf_service.py`

**Pattern**: Pass `laboratory` parameter or get from context

```python
class ProtocolService:
    @staticmethod
    def create_protocol(data, veterinarian, laboratory):
        protocol = Protocol(
            laboratory=laboratory,
            veterinarian=veterinarian,
            **data
        )
        protocol.save()
        return protocol
```

---

### Step 8: Update Counters for Per-Tenant Numbering

**File**: `src/protocols/models.py`

Update counter models to include laboratory:

```python
class ProtocolCounter(models.Model):
    laboratory = models.ForeignKey('accounts.Laboratory', ...)
    analysis_type = models.CharField(...)
    year = models.IntegerField(...)
    last_number = models.IntegerField(default=0)
    
    class Meta:
        unique_together = [['laboratory', 'analysis_type', 'year']]
```

**Update counter methods**:

```python
@classmethod
def get_next_number(cls, laboratory, analysis_type, year=None):
    with transaction.atomic():
        counter, created = cls.objects.select_for_update().get_or_create(
            laboratory=laboratory,
            analysis_type=analysis_type,
            year=year or date.today().year,
            defaults={'last_number': 0}
        )
        counter.last_number += 1
        counter.save()
        # ... format number ...
```

Apply same pattern to:
- `TemporaryCodeCounter`
- `WorkOrderCounter`

---

### Step 9: Implement White-Labeling in Templates

**File**: `src/templates/layouts/index.html` (base template)

Add laboratory branding context:

```django
{% load static %}
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}{{ laboratory.name }}{% endblock %}</title>
    <style>
        :root {
            --primary-color: {{ laboratory.primary_color }};
            --secondary-color: {{ laboratory.secondary_color }};
        }
    </style>
</head>
<body>
    <header>
        {% if laboratory.logo %}
            <img src="{{ laboratory.logo.url }}" alt="{{ laboratory.name }}">
        {% else %}
            <h1>{{ laboratory.name }}</h1>
        {% endif %}
    </header>
    {% block content %}{% endblock %}
</body>
</html>
```

**Create context processor** (`src/accounts/context_processors.py`):

```python
def laboratory_context(request):
    """Add laboratory to template context."""
    return {
        'laboratory': getattr(request, 'laboratory', None)
    }
```

**Add to settings.py**:

```python
TEMPLATES = [{
    'OPTIONS': {
        'context_processors': [
            # ... existing ...
            'accounts.context_processors.laboratory_context',
        ],
    },
}]
```

---

### Step 10: Create Superadmin Interface

**File**: `src/accounts/admin.py`

Create custom admin for managing laboratories:

```python
@admin.register(Laboratory)
class LaboratoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'subscription_start_date', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'email']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'slug', 'email', 'phone', 'address']
        }),
        ('Branding', {
            'fields': ['logo', 'primary_color', 'secondary_color']
        }),
        ('Subscription', {
            'fields': ['is_active', 'subscription_start_date', 'subscription_end_date']
        }),
        ('Billing', {
            'fields': ['billing_contact_name', 'billing_contact_email', 'billing_notes']
        }),
        ('Settings', {
            'fields': ['timezone', 'language']
        }),
    ]
```

**Create superadmin dashboard** for managing all tenants:

```python
class SuperAdminDashboardView(View):
    """Dashboard for platform administrators to manage all laboratories."""
    
    def get(self, request):
        if not request.user.is_superuser:
            return HttpResponseForbidden()
        
        laboratories = Laboratory.objects.all()
        # ... statistics ...
```

---

### Step 11: Update Admin Site for Tenant Filtering

**File**: `src/protocols/admin.py`

Add tenant filtering to all admin classes:

```python
class TenantAdminMixin:
    """Mixin to filter admin by current user's laboratory."""
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # Superuser sees all
        if hasattr(request.user, 'laboratory'):
            return qs.filter(laboratory=request.user.laboratory)
        return qs.none()
    
    def save_model(self, request, obj, form, change):
        if not change and hasattr(request.user, 'laboratory'):
            obj.laboratory = request.user.laboratory
        super().save_model(request, obj, form, change)

@admin.register(Protocol)
class ProtocolAdmin(TenantAdminMixin, admin.ModelAdmin):
    # ... existing config ...
```

---

### Step 12: Update Tests for Multi-Tenancy

**Pattern for all tests**:

```python
class TestProtocolViews(TestCase):
    def setUp(self):
        # Create laboratory
        self.laboratory = Laboratory.objects.create(
            name="Test Lab",
            slug="test-lab",
            email="test@lab.com"
        )
        
        # Create user with laboratory
        self.user = User.objects.create_user(
            email="user@test.com",
            password="password",
            laboratory=self.laboratory
        )
        
        # Set laboratory context
        from accounts.middleware import set_current_laboratory
        set_current_laboratory(self.laboratory)
    
    def tearDown(self):
        from accounts.middleware import set_current_laboratory
        set_current_laboratory(None)
```

**Files requiring test updates**:
- `src/accounts/tests.py`
- `src/protocols/tests.py`
- `src/protocols/tests_reports.py`
- `src/protocols/tests_workorder.py`
- All other test files

---

### Step 13: Add Data Isolation Security Tests

**File**: `src/accounts/tests_security.py` (new file)

```python
class TenantIsolationTests(TestCase):
    """Test that tenant data is properly isolated."""
    
    def test_user_cannot_see_other_lab_protocols(self):
        # Create two labs
        lab1 = Laboratory.objects.create(name="Lab 1", slug="lab1")
        lab2 = Laboratory.objects.create(name="Lab 2", slug="lab2")
        
        # Create protocols in each lab
        protocol1 = Protocol.objects.create(laboratory=lab1, ...)
        protocol2 = Protocol.objects.create(laboratory=lab2, ...)
        
        # Set context to lab1
        set_current_laboratory(lab1)
        
        # Verify only lab1 protocols are visible
        protocols = Protocol.objects.all()
        self.assertEqual(protocols.count(), 1)
        self.assertEqual(protocols.first(), protocol1)
    
    def test_cross_tenant_access_blocked(self):
        # ... test that users cannot access other lab's data via URL manipulation ...
    
    def test_counters_are_per_tenant(self):
        # ... test that protocol numbers don't conflict between labs ...
```

---

### Step 14: Update Email Templates with Branding

**Files**: `src/templates/emails/*.html`

Add laboratory branding to all email templates:

```django
{% load static %}
<div style="background-color: {{ laboratory.primary_color }}; padding: 20px;">
    {% if laboratory.logo %}
        <img src="{{ laboratory.logo.url }}" alt="{{ laboratory.name }}" style="max-height: 60px;">
    {% else %}
        <h1 style="color: white;">{{ laboratory.name }}</h1>
    {% endif %}
</div>

<div style="padding: 20px;">
    {% block email_content %}{% endblock %}
</div>

<footer style="background-color: #f3f4f6; padding: 20px; text-align: center;">
    <p>{{ laboratory.name }}</p>
    <p>{{ laboratory.email }} | {{ laboratory.phone }}</p>
</footer>
```

---

### Step 15: Create Laboratory Settings Page

**File**: `src/accounts/views.py`

```python
class LaboratorySettingsView(LoginRequiredMixin, UpdateView):
    """Allow lab admins to update laboratory settings."""
    model = Laboratory
    template_name = 'accounts/laboratory_settings.html'
    fields = ['name', 'logo', 'primary_color', 'secondary_color', 'email', 'phone', 'address']
    
    def get_object(self):
        return self.request.laboratory
    
    def dispatch(self, request, *args, **kwargs):
        # Only admin users can access
        if not request.user.is_admin_user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)
```

**Template**: `src/accounts/templates/accounts/laboratory_settings.html`

---

### Step 16: Update Documentation

**Files to create/update**:

1. **MULTI_TENANT_GUIDE.md** - Explain multi-tenancy architecture
2. **DEPLOYMENT_GUIDE.md** - Update for SaaS deployment
3. **ADMIN_GUIDE.md** - Guide for superadmins managing laboratories
4. **LAB_ADMIN_GUIDE.md** - Guide for lab administrators
5. **README.md** - Update with multi-tenant information

---

### Step 17: Create Data Migration Script

**File**: `src/scripts/migrate_to_multitenant.py`

Script to migrate existing single-tenant data to multi-tenant structure:

```python
"""
Migrate existing single-tenant data to multi-tenant structure.
This script creates a default laboratory and assigns all existing data to it.
"""

from django.core.management.base import BaseCommand
from accounts.models import Laboratory, User
from protocols.models import Protocol, WorkOrder, Report

class Command(BaseCommand):
    help = 'Migrate single-tenant data to multi-tenant structure'
    
    def handle(self, *args, **options):
        # Create default laboratory
        lab = Laboratory.objects.create(
            name="AdLab - Original",
            slug="adlab-original",
            email="lab@veterinaria.unl.edu.ar",
            is_active=True
        )
        
        # Assign all users to this lab
        User.objects.all().update(laboratory=lab)
        
        # Assign all protocols
        Protocol.objects.all().update(laboratory=lab)
        
        # ... assign all other models ...
        
        self.stdout.write(self.style.SUCCESS(f'Successfully migrated data to laboratory: {lab.name}'))
```

---

### Step 18: Add Subdomain Routing Configuration

**File**: `src/config/settings.py`

```python
# Multi-tenancy settings
ALLOWED_HOSTS = [
    '.yourdomain.com',  # Allow all subdomains
    'localhost',
    '127.0.0.1',
]

# Session cookie domain (for subdomain support)
SESSION_COOKIE_DOMAIN = '.yourdomain.com'
CSRF_COOKIE_DOMAIN = '.yourdomain.com'
```

**Nginx configuration** (for production):

```nginx
server {
    server_name *.yourdomain.com;
    
    location / {
        proxy_pass http://django_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Testing Strategy

1. **Unit Tests**: Test tenant isolation at model level
2. **Integration Tests**: Test cross-tenant access prevention
3. **Security Tests**: Verify no data leakage between tenants
4. **Performance Tests**: Ensure tenant filtering doesn't impact performance
5. **Manual Testing**: Test with multiple laboratory subdomains

---

## Deployment Checklist

- [ ] Run migrations to add Laboratory model
- [ ] Run migration to add laboratory_id to all models
- [ ] Create default laboratory for existing data
- [ ] Run data migration script
- [ ] Update environment variables
- [ ] Configure subdomain routing
- [ ] Test with multiple subdomains
- [ ] Verify data isolation
- [ ] Update documentation
- [ ] Train support team on multi-tenant features

---

## Future Enhancements (Out of Scope)

- Automated billing and subscription management
- Advanced customization (custom fields, workflows)
- API for third-party integrations
- Data migration tools from other lab systems
- Advanced analytics across all tenants (for superadmin)
- Self-service laboratory signup
- Usage-based pricing metrics

---

## Key Files Summary

**New Files**:
- `src/accounts/managers.py` - TenantManager
- `src/accounts/middleware.py` - TenantMiddleware
- `src/accounts/context_processors.py` - Laboratory context
- `src/accounts/tests_security.py` - Tenant isolation tests
- `src/scripts/migrate_to_multitenant.py` - Migration script
- `MULTI_TENANT_GUIDE.md` - Documentation

**Modified Files**:
- `src/accounts/models.py` - Add Laboratory model, add laboratory FK to User
- `src/protocols/models.py` - Add laboratory FK to all models
- `src/accounts/views.py` - Update registration/login
- `src/protocols/views.py` - Update all views
- `src/protocols/views_reports.py` - Update report views
- `src/protocols/views_workorder.py` - Update work order views
- `src/config/settings.py` - Add middleware, context processor
- All service files - Add laboratory context
- All test files - Add laboratory setup
- All templates - Add laboratory branding

---

## Estimated Effort

- **Step 1-2**: Database models (2-3 days)
- **Step 3-4**: Tenant manager and middleware (2 days)
- **Step 5-6**: Views and authentication (3-4 days)
- **Step 7-8**: Services and counters (2 days)
- **Step 9**: White-labeling (1-2 days)
- **Step 10-11**: Admin interface (2 days)
- **Step 12-13**: Testing (3-4 days)
- **Step 14-15**: Email and settings (1-2 days)
- **Step 16-18**: Documentation and deployment (2-3 days)

**Total**: 20-27 days (4-5 weeks)

---

## Risk Mitigation

1. **Data Leakage**: Comprehensive security tests, code review
2. **Performance**: Index laboratory_id fields, monitor query performance
3. **Migration Issues**: Test migration on copy of production data
4. **Breaking Changes**: Maintain backward compatibility where possible
5. **Testing Coverage**: Aim for >90% test coverage on tenant isolation

---

## Implementation Checklist

- [ ] Create Laboratory (tenant) model with branding fields, subscription info, and settings
- [ ] Add laboratory foreign key to all models (User, Protocol, Report, WorkOrder, counters, etc.)
- [ ] Create TenantManager that automatically filters queries by current laboratory
- [ ] Implement TenantMiddleware to set laboratory context from subdomain or user
- [ ] Update registration and login views to handle laboratory context
- [ ] Update all views (protocols, reports, work orders) for tenant isolation
- [ ] Update all service classes to handle laboratory context
- [ ] Update protocol/work order counters to be per-tenant
- [ ] Add laboratory branding to templates (logo, colors) and create context processor
- [ ] Create superadmin interface for managing laboratories
- [ ] Add tenant filtering to Django admin for all models
- [ ] Update all existing tests to create laboratory context
- [ ] Create comprehensive tenant isolation security tests
- [ ] Add laboratory branding to all email templates
- [ ] Create laboratory settings page for lab admins
- [ ] Create script to migrate existing single-tenant data to multi-tenant
- [ ] Update settings and deployment config for subdomain routing
- [ ] Create multi-tenant documentation (admin guide, deployment guide, architecture docs)

---

## Notes

This step represents a major architectural change that transforms the system from single-tenant to multi-tenant SaaS. It should only be implemented after the core system is complete and stable. The implementation requires careful planning and testing to ensure data isolation and security.

**Prerequisites**:
- Complete Steps 01-15 (current system)
- Stable production deployment
- Comprehensive test coverage
- Backup of existing data

**Business Impact**:
- Enables selling the system to multiple laboratories
- Creates recurring revenue opportunity
- Requires new business model (SaaS subscriptions)
- Increases operational complexity

**Technical Impact**:
- Major database schema changes
- All views and services need updates
- New middleware and context management
- Subdomain routing configuration
- Enhanced security requirements
