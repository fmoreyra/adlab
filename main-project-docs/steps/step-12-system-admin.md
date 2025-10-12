# Step 12: System Configuration & Administration

## Problem Statement

The system requires administrative capabilities for managing users, configuring system settings, maintaining reference data (pricing, species lists, etc.), monitoring system health, and accessing audit logs. Django's built-in admin interface provides a powerful foundation for these tasks. We'll customize the admin with laboratory-specific branding, add a configuration panel, system health monitoring, and enhance the user experience for administrators.

## Requirements

### Functional Requirements

- **Django Admin Customization**:
  - Custom admin site branding (logo, colors, titles)
  - Enhanced admin dashboard with quick stats
  - System health monitoring panel
  - Configuration management interface
  
- **User Management** (via Django Admin):
  - Create, edit, disable user accounts
  - Role assignment via groups and permissions
  - Bulk user operations (activate/deactivate)
  - User activity tracking
  
- **Configuration Panel**:
  - System-wide settings (editable via admin)
  - Email configuration
  - TAT targets
  - File upload limits
  - Maintenance mode toggle
  
- **Reference Data Management** (via Django Admin):
- Pricing catalog maintenance
  - Species, breeds, diagnosis categories
  - All existing models accessible
  
- **System Monitoring**:
  - Custom admin views for system health
  - Database statistics
  - Disk usage warnings
  - Recent activity overview
  - Alert management

### Non-Functional Requirements

- **Security**: Django's built-in permissions + staff-only access
- **Auditability**: Django admin log + custom AdminAction model
- **Usability**: Clean, intuitive admin interface
- **Performance**: Admin operations don't impact user experience

## Data Model

### Existing Models (Managed via Django Admin)
All models from previous steps are accessible via Django admin:
- `User`, `Veterinarian`, `Histopathologist` (Step 01-02)
- `Protocol`, `Sample` (Step 03-04)
- `Report` (Step 06)
- `WorkOrder`, `PricingCatalog` (Step 07)
- `AnalyticsSnapshot` (Step 10, read-only)

### New Model: SystemConfig

```python
class SystemConfig(models.Model):
    """
    System-wide configuration settings.
    Editable via Django admin.
    """
    
    class ConfigType(models.TextChoices):
        STRING = 'string', 'String'
        INTEGER = 'integer', 'Integer'
        BOOLEAN = 'boolean', 'Boolean'
        DECIMAL = 'decimal', 'Decimal'
        JSON = 'json', 'JSON'
    
    class ConfigCategory(models.TextChoices):
        EMAIL = 'email', 'Email Settings'
        SYSTEM = 'system', 'System Settings'
        TAT = 'tat', 'TAT Targets'
        FILES = 'files', 'File Uploads'
        NOTIFICATIONS = 'notifications', 'Notifications'
    
    key = models.CharField(max_length=100, unique=True, 
                           help_text="Configuration key (e.g., smtp_host)")
    value = models.TextField(help_text="Configuration value")
    config_type = models.CharField(max_length=20, choices=ConfigType.choices, 
                                    default=ConfigType.STRING)
    category = models.CharField(max_length=50, choices=ConfigCategory.choices,
                                default=ConfigCategory.SYSTEM)
    description = models.TextField(help_text="Human-readable description")
    is_editable = models.BooleanField(default=True, 
                                      help_text="Can be edited via admin?")
    is_secret = models.BooleanField(default=False,
                                    help_text="Hide value in admin (passwords)")
    
    updated_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                    null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "System Configuration"
        verbose_name_plural = "System Configuration"
        ordering = ['category', 'key']
    
    def __str__(self):
        return f"{self.key} = {self.get_display_value()}"
    
    def get_typed_value(self):
        """Return value cast to correct type."""
        if self.config_type == self.ConfigType.INTEGER:
            return int(self.value)
        elif self.config_type == self.ConfigType.BOOLEAN:
            return self.value.lower() in ('true', '1', 'yes')
        elif self.config_type == self.ConfigType.DECIMAL:
            return Decimal(self.value)
        elif self.config_type == self.ConfigType.JSON:
            return json.loads(self.value)
        return self.value
    
    def get_display_value(self):
        """Return display value (hide secrets)."""
        if self.is_secret:
            return '******'
        return self.value[:50] + '...' if len(self.value) > 50 else self.value
    
    @classmethod
    def get_config(cls, key, default=None):
        """Get configuration value by key."""
        try:
            config = cls.objects.get(key=key)
            return config.get_typed_value()
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_config(cls, key, value, user=None):
        """Set configuration value."""
        config, created = cls.objects.get_or_create(key=key)
        config.value = str(value)
        config.updated_by = user
        config.save()
        return config
```

