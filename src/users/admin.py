from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Address, Veterinarian, Histopathologist

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("street", "number", "city", "province", "postal_code")
    search_fields = ("street", "city", "province", "postal_code")

class VeterinarianInline(admin.StackedInline):
    model = Veterinarian
    can_delete = False
    verbose_name_plural = 'Veterinarian Profile'

class CustomUserAdmin(UserAdmin):
    inlines = (VeterinarianInline,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

def approve_veterinarians(modeladmin, request, queryset):
    """Admin action to approve selected veterinarians"""
    updated = queryset.update(is_approved=True)
    modeladmin.message_user(request, f'{updated} veterinarian(s) approved successfully.')
approve_veterinarians.short_description = 'Approve selected veterinarians'

def unapprove_veterinarians(modeladmin, request, queryset):
    """Admin action to unapprove selected veterinarians"""
    updated = queryset.update(is_approved=False)
    modeladmin.message_user(request, f'{updated} veterinarian(s) unapproved.')
unapprove_veterinarians.short_description = 'Unapprove selected veterinarians'

@admin.register(Veterinarian)
class VeterinarianAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "license_number", "is_approved", "address")
    search_fields = ("user__first_name", "user__last_name", "user__email", "license_number")
    list_filter = ("is_approved", "license_number")
    actions = [approve_veterinarians, unapprove_veterinarians]
    
    def get_queryset(self, request):
        """Order by approval status (pending first) then by name"""
        qs = super().get_queryset(request)
        return qs.order_by('is_approved', 'user__first_name')

@admin.register(Histopathologist)
class HistopathologistAdmin(admin.ModelAdmin):
    list_display = ("user", "license_number", "position", "can_issue_reports")
    search_fields = ("user__first_name", "user__last_name", "license_number", "position")
    list_filter = ("can_issue_reports", "position")
