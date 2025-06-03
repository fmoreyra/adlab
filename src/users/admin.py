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

@admin.register(Veterinarian)
class VeterinarianAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "license_number", "address")
    search_fields = ("user__first_name", "user__last_name", "user__email", "license_number")
    list_filter = ("license_number",)

@admin.register(Histopathologist)
class HistopathologistAdmin(admin.ModelAdmin):
    list_display = ("user", "license_number", "position", "can_issue_reports")
    search_fields = ("user__first_name", "user__last_name", "license_number", "position")
    list_filter = ("can_issue_reports", "position")