### New Model: SystemAlert

```python
class SystemAlert(models.Model):
    """
    System alerts for monitoring.
    Managed via Django admin.
    """
    
    class AlertType(models.TextChoices):
        ERROR = 'error', 'Error'
        WARNING = 'warning', 'Warning'
        INFO = 'info', 'Info'
    
    class Severity(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'
    
    alert_type = models.CharField(max_length=20, choices=AlertType.choices)
    severity = models.CharField(max_length=20, choices=Severity.choices)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='resolved_alerts')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_note = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "System Alert"
        verbose_name_plural = "System Alerts"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_resolved', '-created_at']),
            models.Index(fields=['severity', '-created_at']),
        ]
    
    def __str__(self):
        return f"[{self.severity.upper()}] {self.message[:50]}"
    
    def resolve(self, user, note=''):
        """Mark alert as resolved."""
        self.is_resolved = True
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.resolved_note = note
        self.save()
```

### Django Admin Log (Built-in)
Django provides `LogEntry` model that automatically logs admin actions:
- User additions/changes/deletions
- Model instance additions/changes/deletions
- Includes user, timestamp, action type, and change message

## Django Admin Customization

### Custom Admin Site

Create a custom admin site with laboratory branding:

```python
# config/admin.py
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html

class LabAdminSite(AdminSite):
    site_header = 'Laboratorio de Anatomía Patológica'
    site_title = 'Admin - LAP UNL'
    index_title = 'Administración del Sistema'
    
    def each_context(self, request):
        """Add custom context to every admin page."""
        context = super().each_context(request)
        
        # Add quick stats
        from protocols.models import Protocol, WorkOrder
        from accounts.models import User
        
        context['quick_stats'] = {
            'active_users': User.objects.filter(is_active=True).count(),
            'pending_protocols': Protocol.objects.filter(
                status=Protocol.Status.PENDING_RECEPTION
            ).count(),
            'unresolved_alerts': SystemAlert.objects.filter(
                is_resolved=False
            ).count(),
        }
        
        return context

# Replace default admin site
lab_admin_site = LabAdminSite(name='lab_admin')
```

### Admin Styling

```css
/* static/admin/css/lab_admin.css */

/* Custom color scheme - Laboratory blue/green */
:root {
    --primary: #1976d2;  /* Lab blue */
    --secondary: #388e3c;  /* Lab green */
    --accent: #f57c00;  /* Warning orange */
    --dark: #263238;
}

#header {
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
    color: white;
}

.module h2, .module caption, .inline-group h2 {
    background: var(--primary);
}

.button, input[type=submit], input[type=button], .submit-row input {
    background: var(--primary);
    border-color: var(--primary);
}

.button:hover, input[type=submit]:hover, input[type=button]:hover {
    background: var(--secondary);
    border-color: var(--secondary);
}

/* Dashboard widgets */
.dashboard-widget {
    background: white;
    border-left: 4px solid var(--primary);
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.dashboard-widget h3 {
    color: var(--primary);
    margin-top: 0;
}

.stat-box {
    display: inline-block;
    background: #f5f5f5;
    padding: 15px 25px;
    border-radius: 8px;
    margin: 10px 10px 10px 0;
}

.stat-box .number {
    font-size: 2em;
    font-weight: bold;
    color: var(--primary);
}

.stat-box .label {
    font-size: 0.9em;
    color: #666;
}

/* Alert severity colors */
.alert-critical {
    border-left-color: #d32f2f;
}

.alert-high {
    border-left-color: #f57c00;
}

.alert-medium {
    border-left-color: #fbc02d;
}

.alert-low {
    border-left-color: #388e3c;
}
```

