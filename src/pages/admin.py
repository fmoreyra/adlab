"""
Django admin for the pages app.
"""

from django.contrib import admin

from pages.models import ServerStatsSnapshot


@admin.register(ServerStatsSnapshot)
class ServerStatsSnapshotAdmin(admin.ModelAdmin):
    """Read-only admin for server stats snapshot (debugging)."""

    list_display = ("id", "updated_at")
    readonly_fields = ("payload", "updated_at")
    list_display_links = ("id", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return ["payload", "updated_at"]
