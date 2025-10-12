"""
Admin configuration for Report models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from protocols.models import CassetteObservation, Report, ReportImage


class CassetteObservationInline(admin.TabularInline):
    """Inline admin for cassette observations in reports."""

    model = CassetteObservation
    extra = 1
    fields = ["cassette", "observations", "partial_diagnosis", "order"]
    readonly_fields = []


class ReportImageInline(admin.TabularInline):
    """Inline admin for report images."""

    model = ReportImage
    extra = 0
    fields = [
        "cassette",
        "slide",
        "image_path",
        "description",
        "magnification",
        "technique",
        "order",
    ]
    readonly_fields = []


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Admin interface for Report model."""

    list_display = [
        "id",
        "get_protocol_number",
        "histopathologist",
        "veterinarian",
        "status",
        "report_date",
        "email_status",
        "created_at",
    ]
    list_filter = [
        "status",
        "email_status",
        "report_date",
        "created_at",
    ]
    search_fields = [
        "protocol__protocol_number",
        "protocol__temporary_code",
        "protocol__animal_identification",
        "histopathologist__last_name",
        "histopathologist__first_name",
        "veterinarian__last_name",
        "veterinarian__first_name",
        "diagnosis",
    ]
    readonly_fields = ["created_at", "updated_at", "pdf_hash"]
    date_hierarchy = "report_date"

    fieldsets = (
        (
            _("Protocol Information"),
            {
                "fields": (
                    "protocol",
                    "histopathologist",
                    "veterinarian",
                ),
            },
        ),
        (
            _("Report Content"),
            {
                "fields": (
                    "macroscopic_observations",
                    "microscopic_observations",
                    "diagnosis",
                    "comments",
                    "recommendations",
                ),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": (
                    "report_date",
                    "version",
                    "status",
                ),
            },
        ),
        (
            _("PDF Information"),
            {
                "fields": (
                    "pdf_path",
                    "pdf_hash",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Email Information"),
            {
                "fields": (
                    "sent_date",
                    "sent_to_email",
                    "email_status",
                    "email_error",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [CassetteObservationInline, ReportImageInline]

    def get_protocol_number(self, obj):
        """Display protocol number with link."""
        if obj.protocol.protocol_number:
            return format_html(
                '<a href="/admin/protocols/protocol/{}/change/">{}</a>',
                obj.protocol.id,
                obj.protocol.protocol_number,
            )
        return "-"

    get_protocol_number.short_description = _("Protocol")
    get_protocol_number.admin_order_field = "protocol__protocol_number"


@admin.register(CassetteObservation)
class CassetteObservationAdmin(admin.ModelAdmin):
    """Admin interface for CassetteObservation model."""

    list_display = [
        "id",
        "get_report",
        "get_cassette_code",
        "get_observations_preview",
        "order",
    ]
    list_filter = ["report__status", "created_at"]
    search_fields = [
        "report__protocol__protocol_number",
        "cassette__codigo_cassette",
        "observations",
        "partial_diagnosis",
    ]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            _("Report and Cassette"),
            {
                "fields": (
                    "report",
                    "cassette",
                    "order",
                ),
            },
        ),
        (
            _("Observations"),
            {
                "fields": (
                    "observations",
                    "partial_diagnosis",
                ),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_report(self, obj):
        """Display report with protocol number."""
        return f"{obj.report.protocol.protocol_number} - v{obj.report.version}"

    get_report.short_description = _("Report")

    def get_cassette_code(self, obj):
        """Display cassette code."""
        return obj.cassette.codigo_cassette

    get_cassette_code.short_description = _("Cassette")
    get_cassette_code.admin_order_field = "cassette__codigo_cassette"

    def get_observations_preview(self, obj):
        """Display preview of observations."""
        return (
            obj.observations[:100] + "..."
            if len(obj.observations) > 100
            else obj.observations
        )

    get_observations_preview.short_description = _("Observations")


@admin.register(ReportImage)
class ReportImageAdmin(admin.ModelAdmin):
    """Admin interface for ReportImage model."""

    list_display = [
        "id",
        "get_report",
        "get_item",
        "description",
        "magnification",
        "technique",
        "order",
    ]
    list_filter = ["created_at"]
    search_fields = [
        "report__protocol__protocol_number",
        "cassette__codigo_cassette",
        "slide__codigo_portaobjetos",
        "description",
    ]
    readonly_fields = ["created_at"]

    fieldsets = (
        (
            _("Report and Item"),
            {
                "fields": (
                    "report",
                    "cassette",
                    "slide",
                    "order",
                ),
            },
        ),
        (
            _("Image Information"),
            {
                "fields": (
                    "image_path",
                    "description",
                    "magnification",
                    "technique",
                ),
            },
        ),
        (
            _("Timestamp"),
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )

    def get_report(self, obj):
        """Display report with protocol number."""
        return f"{obj.report.protocol.protocol_number} - v{obj.report.version}"

    get_report.short_description = _("Report")

    def get_item(self, obj):
        """Display associated cassette or slide."""
        if obj.cassette:
            return obj.cassette.codigo_cassette
        elif obj.slide:
            return obj.slide.codigo_portaobjetos
        return "-"

    get_item.short_description = _("Item")