### System Configuration Admin

```python
# protocols/admin.py (or create config/admin.py)
from django.contrib import admin
from .models import SystemConfig, SystemAlert

@admin.register(SystemConfig, site=lab_admin_site)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ['key', 'category', 'display_value', 'config_type', 
                    'updated_by', 'updated_at']
    list_filter = ['category', 'config_type', 'is_editable']
    search_fields = ['key', 'description']
    readonly_fields = ['updated_by', 'updated_at', 'created_at']
    
    fieldsets = [
        ('Configuration', {
            'fields': ('key', 'value', 'config_type', 'category', 'description')
        }),
        ('Options', {
            'fields': ('is_editable', 'is_secret')
        }),
        ('Metadata', {
            'fields': ('updated_by', 'updated_at', 'created_at'),
            'classes': ('collapse',)
        }),
    ]
    
    def display_value(self, obj):
        """Show value with proper formatting."""
        return obj.get_display_value()
    display_value.short_description = 'Value'
    
    def get_readonly_fields(self, request, obj=None):
        """Make non-editable configs readonly."""
        readonly = list(self.readonly_fields)
        if obj and not obj.is_editable:
            readonly.extend(['key', 'value', 'config_type'])
        return readonly
    
    def save_model(self, request, obj, form, change):
        """Track who updated the config."""
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj=None):
        """Only allow deletion of editable configs."""
        if obj and not obj.is_editable:
            return False
        return super().has_delete_permission(request, obj)
```

### System Alerts Admin

```python
@admin.register(SystemAlert, site=lab_admin_site)
class SystemAlertAdmin(admin.ModelAdmin):
    list_display = ['colored_severity', 'alert_type', 'message_preview', 
                    'is_resolved', 'created_at']
    list_filter = ['severity', 'alert_type', 'is_resolved', 'created_at']
    search_fields = ['message']
    readonly_fields = ['created_at', 'resolved_by', 'resolved_at']
    
    fieldsets = [
        ('Alert Information', {
            'fields': ('alert_type', 'severity', 'message', 'details')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_note', 'resolved_by', 'resolved_at'),
            'classes': ('collapse',)
        }),
    ]
    
    actions = ['mark_resolved', 'mark_unresolved']
    
    def colored_severity(self, obj):
        """Display severity with color."""
        colors = {
            'critical': '#d32f2f',
            'high': '#f57c00',
            'medium': '#fbc02d',
            'low': '#388e3c',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.severity, '#666'),
            obj.get_severity_display()
        )
    colored_severity.short_description = 'Severity'
    
    def message_preview(self, obj):
        """Show first 80 chars of message."""
        return obj.message[:80] + '...' if len(obj.message) > 80 else obj.message
    message_preview.short_description = 'Message'
    
    @admin.action(description='Mark selected alerts as resolved')
    def mark_resolved(self, request, queryset):
        """Bulk resolve alerts."""
        for alert in queryset:
            alert.resolve(request.user, 'Resolved by admin')
        self.message_user(request, f'{queryset.count()} alerts marked as resolved.')
    
    @admin.action(description='Mark selected alerts as unresolved')
    def mark_unresolved(self, request, queryset):
        """Bulk unresolve alerts."""
        queryset.update(is_resolved=False, resolved_by=None, 
                       resolved_at=None, resolved_note='')
        self.message_user(request, f'{queryset.count()} alerts marked as unresolved.')
```

### Enhanced User Admin

```python
# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Veterinarian

@admin.register(User, site=lab_admin_site)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_active', 
                    'is_staff', 'last_login']
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Laboratory Info', {
            'fields': ('role',)
        }),
    )
    
    actions = ['activate_users', 'deactivate_users', 'send_password_reset']
    
    @admin.action(description='Activate selected users')
    def activate_users(self, request, queryset):
        """Bulk activate users."""
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} users activated.')
    
    @admin.action(description='Deactivate selected users')
    def deactivate_users(self, request, queryset):
        """Bulk deactivate users."""
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} users deactivated.')
    
    @admin.action(description='Send password reset emails')
    def send_password_reset(self, request, queryset):
        """Send password reset to selected users."""
        from django.contrib.auth.forms import PasswordResetForm
        
        count = 0
        for user in queryset:
            form = PasswordResetForm({'email': user.email})
            if form.is_valid():
                form.save(request=request)
                count += 1
        
        self.message_user(request, f'Password reset sent to {count} users.')
```

### Custom Dashboard View

```python
# config/admin_views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count, Q
from datetime import timedelta
from django.utils import timezone

@staff_member_required
def system_health_view(request):
    """Custom admin view for system health."""
    import shutil
    import psutil
    
    # Database stats
    from protocols.models import Protocol, Report, WorkOrder
    from accounts.models import User
    
    # Disk usage
    disk = shutil.disk_usage('/')
    disk_percent = (disk.used / disk.total) * 100
    
    # Protocol stats
    last_30_days = timezone.now() - timedelta(days=30)
    protocols_last_30 = Protocol.objects.filter(
        reception_date__gte=last_30_days
    ).count()
    
    # Pending items
    pending_protocols = Protocol.objects.filter(
        status=Protocol.Status.PENDING_RECEPTION
    ).count()
    
    pending_reports = Protocol.objects.filter(
        status__in=[Protocol.Status.PROCESSING, Protocol.Status.PENDING_REPORT]
    ).count()
    
    # System alerts
    unresolved_alerts = SystemAlert.objects.filter(is_resolved=False)
    critical_alerts = unresolved_alerts.filter(severity='critical').count()
    
    context = {
        'title': 'System Health',
        'disk_usage': {
            'used_gb': disk.used // (1024**3),
            'total_gb': disk.total // (1024**3),
            'percent': disk_percent,
            'status': 'critical' if disk_percent > 95 else 'warning' if disk_percent > 90 else 'ok'
        },
        'stats': {
            'active_users': User.objects.filter(is_active=True).count(),
            'protocols_last_30': protocols_last_30,
            'pending_protocols': pending_protocols,
            'pending_reports': pending_reports,
        },
        'alerts': {
            'total_unresolved': unresolved_alerts.count(),
            'critical': critical_alerts,
            'recent': unresolved_alerts[:10]
        }
    }
    
    return render(request, 'admin/system_health.html', context)
```

### Register Custom View in Admin

```python
# config/urls.py
from django.urls import path
from config.admin_views import system_health_view

# Add to admin URLs
lab_admin_site.get_urls = lambda: [
    path('system-health/', system_health_view, name='system_health'),
] + super(LabAdminSite, lab_admin_site).get_urls()
```

### Custom Dashboard Template

```html
<!-- templates/admin/index.html -->
{% extends "admin/base_site.html" %}
{% load i18n static %}

{% block extrastyle %}
<link rel="stylesheet" type="text/css" href="{% static 'admin/css/lab_admin.css' %}">
{% endblock %}

{% block content %}
<h1>{% translate 'Dashboard' %}</h1>

<!-- Quick Stats -->
<div class="dashboard-widget">
    <h3>📊 Quick Stats</h3>
    <div class="stat-box">
        <div class="number">{{ quick_stats.active_users }}</div>
        <div class="label">Active Users</div>
    </div>
    <div class="stat-box">
        <div class="number">{{ quick_stats.pending_protocols }}</div>
        <div class="label">Pending Protocols</div>
    </div>
    <div class="stat-box">
        <div class="number">{{ quick_stats.unresolved_alerts }}</div>
        <div class="label">Unresolved Alerts</div>
    </div>
    
    <a href="{% url 'admin:system_health' %}" class="button">
        View System Health →
    </a>
</div>

<!-- Recent Activity -->
<div class="dashboard-widget">
    <h3>📝 Recent Admin Actions</h3>
    {% load log %}
    {% get_admin_log 10 as admin_log %}
    <ul>
    {% for entry in admin_log %}
        <li>
            {{ entry.action_time|date:"SHORT_DATETIME_FORMAT" }} - 
            {{ entry.user.get_username }} - 
            {{ entry.change_message }}
        </li>
    {% empty %}
        <li>No recent actions.</li>
    {% endfor %}
    </ul>
</div>

<!-- Default admin app list -->
<div id="content-main">
    {% for app in available_apps %}
        <div class="app-{{ app.app_label }} module">
            <table>
                <caption>
                    <a href="{{ app.app_url }}" class="section" title="{% blocktranslate with name=app.name %}Models in the {{ name }} application{% endblocktranslate %}">{{ app.name }}</a>
                </caption>
                {% for model in app.models %}
                    <tr class="model-{{ model.object_name|lower }}">
                        {% if model.admin_url %}
                            <th scope="row"><a href="{{ model.admin_url }}">{{ model.name }}</a></th>
                        {% else %}
                            <th scope="row">{{ model.name }}</th>
                        {% endif %}

                        {% if model.add_url %}
                            <td><a href="{{ model.add_url }}" class="addlink">{% translate 'Add' %}</a></td>
                        {% else %}
                            <td>&nbsp;</td>
                        {% endif %}

                        {% if model.admin_url %}
                            {% if model.view_only %}
                                <td><a href="{{ model.admin_url }}" class="viewlink">{% translate 'View' %}</a></td>
                            {% else %}
                                <td><a href="{{ model.admin_url }}" class="changelink">{% translate 'Change' %}</a></td>
                            {% endif %}
                        {% else %}
                            <td>&nbsp;</td>
                        {% endif %}
                    </tr>
                {% endfor %}
            </table>
        </div>
    {% endfor %}
</div>
{% endblock %}
```

---

## Business Logic

### Django Admin Features

**Built-in Capabilities:**
- User CRUD operations via Django admin
- Permission management via groups
- Automatic audit logging (LogEntry)
- Search and filtering on all models
- Export to CSV (can be enabled)
- Inline editing for related models

**Custom Enhancements:**
- Laboratory-specific branding and colors
- Configuration panel via `SystemConfig` model
- System health monitoring dashboard
- Alert management system
- Bulk user operations (activate/deactivate)
- Password reset emails from admin

### Configuration Management

**System Config Model:**
```python
# Example configurations
CONFIGS = {
    'smtp_host': 'smtp.unl.edu.ar',
    'smtp_port': 587,
    'tat_target_histopatologia': 10,
    'tat_target_citologia': 3,
    'max_file_size_mb': 25,
    'maintenance_mode': False,
    'session_timeout_minutes': 120,
}
```

**Configuration Rules:**
- Editable configs can be changed via admin
- Secret configs (passwords) are masked
- Non-editable configs are read-only
- All changes tracked (`updated_by`, `updated_at`)
- Type casting ensures correct data types

**Accessing Configuration:**
```python
# In views or models
smtp_host = SystemConfig.get_config('smtp_host', 'localhost')
tat_target = SystemConfig.get_config('tat_target_histopatologia', 10)

# Setting configuration
SystemConfig.set_config('maintenance_mode', True, user=request.user)
```

### System Health Monitoring

**Celery Task for Monitoring:**
```python
@periodic_task(run_every=timedelta(hours=1))
def check_system_health():
    """Periodic task to check system health and create alerts."""
    import shutil
    
    # Check disk space
    disk = shutil.disk_usage('/')
    disk_percent = (disk.used / disk.total) * 100
    
    if disk_percent > 95:
        SystemAlert.objects.create(
            alert_type='error',
            severity='critical',
            message=f'Disk space critical: {disk_percent:.1f}% used',
            details={'disk_percent': disk_percent, 'used_gb': disk.used // (1024**3)}
        )
    elif disk_percent > 90:
        SystemAlert.objects.create(
            alert_type='warning',
            severity='high',
            message=f'Disk space warning: {disk_percent:.1f}% used',
            details={'disk_percent': disk_percent}
        )
    
    # Check pending protocols
    from protocols.models import Protocol
    old_pending = Protocol.objects.filter(
        status=Protocol.Status.PENDING_RECEPTION,
        submission_date__lt=timezone.now() - timedelta(days=7)
    ).count()
    
    if old_pending > 0:
        SystemAlert.objects.create(
            alert_type='warning',
            severity='medium',
            message=f'{old_pending} protocols pending reception for > 7 days',
            details={'count': old_pending}
        )
```

**Alert Management:**
- Alerts created automatically by monitoring tasks
- Admins can view/resolve via Django admin
- Bulk actions to resolve multiple alerts
- Resolution tracking (who, when, note)

### Audit Logging

**Django's Built-in Logging:**
Django automatically logs all admin actions to `LogEntry`:
- User additions/changes/deletions
- Model additions/changes/deletions
- Includes: user, timestamp, action type, change message

**Viewing Audit Log:**
```python
from django.contrib.admin.models import LogEntry

# Recent actions
recent_actions = LogEntry.objects.all()[:100]

# Actions by specific user
user_actions = LogEntry.objects.filter(user=user)

# Actions on specific model
model_actions = LogEntry.objects.filter(
    content_type__app_label='protocols',
    content_type__model='protocol'
)
```

**Enhanced Logging:**
Add custom logging for sensitive operations:
```python
def log_config_change(user, config_key, old_value, new_value):
    """Log configuration changes."""
    logger.info(
        f"Config changed by {user.email}: {config_key} "
        f"from '{old_value}' to '{new_value}'"
    )
```

### Security Considerations

**Django Admin Security:**
- Only staff users (`is_staff=True`) can access admin
- Use Django's permission system for granular access
- Enable two-factor authentication (via `django-otp`)
- Use HTTPS in production
- Set secure session cookies
- Implement IP whitelist ing if needed

**Permissions Strategy:**
```python
# Example: Create groups with specific permissions
admin_group = Group.objects.create(name='Lab Administrators')
admin_group.permissions.add(
    # All permissions
    *Permission.objects.all()
)

staff_group = Group.objects.create(name='Lab Staff')
staff_group.permissions.add(
    # View and change protocols, reports, work orders
    *Permission.objects.filter(
        content_type__app_label='protocols',
        codename__in=['view_protocol', 'change_protocol', 'view_report']
    )
)
```

## Acceptance Criteria

1. [ ] Custom admin site with laboratory branding displays correctly
2. [ ] Admin dashboard shows quick stats (users, pending protocols, alerts)
3. [ ] System health view displays disk usage, database stats, and alerts
4. [ ] `SystemConfig` model allows configuration management via admin
5. [ ] Secret configurations are masked in admin interface
6. [ ] Non-editable configurations are read-only
7. [ ] `SystemAlert` model manages system alerts via admin
8. [ ] Bulk alert resolution action works
9. [ ] Colored severity display for alerts
10. [ ] Custom CSS styles admin interface with lab colors
11. [ ] Enhanced User admin includes bulk activate/deactivate actions
12. [ ] Password reset email action works from user admin
13. [ ] All existing models are accessible via admin
14. [ ] Django's LogEntry tracks all admin actions
15. [ ] Celery task monitors system health hourly
16. [ ] Alerts are created automatically for critical conditions
17. [ ] Only staff users can access admin interface
18. [ ] Permission groups can be configured for role-based access

## Testing Approach

### Model Tests
- **SystemConfig Model:**
  - `get_typed_value()` casts to correct type
  - `get_display_value()` masks secrets
  - `get_config()` retrieves values with defaults
  - `set_config()` updates and tracks user

- **SystemAlert Model:**
  - `resolve()` method updates fields correctly
  - Ordering by creation date descending
  - String representation formats correctly

### Admin Tests
- **SystemConfigAdmin:**
  - List display shows all fields
  - Secret values are masked
  - Non-editable configs are readonly
  - `save_model()` tracks `updated_by`
  - Can't delete non-editable configs

- **SystemAlertAdmin:**
  - Colored severity displays correctly
  - Message preview truncates long messages
  - Bulk resolve action works
  - Bulk unresolve action works

- **CustomUserAdmin:**
  - Bulk activate users action
  - Bulk deactivate users action
  - Send password reset action
  - Role field displays correctly

### Integration Tests
- **Custom Admin Site:**
  - Quick stats calculated correctly
  - System health view accessible
  - Dashboard template renders
  - Custom CSS loads

- **Permissions:**
  - Non-staff users can't access admin
  - Staff users can access admin
  - Permission groups restrict access correctly

### Celery Task Tests
- **check_system_health:**
  - Creates critical alert when disk > 95%
  - Creates warning alert when disk > 90%
  - Creates alert for old pending protocols
  - Doesn't create duplicate alerts

### Security Tests
- Only staff users (`is_staff=True`) can access admin
- CSRF protection enabled for all admin forms
- XSS protection on user inputs
- Session security settings correct

## Technical Considerations

### Django Admin Customization Stack

**Core Technologies:**
- Django 4.x built-in admin
- Custom `AdminSite` subclass
- Template overrides in `templates/admin/`
- CSS in `static/admin/css/`

**Key Files:**
- `config/admin.py` - Custom admin site
- `protocols/admin.py` - Model admin classes
- `config/admin_views.py` - Custom views (system health)
- `templates/admin/index.html` - Dashboard template
- `templates/admin/system_health.html` - Health view template
- `static/admin/css/lab_admin.css` - Custom styling

### Optional Enhancements

**1. Django Admin Interface (django-admin-interface):**
- Even more customization options
- Theme builder
- Logo/favicon management
- Not required, but nice to have

**2. Two-Factor Authentication (django-otp):**
```python
# Add to INSTALLED_APPS
INSTALLED_APPS += [
    'django_otp',
    'django_otp.plugins.otp_totp',
]

# Add middleware
MIDDLEWARE += [
    'django_otp.middleware.OTPMiddleware',
]
```

**3. Advanced Permissions (django-guardian):**
- Object-level permissions
- More granular access control
- Only if needed for complex scenarios

### Performance Considerations

**Admin Queries:**
- Use `list_select_related` for foreign keys
- Use `list_prefetch_related` for many-to-many
- Add `search_fields` with database indexes
- Limit `list_per_page` for large datasets

```python
class ProtocolAdmin(admin.ModelAdmin):
    list_select_related = ['veterinarian', 'work_order']
    list_prefetch_related = ['samples']
    list_per_page = 50  # Default is 100
```

**System Health Monitoring:**
- Run as Celery periodic task (hourly)
- Don't run on every request
- Cache results if displaying on dashboard
- Use database indexes for alert queries

### Security Best Practices

**Settings Configuration:**
```python
# settings.py

# Secure admin URL (obscurity, not security)
ADMIN_URL = env('ADMIN_URL', default='admin/')  # Could be 'secret-admin/'

# Session security
SESSION_COOKIE_AGE = 7200  # 2 hours
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'

# CSRF protection
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

# Admin session timeout
ADMIN_SESSION_TIMEOUT = 1800  # 30 minutes
```

**IP Whitelisting (Optional):**
```python
# middleware/admin_ip_whitelist.py
class AdminIPWhitelistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.whitelist = ['192.168.1.0/24', '10.0.0.1']
    
    def __call__(self, request):
        if request.path.startswith('/admin/'):
            if not self._is_whitelisted(request):
                return HttpResponseForbidden('Access denied')
        return self.get_response(request)
```

**Rate Limiting:**
```python
# Use django-ratelimit for admin login
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/h', method='POST')
def admin_login_view(request):
    # Login logic
    pass
```

## Dependencies

### Must be completed first:
- Step 01: Authentication (User model)
- All other steps (to register their models in admin)

### Optional Dependencies:
- Celery configuration (for system health monitoring)
- Step 07 (WorkOrder, PricingCatalog models)

### Estimated Effort

**Time**: 3-4 days

**Breakdown**:
- SystemConfig and SystemAlert models: 0.5 day
- Custom admin site and branding: 0.5 day
- Admin class customizations: 1 day
- Custom CSS styling: 0.5 day
- System health view and dashboard: 1 day
- Celery monitoring task: 0.5 day
- Testing: 0.5-1 day

**Note**: Much less effort than originally estimated because we're leveraging Django's built-in admin instead of building custom APIs and interfaces.

## Implementation Notes

### File Structure

```
laboratory-system/
├── src/
│   ├── config/
│   │   ├── admin.py              # Custom admin site
│   │   ├── admin_views.py        # System health view
│   │   ├── models.py             # SystemConfig, SystemAlert
│   │   └── tasks.py              # check_system_health Celery task
│   │
│   ├── accounts/
│   │   └── admin.py              # CustomUserAdmin
│   │
│   ├── protocols/
│   │   └── admin.py              # Protocol, WorkOrder admins
│   │
│   ├── templates/
│   │   └── admin/
│   │       ├── index.html        # Dashboard
│   │       ├── system_health.html
│   │       └── base_site.html    # Branding overrides
│   │
│   └── static/
│       └── admin/
│           └── css/
│               └── lab_admin.css  # Custom styling
```

### Initial Configuration Setup

Create a management command to populate default configurations:

```python
# config/management/commands/setup_configs.py
from django.core.management.base import BaseCommand
from config.models import SystemConfig

class Command(BaseCommand):
    help = 'Setup default system configurations'
    
    def handle(self, *args, **options):
        configs = [
            {
                'key': 'smtp_host',
                'value': 'smtp.unl.edu.ar',
                'config_type': 'string',
                'category': 'email',
                'description': 'SMTP server hostname',
                'is_editable': True,
            },
            {
                'key': 'smtp_port',
                'value': '587',
                'config_type': 'integer',
                'category': 'email',
                'description': 'SMTP server port',
                'is_editable': True,
            },
            {
                'key': 'tat_target_histopatologia',
                'value': '10',
                'config_type': 'integer',
                'category': 'tat',
                'description': 'Target TAT for histopathology (days)',
                'is_editable': True,
            },
            {
                'key': 'tat_target_citologia',
                'value': '3',
                'config_type': 'integer',
                'category': 'tat',
                'description': 'Target TAT for cytology (days)',
                'is_editable': True,
            },
            {
                'key': 'max_file_size_mb',
                'value': '25',
                'config_type': 'integer',
                'category': 'files',
                'description': 'Maximum file upload size (MB)',
                'is_editable': True,
            },
            {
                'key': 'maintenance_mode',
                'value': 'false',
                'config_type': 'boolean',
                'category': 'system',
                'description': 'Enable maintenance mode',
                'is_editable': True,
            },
        ]
        
        for config_data in configs:
            SystemConfig.objects.get_or_create(
                key=config_data['key'],
                defaults=config_data
            )
        
        self.stdout.write(self.style.SUCCESS('✓ Default configurations created'))
```

Run with: `python manage.py setup_configs`

### URL Configuration

```python
# config/urls.py
from django.contrib import admin
from django.urls import path, include
from config.admin import lab_admin_site

urlpatterns = [
    # Use custom admin site
    path('admin/', lab_admin_site.urls),
    
    # Other URLs
    path('', include('protocols.urls')),
    path('accounts/', include('accounts.urls')),
]
```

### Celery Beat Schedule

```python
# config/celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    # ... existing schedules ...
    
    'check-system-health': {
        'task': 'config.tasks.check_system_health',
        'schedule': crontab(minute=0),  # Every hour
    },
}
```

### Testing Checklist

- [ ] Custom admin site displays with laboratory branding
- [ ] Quick stats show on dashboard
- [ ] System health view accessible and displays metrics
- [ ] SystemConfig can be added/edited via admin
- [ ] Secret configs are masked
- [ ] Non-editable configs are readonly
- [ ] SystemAlert can be added/resolved via admin
- [ ] Bulk alert actions work
- [ ] User bulk actions work (activate/deactivate/password reset)
- [ ] All models registered and accessible
- [ ] Django LogEntry tracks actions
- [ ] Celery task creates alerts
- [ ] Custom CSS styles apply
- [ ] Non-staff users cannot access admin
- [ ] Permission groups work

### Migration from Step 12

If existing admin customizations exist, they can be integrated:
1. Keep existing `ModelAdmin` classes
2. Register with `lab_admin_site` instead of default `admin.site`
3. Add custom branding CSS
4. Add `SystemConfig` and `SystemAlert` models
5. Create system health view

