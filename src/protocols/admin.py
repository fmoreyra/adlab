from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.utils.translation import gettext_lazy as _

from protocols.emails import (
    queue_email,
    send_sample_reception_notification,
    send_work_order_notification,
)
from protocols.models import (
    Cassette,
    CassetteSlide,
    CytologySample,
    EmailLog,
    HistopathologySample,
    NotificationPreference,
    PricingCatalog,
    ProcessingLog,
    Protocol,
    ProtocolCounter,
    ProtocolStatusHistory,
    ReceptionLog,
    Slide,
    TemporaryCodeCounter,
    WorkOrder,
    WorkOrderCounter,
    WorkOrderService,
)


class CytologySampleInline(admin.StackedInline):
    """Inline admin for cytology samples."""

    model = CytologySample
    extra = 0
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (
            _("Sample Details"),
            {
                "fields": (
                    "veterinarian",
                    "technique_used",
                    "sampling_site",
                    "number_of_slides",
                    "number_slides_received",
                    "observations",
                ),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


class HistopathologySampleInline(admin.StackedInline):
    """Inline admin for histopathology samples."""

    model = HistopathologySample
    extra = 0
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (
            _("Sample Details"),
            {
                "fields": (
                    "veterinarian",
                    "material_submitted",
                    "number_of_containers",
                    "number_jars_received",
                    "preservation",
                    "observations",
                ),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


class ProtocolStatusHistoryInline(admin.TabularInline):
    """Inline admin for protocol status history."""

    model = ProtocolStatusHistory
    extra = 0
    readonly_fields = ["status", "changed_by", "description", "changed_at"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Protocol)
class ProtocolAdmin(admin.ModelAdmin):
    """Admin interface for Protocol model."""

    list_display = [
        "id",
        "get_protocol_code",
        "analysis_type",
        "animal_identification",
        "species",
        "veterinarian",
        "status",
        "submission_date",
        "created_at",
    ]
    list_filter = [
        "status",
        "analysis_type",
        "species",
        "submission_date",
        "created_at",
    ]
    search_fields = [
        "temporary_code",
        "protocol_number",
        "animal_identification",
        "presumptive_diagnosis",
        "veterinarian__first_name",
        "veterinarian__last_name",
        "veterinarian__license_number",
    ]
    readonly_fields = [
        "temporary_code",
        "protocol_number",
        "created_at",
        "updated_at",
        "get_editable_status",
    ]
    date_hierarchy = "submission_date"

    fieldsets = (
        (
            _("Tracking"),
            {
                "fields": (
                    "temporary_code",
                    "protocol_number",
                    "status",
                    "get_editable_status",
                ),
            },
        ),
        (
            _("Basic Information"),
            {
                "fields": (
                    "analysis_type",
                    "veterinarian",
                    "work_order",
                ),
            },
        ),
        (
            _("Animal Information"),
            {
                "fields": (
                    "species",
                    "breed",
                    "sex",
                    "age",
                    "animal_identification",
                    "owner_last_name",
                    "owner_first_name",
                ),
            },
        ),
        (
            _("Clinical Information"),
            {
                "fields": (
                    "presumptive_diagnosis",
                    "clinical_history",
                    "academic_interest",
                ),
            },
        ),
        (
            _("Dates"),
            {
                "fields": (
                    "submission_date",
                    "reception_date",
                    "received_by",
                ),
            },
        ),
        (
            _("Reception Information"),
            {
                "fields": (
                    "sample_condition",
                    "reception_notes",
                    "discrepancies",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["mark_as_received", "mark_as_processing", "mark_as_ready"]

    def get_inlines(self, request, obj):
        """Return appropriate inline based on analysis type."""
        if obj and obj.analysis_type == Protocol.AnalysisType.CYTOLOGY:
            return [CytologySampleInline, ProtocolStatusHistoryInline]
        elif obj and obj.analysis_type == Protocol.AnalysisType.HISTOPATHOLOGY:
            return [HistopathologySampleInline, ProtocolStatusHistoryInline]
        return [ProtocolStatusHistoryInline]

    def get_protocol_code(self, obj):
        """Display protocol number if available, otherwise temporary code."""
        if obj.protocol_number:
            return format_html(
                '<strong style="color: green;">{}</strong>',
                obj.protocol_number,
            )
        elif obj.temporary_code:
            return format_html(
                '<span style="color: orange;">{}</span>',
                obj.temporary_code,
            )
        return "-"

    get_protocol_code.short_description = _("Code")

    def get_editable_status(self, obj):
        """Show if protocol is editable/deletable."""
        if obj.is_editable:
            return format_html(
                '<span style="color: green;">✓ Editable/Deletable</span>'
            )
        return format_html('<span style="color: red;">✗ Locked</span>')

    get_editable_status.short_description = _("Edit Status")

    @admin.action(description=_("Mark selected protocols as received"))
    def mark_as_received(self, request, queryset):
        """Mark selected protocols as received and assign protocol numbers."""
        count = 0
        for protocol in queryset:
            if protocol.status in [
                Protocol.Status.SUBMITTED,
                Protocol.Status.DRAFT,
            ]:
                try:
                    protocol.receive()
                    ProtocolStatusHistory.log_status_change(
                        protocol=protocol,
                        new_status=Protocol.Status.RECEIVED,
                        changed_by=request.user,
                        description="Marked as received by admin",
                    )

                    # Send reception notification email
                    try:
                        send_sample_reception_notification(protocol)
                    except Exception as e:
                        # Log but don't fail the action
                        import logging

                        logger = logging.getLogger(__name__)
                        logger.error(
                            f"Failed to send reception email for protocol {protocol.pk}: {e}"
                        )

                    count += 1
                except Exception:
                    pass

        self.message_user(
            request,
            _("%(count)d protocol(s) marked as received.") % {"count": count},
        )

    @admin.action(description=_("Mark selected protocols as processing"))
    def mark_as_processing(self, request, queryset):
        """Mark selected protocols as processing."""
        count = queryset.filter(status=Protocol.Status.RECEIVED).update(
            status=Protocol.Status.PROCESSING
        )

        # Log status changes
        for protocol in queryset.filter(status=Protocol.Status.PROCESSING):
            ProtocolStatusHistory.log_status_change(
                protocol=protocol,
                new_status=Protocol.Status.PROCESSING,
                changed_by=request.user,
                description="Marked as processing by admin",
            )

        self.message_user(
            request,
            _("%(count)d protocol(s) marked as processing.")
            % {"count": count},
        )

    @admin.action(description=_("Mark selected protocols as ready"))
    def mark_as_ready(self, request, queryset):
        """Mark selected protocols as ready."""
        count = queryset.filter(status=Protocol.Status.PROCESSING).update(
            status=Protocol.Status.READY
        )

        # Log status changes and send notifications
        for protocol in queryset.filter(status=Protocol.Status.READY):
            ProtocolStatusHistory.log_status_change(
                protocol=protocol,
                new_status=Protocol.Status.READY,
                changed_by=request.user,
                description="Marked as ready by admin",
            )

            # Send protocol ready notification
            try:
                queue_email(
                    email_type=EmailLog.EmailType.CUSTOM,
                    recipient_email=protocol.veterinarian.email,
                    subject=f"Muestra lista para diagnóstico - Protocolo {protocol.protocol_number}",
                    context={
                        "protocol": protocol,
                        "veterinarian": protocol.veterinarian,
                    },
                    template_name="emails/protocol_ready.html",
                    protocol=protocol,
                    veterinarian=protocol.veterinarian,
                )
            except Exception as e:
                # Log but don't fail the action
                import logging

                logger = logging.getLogger(__name__)
                logger.error(
                    f"Failed to send ready email for protocol {protocol.pk}: {e}"
                )

        self.message_user(
            request,
            _("%(count)d protocol(s) marked as ready.") % {"count": count},
        )


@admin.register(CytologySample)
class CytologySampleAdmin(admin.ModelAdmin):
    """Admin interface for CytologySample model."""

    list_display = [
        "id",
        "get_protocol_code",
        "veterinarian",
        "technique_used",
        "sampling_site",
        "number_of_slides",
        "created_at",
    ]
    list_filter = [
        "technique_used",
        "created_at",
    ]
    search_fields = [
        "protocol__temporary_code",
        "protocol__protocol_number",
        "sampling_site",
        "technique_used",
        "veterinarian__first_name",
        "veterinarian__last_name",
    ]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            _("Protocol"),
            {
                "fields": ("protocol", "veterinarian"),
            },
        ),
        (
            _("Sample Details"),
            {
                "fields": (
                    "technique_used",
                    "sampling_site",
                    "number_of_slides",
                    "observations",
                ),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_protocol_code(self, obj):
        """Display protocol code."""
        if obj.protocol.protocol_number:
            return obj.protocol.protocol_number
        elif obj.protocol.temporary_code:
            return obj.protocol.temporary_code
        return f"Protocol #{obj.protocol.id}"

    get_protocol_code.short_description = _("Protocol")


@admin.register(HistopathologySample)
class HistopathologySampleAdmin(admin.ModelAdmin):
    """Admin interface for HistopathologySample model."""

    list_display = [
        "id",
        "get_protocol_code",
        "veterinarian",
        "get_material_preview",
        "number_of_containers",
        "preservation",
        "created_at",
    ]
    list_filter = [
        "preservation",
        "created_at",
    ]
    search_fields = [
        "protocol__temporary_code",
        "protocol__protocol_number",
        "material_submitted",
        "veterinarian__first_name",
        "veterinarian__last_name",
    ]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            _("Protocol"),
            {
                "fields": ("protocol", "veterinarian"),
            },
        ),
        (
            _("Sample Details"),
            {
                "fields": (
                    "material_submitted",
                    "number_of_containers",
                    "preservation",
                    "observations",
                ),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_protocol_code(self, obj):
        """Display protocol code."""
        if obj.protocol.protocol_number:
            return obj.protocol.protocol_number
        elif obj.protocol.temporary_code:
            return obj.protocol.temporary_code
        return f"Protocol #{obj.protocol.id}"

    get_protocol_code.short_description = _("Protocol")

    def get_material_preview(self, obj):
        """Show preview of material submitted."""
        return (
            obj.material_submitted[:50] + "..."
            if len(obj.material_submitted) > 50
            else obj.material_submitted
        )

    get_material_preview.short_description = _("Material")


@admin.register(ProtocolStatusHistory)
class ProtocolStatusHistoryAdmin(admin.ModelAdmin):
    """Admin interface for ProtocolStatusHistory model."""

    list_display = [
        "id",
        "protocol",
        "status",
        "changed_by",
        "changed_at",
    ]
    list_filter = [
        "status",
        "changed_at",
    ]
    search_fields = [
        "protocol__temporary_code",
        "protocol__protocol_number",
        "description",
    ]
    readonly_fields = [
        "protocol",
        "status",
        "changed_by",
        "description",
        "changed_at",
    ]
    date_hierarchy = "changed_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        """Audit logs are immutable - no deletion allowed."""
        return False


# ============================================================================
# WORK ORDER ADMIN (STEP 07)
# ============================================================================


class WorkOrderServiceInline(admin.TabularInline):
    """Inline admin for work order services."""

    model = WorkOrderService
    extra = 0
    readonly_fields = ["subtotal"]
    fields = [
        "protocol",
        "description",
        "service_type",
        "quantity",
        "unit_price",
        "subtotal",
        "discount",
    ]


@admin.register(PricingCatalog)
class PricingCatalogAdmin(admin.ModelAdmin):
    """Admin interface for PricingCatalog model."""

    list_display = [
        "service_type",
        "description",
        "price",
        "valid_from",
        "valid_until",
        "is_currently_valid",
    ]
    list_filter = [
        "valid_from",
        "valid_until",
    ]
    search_fields = [
        "service_type",
        "description",
    ]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "valid_from"

    fieldsets = (
        (
            _("Service Information"),
            {
                "fields": (
                    "service_type",
                    "description",
                    "price",
                ),
            },
        ),
        (
            _("Validity Period"),
            {
                "fields": (
                    "valid_from",
                    "valid_until",
                ),
            },
        ),
        (
            _("Additional Information"),
            {
                "fields": ("observations",),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def is_currently_valid(self, obj):
        """Show if price is currently valid."""
        if obj.is_valid():
            return format_html('<span style="color: green;">✓ Valid</span>')
        return format_html('<span style="color: red;">✗ Expired</span>')

    is_currently_valid.short_description = _("Currently Valid")


@admin.register(WorkOrderCounter)
class WorkOrderCounterAdmin(admin.ModelAdmin):
    """Admin interface for WorkOrderCounter model."""

    list_display = [
        "year",
        "last_number",
        "get_next_number_preview",
    ]
    list_filter = [
        "year",
    ]
    search_fields = [
        "year",
    ]
    readonly_fields = ["get_next_number_preview"]

    fieldsets = (
        (
            _("Counter Information"),
            {
                "fields": (
                    "year",
                    "last_number",
                    "get_next_number_preview",
                ),
            },
        ),
    )

    def get_next_number_preview(self, obj):
        """Show example of next work order number."""
        next_num = obj.last_number + 1
        return format_html(
            "<strong>Next number: OT-{}-{:03d}</strong>",
            obj.year,
            next_num,
        )

    get_next_number_preview.short_description = _("Preview")

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete counters."""
        return request.user.is_superuser


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    """Admin interface for WorkOrder model."""

    list_display = [
        "order_number",
        "veterinarian",
        "issue_date",
        "total_amount",
        "balance_due",
        "payment_status",
        "status",
        "created_at",
    ]
    list_filter = [
        "status",
        "payment_status",
        "issue_date",
        "created_at",
    ]
    search_fields = [
        "order_number",
        "veterinarian__user__first_name",
        "veterinarian__user__last_name",
        "veterinarian__license_number",
        "billing_name",
        "cuit_cuil",
    ]
    readonly_fields = [
        "order_number",
        "balance_due",
        "created_at",
        "updated_at",
        "get_payment_status_display_formatted",
        "get_total_from_services",
    ]
    date_hierarchy = "issue_date"
    inlines = [WorkOrderServiceInline]

    fieldsets = (
        (
            _("Work Order Information"),
            {
                "fields": (
                    "order_number",
                    "issue_date",
                    "veterinarian",
                    "status",
                    "created_by",
                ),
            },
        ),
        (
            _("Financial Information"),
            {
                "fields": (
                    "get_total_from_services",
                    "total_amount",
                    "advance_payment",
                    "balance_due",
                    "payment_status",
                    "get_payment_status_display_formatted",
                ),
            },
        ),
        (
            _("Billing Details"),
            {
                "fields": (
                    "billing_name",
                    "cuit_cuil",
                    "iva_condition",
                ),
            },
        ),
        (
            _("Files"),
            {
                "fields": ("pdf_path",),
            },
        ),
        (
            _("Status Tracking"),
            {
                "fields": (
                    "sent_date",
                    "invoiced_date",
                ),
            },
        ),
        (
            _("Additional Information"),
            {
                "fields": ("observations",),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["mark_as_issued", "mark_as_sent", "mark_as_invoiced"]

    def get_payment_status_display_formatted(self, obj):
        """Display payment status with visual indicators."""
        colors = {
            WorkOrder.PaymentStatus.PENDING: "red",
            WorkOrder.PaymentStatus.PARTIAL: "orange",
            WorkOrder.PaymentStatus.PAID: "green",
        }
        color = colors.get(obj.payment_status, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_payment_status_display(),
        )

    get_payment_status_display_formatted.short_description = _(
        "Payment Status"
    )

    def get_total_from_services(self, obj):
        """Calculate total from services."""
        if obj.pk:
            total = obj.calculate_total()
            return format_html(
                "<strong>${:.2f}</strong>",
                total,
            )
        return "-"

    get_total_from_services.short_description = _("Calculated Total")

    @admin.action(description=_("Mark as issued"))
    def mark_as_issued(self, request, queryset):
        """Mark selected work orders as issued."""
        count = 0
        for wo in queryset.filter(status=WorkOrder.Status.DRAFT):
            try:
                wo.issue()

                # Send work order notification email
                try:
                    send_work_order_notification(
                        work_order=wo, work_order_pdf_path=None
                    )
                except Exception as e:
                    # Log but don't fail the action
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.error(
                        f"Failed to send work order email for {wo.pk}: {e}"
                    )

                count += 1
            except ValueError:
                pass
        self.message_user(
            request,
            _("%(count)d work order(s) marked as issued.") % {"count": count},
        )

    @admin.action(description=_("Mark as sent"))
    def mark_as_sent(self, request, queryset):
        """Mark selected work orders as sent."""
        count = 0
        for wo in queryset.filter(
            status__in=[WorkOrder.Status.DRAFT, WorkOrder.Status.ISSUED]
        ):
            try:
                wo.mark_as_sent()
                count += 1
            except ValueError:
                pass
        self.message_user(
            request,
            _("%(count)d work order(s) marked as sent.") % {"count": count},
        )

    @admin.action(description=_("Mark as invoiced"))
    def mark_as_invoiced(self, request, queryset):
        """Mark selected work orders as invoiced."""
        count = 0
        for wo in queryset.filter(status=WorkOrder.Status.SENT):
            try:
                wo.mark_as_invoiced()
                count += 1
            except ValueError:
                pass
        self.message_user(
            request,
            _("%(count)d work order(s) marked as invoiced.")
            % {"count": count},
        )


@admin.register(WorkOrderService)
class WorkOrderServiceAdmin(admin.ModelAdmin):
    """Admin interface for WorkOrderService model."""

    list_display = [
        "id",
        "work_order",
        "protocol",
        "description",
        "service_type",
        "quantity",
        "unit_price",
        "subtotal",
        "discount",
    ]
    list_filter = [
        "service_type",
        "work_order__status",
    ]
    search_fields = [
        "work_order__order_number",
        "protocol__protocol_number",
        "protocol__temporary_code",
        "description",
        "service_type",
    ]
    readonly_fields = ["subtotal"]

    fieldsets = (
        (
            _("Work Order"),
            {
                "fields": (
                    "work_order",
                    "protocol",
                ),
            },
        ),
        (
            _("Service Details"),
            {
                "fields": (
                    "description",
                    "service_type",
                    "quantity",
                    "unit_price",
                    "subtotal",
                    "discount",
                ),
            },
        ),
    )


@admin.register(ReceptionLog)
class ReceptionLogAdmin(admin.ModelAdmin):
    """Admin interface for ReceptionLog model."""

    list_display = [
        "id",
        "protocol",
        "action",
        "user",
        "created_at",
    ]
    list_filter = [
        "action",
        "created_at",
    ]
    search_fields = [
        "protocol__temporary_code",
        "protocol__protocol_number",
        "notes",
        "user__email",
    ]
    readonly_fields = [
        "protocol",
        "action",
        "user",
        "notes",
        "created_at",
    ]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        """Reception logs should not be manually added."""
        return False

    def has_change_permission(self, request, obj=None):
        """Reception logs are read-only."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Audit logs are immutable - no deletion allowed."""
        return False


@admin.register(ProtocolCounter)
class ProtocolCounterAdmin(admin.ModelAdmin):
    """Admin interface for ProtocolCounter model."""

    list_display = [
        "id",
        "analysis_type",
        "year",
        "last_number",
        "get_formatted_display",
    ]
    list_filter = [
        "analysis_type",
        "year",
    ]
    search_fields = [
        "year",
    ]
    readonly_fields = ["get_formatted_display"]

    fieldsets = (
        (
            _("Counter Information"),
            {
                "fields": (
                    "analysis_type",
                    "year",
                    "last_number",
                    "get_formatted_display",
                ),
            },
        ),
    )

    def get_formatted_display(self, obj):
        """Show example of next protocol number."""
        prefix = (
            "CT"
            if obj.analysis_type == Protocol.AnalysisType.CYTOLOGY
            else "HP"
        )
        year_short = str(obj.year)[-2:]
        next_num = obj.last_number + 1
        # Use regular string formatting to avoid SafeString issues
        formatted_text = f"<strong>Next number: {prefix} {year_short}/{next_num:03d}</strong>"
        return mark_safe(formatted_text)

    get_formatted_display.short_description = _("Preview")

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete counters."""
        return request.user.is_superuser


@admin.register(TemporaryCodeCounter)
class TemporaryCodeCounterAdmin(admin.ModelAdmin):
    """Admin interface for TemporaryCodeCounter model."""

    list_display = [
        "id",
        "analysis_type",
        "date",
        "last_number",
        "get_formatted_display",
    ]
    list_filter = [
        "analysis_type",
        "date",
    ]
    search_fields = [
        "date",
    ]
    readonly_fields = ["get_formatted_display"]

    fieldsets = (
        (
            _("Counter Information"),
            {
                "fields": (
                    "analysis_type",
                    "date",
                    "last_number",
                    "get_formatted_display",
                ),
            },
        ),
    )

    def get_formatted_display(self, obj):
        """Show example of next temporary code."""
        prefix = (
            "CT"
            if obj.analysis_type == Protocol.AnalysisType.CYTOLOGY
            else "HP"
        )
        date_str = obj.date.strftime("%Y%m%d")
        next_num = obj.last_number + 1
        formatted_text = f"<strong>Next code: TMP-{prefix}-{date_str}-{next_num:03d}</strong>"
        return mark_safe(formatted_text)

    get_formatted_display.short_description = _("Preview")

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete counters."""
        return request.user.is_superuser


# ============================================================================
# PROCESSING ADMIN (STEP 05)
# ============================================================================


class CassetteSlideInline(admin.TabularInline):
    """Inline admin for cassette-slide associations."""

    model = CassetteSlide
    extra = 0
    readonly_fields = ["created_at"]
    fields = [
        "slide",
        "posicion",
        "coloracion",
        "requiere_multicorte",
        "observaciones",
    ]


@admin.register(Cassette)
class CassetteAdmin(admin.ModelAdmin):
    """Admin interface for Cassette model."""

    list_display = [
        "codigo_cassette",
        "get_protocol_code",
        "material_preview",
        "tipo_cassette",
        "color_cassette",
        "estado",
        "created_at",
    ]
    list_filter = [
        "estado",
        "tipo_cassette",
        "color_cassette",
        "created_at",
    ]
    search_fields = [
        "codigo_cassette",
        "material_incluido",
        "histopathology_sample__protocol__protocol_number",
        "histopathology_sample__protocol__temporary_code",
    ]
    readonly_fields = [
        "codigo_cassette",
        "created_at",
        "updated_at",
        "get_processing_timeline",
    ]
    date_hierarchy = "created_at"
    inlines = [CassetteSlideInline]

    fieldsets = (
        (
            _("Identification"),
            {
                "fields": (
                    "histopathology_sample",
                    "codigo_cassette",
                ),
            },
        ),
        (
            _("Cassette Details"),
            {
                "fields": (
                    "material_incluido",
                    "tipo_cassette",
                    "color_cassette",
                    "estado",
                    "observaciones",
                ),
            },
        ),
        (
            _("Processing Stages"),
            {
                "fields": (
                    "fecha_encasetado",
                    "fecha_fijacion",
                    "fecha_inclusion",
                    "fecha_entacado",
                    "get_processing_timeline",
                ),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = [
        "mark_stage_encasetado",
        "mark_stage_fijacion",
        "mark_stage_inclusion",
        "mark_stage_entacado",
    ]

    def get_protocol_code(self, obj):
        """Display protocol code."""
        protocol = obj.histopathology_sample.protocol
        if protocol.protocol_number:
            return format_html("<strong>{}</strong>", protocol.protocol_number)
        return protocol.temporary_code or f"Protocol #{protocol.id}"

    get_protocol_code.short_description = _("Protocol")

    def material_preview(self, obj):
        """Show preview of material."""
        preview = obj.material_incluido[:40]
        if len(obj.material_incluido) > 40:
            preview += "..."
        return preview

    material_preview.short_description = _("Material")

    def get_processing_timeline(self, obj):
        """Display processing timeline with visual indicators."""
        stages = [
            ("Encasetado", obj.fecha_encasetado),
            ("Fijación", obj.fecha_fijacion),
            ("Inclusión", obj.fecha_inclusion),
            ("Entacado", obj.fecha_entacado),
        ]

        html_parts = []
        for stage_name, stage_date in stages:
            if stage_date:
                html_parts.append(
                    f'<div style="margin: 5px 0;">'
                    f'<span style="color: green;">✓</span> '
                    f"<strong>{stage_name}:</strong> "
                    f"{stage_date.strftime('%Y-%m-%d %H:%M')}"
                    f"</div>"
                )
            else:
                html_parts.append(
                    f'<div style="margin: 5px 0;">'
                    f'<span style="color: gray;">○</span> '
                    f"<strong>{stage_name}:</strong> "
                    f'<span style="color: gray;">Pendiente</span>'
                    f"</div>"
                )

        return format_html("".join(html_parts))

    get_processing_timeline.short_description = _("Processing Timeline")

    @admin.action(description=_("Mark as encasetado"))
    def mark_stage_encasetado(self, request, queryset):
        """Mark selected cassettes as encasetado."""
        count = 0
        for cassette in queryset:
            cassette.update_stage("encasetado")
            ProcessingLog.log_action(
                protocol=cassette.histopathology_sample.protocol,
                etapa=ProcessingLog.Stage.ENCASETADO,
                usuario=request.user,
                cassette=cassette,
                observaciones="Marked by admin",
            )
            count += 1
        self.message_user(
            request,
            _("%(count)d cassette(s) marked as encasetado.")
            % {"count": count},
        )

    @admin.action(description=_("Mark as fijación"))
    def mark_stage_fijacion(self, request, queryset):
        """Mark selected cassettes as in fijación."""
        count = 0
        for cassette in queryset:
            cassette.update_stage("fijacion")
            ProcessingLog.log_action(
                protocol=cassette.histopathology_sample.protocol,
                etapa=ProcessingLog.Stage.FIJACION,
                usuario=request.user,
                cassette=cassette,
                observaciones="Marked by admin",
            )
            count += 1
        self.message_user(
            request,
            _("%(count)d cassette(s) marked as fijación.") % {"count": count},
        )

    @admin.action(description=_("Mark as inclusión"))
    def mark_stage_inclusion(self, request, queryset):
        """Mark selected cassettes as in inclusión."""
        count = 0
        for cassette in queryset:
            cassette.update_stage("inclusion")
            ProcessingLog.log_action(
                protocol=cassette.histopathology_sample.protocol,
                etapa=ProcessingLog.Stage.INCLUSION,
                usuario=request.user,
                cassette=cassette,
                observaciones="Marked by admin",
            )
            count += 1
        self.message_user(
            request,
            _("%(count)d cassette(s) marked as inclusión.") % {"count": count},
        )

    @admin.action(description=_("Mark as entacado (completed)"))
    def mark_stage_entacado(self, request, queryset):
        """Mark selected cassettes as entacado (completed)."""
        count = 0
        for cassette in queryset:
            cassette.update_stage("entacado")
            ProcessingLog.log_action(
                protocol=cassette.histopathology_sample.protocol,
                etapa=ProcessingLog.Stage.ENTACADO,
                usuario=request.user,
                cassette=cassette,
                observaciones="Marked by admin",
            )
            count += 1
        self.message_user(
            request,
            _("%(count)d cassette(s) marked as entacado.") % {"count": count},
        )


@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    """Admin interface for Slide model."""

    list_display = [
        "codigo_portaobjetos",
        "get_protocol_code",
        "get_sample_type",
        "tecnica_coloracion",
        "estado",
        "calidad",
        "created_at",
    ]
    list_filter = [
        "estado",
        "calidad",
        "protocol__analysis_type",
        "created_at",
    ]
    search_fields = [
        "codigo_portaobjetos",
        "protocol__protocol_number",
        "protocol__temporary_code",
        "tecnica_coloracion",
    ]
    readonly_fields = [
        "codigo_portaobjetos",
        "created_at",
        "updated_at",
        "get_cassette_info",
    ]
    date_hierarchy = "created_at"
    inlines = [CassetteSlideInline]

    fieldsets = (
        (
            _("Identification"),
            {
                "fields": (
                    "protocol",
                    "codigo_portaobjetos",
                    "cytology_sample",
                ),
            },
        ),
        (
            _("Slide Details"),
            {
                "fields": (
                    "campo",
                    "tecnica_coloracion",
                    "calidad",
                    "estado",
                    "observaciones",
                ),
            },
        ),
        (
            _("Processing Stages"),
            {
                "fields": (
                    "fecha_montaje",
                    "fecha_coloracion",
                ),
            },
        ),
        (
            _("Cassette Associations"),
            {
                "fields": ("get_cassette_info",),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = [
        "mark_stage_montaje",
        "mark_stage_coloracion",
        "mark_as_ready",
    ]

    def get_protocol_code(self, obj):
        """Display protocol code."""
        if obj.protocol.protocol_number:
            return format_html(
                "<strong>{}</strong>", obj.protocol.protocol_number
            )
        return obj.protocol.temporary_code or f"Protocol #{obj.protocol.id}"

    get_protocol_code.short_description = _("Protocol")

    def get_sample_type(self, obj):
        """Display sample type."""
        return obj.protocol.get_analysis_type_display()

    get_sample_type.short_description = _("Type")

    def get_cassette_info(self, obj):
        """Display associated cassettes."""
        cassette_slides = obj.cassette_slides.select_related("cassette").all()
        if not cassette_slides:
            return format_html(
                '<span style="color: gray;">No cassettes</span>'
            )

        html_parts = []
        for cs in cassette_slides:
            html_parts.append(
                f'<div style="margin: 5px 0;">'
                f"<strong>{cs.cassette.codigo_cassette}</strong> "
                f"({cs.get_posicion_display()})"
                f"</div>"
            )

        return format_html("".join(html_parts))

    get_cassette_info.short_description = _("Associated Cassettes")

    @admin.action(description=_("Mark as montaje"))
    def mark_stage_montaje(self, request, queryset):
        """Mark selected slides as mounted."""
        count = 0
        for slide in queryset:
            slide.update_stage("montaje")
            ProcessingLog.log_action(
                protocol=slide.protocol,
                etapa=ProcessingLog.Stage.MONTAJE,
                usuario=request.user,
                slide=slide,
                observaciones="Marked by admin",
            )
            count += 1
        self.message_user(
            request,
            _("%(count)d slide(s) marked as montaje.") % {"count": count},
        )

    @admin.action(description=_("Mark as coloración"))
    def mark_stage_coloracion(self, request, queryset):
        """Mark selected slides as stained."""
        count = 0
        for slide in queryset:
            slide.update_stage("coloracion")
            ProcessingLog.log_action(
                protocol=slide.protocol,
                etapa=ProcessingLog.Stage.COLORACION,
                usuario=request.user,
                slide=slide,
                observaciones="Marked by admin",
            )
            count += 1
        self.message_user(
            request,
            _("%(count)d slide(s) marked as coloración.") % {"count": count},
        )

    @admin.action(description=_("Mark as ready"))
    def mark_as_ready(self, request, queryset):
        """Mark selected slides as ready."""
        count = 0
        for slide in queryset:
            slide.mark_ready()
            count += 1
        self.message_user(
            request,
            _("%(count)d slide(s) marked as ready.") % {"count": count},
        )


@admin.register(CassetteSlide)
class CassetteSlideAdmin(admin.ModelAdmin):
    """Admin interface for CassetteSlide junction model."""

    list_display = [
        "cassette",
        "slide",
        "posicion",
        "coloracion",
        "requiere_multicorte",
        "created_at",
    ]
    list_filter = [
        "posicion",
        "requiere_multicorte",
        "created_at",
    ]
    search_fields = [
        "cassette__codigo_cassette",
        "slide__codigo_portaobjetos",
        "coloracion",
    ]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            _("Association"),
            {
                "fields": (
                    "cassette",
                    "slide",
                ),
            },
        ),
        (
            _("Details"),
            {
                "fields": (
                    "posicion",
                    "coloracion",
                    "requiere_multicorte",
                    "observaciones",
                ),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ProcessingLog)
class ProcessingLogAdmin(admin.ModelAdmin):
    """Admin interface for ProcessingLog model."""

    list_display = [
        "id",
        "protocol",
        "get_item",
        "etapa",
        "usuario",
        "fecha_inicio",
        "created_at",
    ]
    list_filter = [
        "etapa",
        "created_at",
    ]
    search_fields = [
        "protocol__protocol_number",
        "protocol__temporary_code",
        "cassette__codigo_cassette",
        "slide__codigo_portaobjetos",
        "observaciones",
    ]
    readonly_fields = [
        "protocol",
        "cassette",
        "slide",
        "etapa",
        "usuario",
        "fecha_inicio",
        "fecha_fin",
        "observaciones",
        "created_at",
    ]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            _("Log Entry"),
            {
                "fields": (
                    "protocol",
                    "etapa",
                    "usuario",
                ),
            },
        ),
        (
            _("Related Items"),
            {
                "fields": (
                    "cassette",
                    "slide",
                ),
            },
        ),
        (
            _("Timing"),
            {
                "fields": (
                    "fecha_inicio",
                    "fecha_fin",
                ),
            },
        ),
        (
            _("Notes"),
            {
                "fields": ("observaciones",),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )

    def get_item(self, obj):
        """Display the item (cassette or slide) being processed."""
        if obj.cassette:
            return format_html(
                "<strong>{}</strong>", obj.cassette.codigo_cassette
            )
        elif obj.slide:
            return format_html(
                "<strong>{}</strong>", obj.slide.codigo_portaobjetos
            )
        return "-"

    get_item.short_description = _("Item")

    def has_add_permission(self, request):
        """Processing logs should not be manually added."""
        return False

    def has_change_permission(self, request, obj=None):
        """Processing logs are read-only."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Audit logs are immutable - no deletion allowed."""
        return False


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    """Admin for email logs."""

    list_display = [
        "id",
        "email_type",
        "recipient_email",
        "subject",
        "status",
        "sent_at",
        "created_at",
    ]
    list_filter = [
        "email_type",
        "status",
        "created_at",
        "sent_at",
    ]
    search_fields = [
        "recipient_email",
        "subject",
        "celery_task_id",
    ]
    readonly_fields = [
        "email_type",
        "recipient_email",
        "recipient",
        "subject",
        "protocol",
        "work_order",
        "celery_task_id",
        "status",
        "sent_at",
        "error_message",
        "has_attachment",
        "created_at",
    ]
    fieldsets = (
        (
            _("Email Details"),
            {
                "fields": (
                    "email_type",
                    "recipient_email",
                    "recipient",
                    "subject",
                ),
            },
        ),
        (
            _("Related Objects"),
            {
                "fields": (
                    "protocol",
                    "work_order",
                ),
            },
        ),
        (
            _("Status"),
            {
                "fields": (
                    "celery_task_id",
                    "status",
                    "sent_at",
                    "error_message",
                ),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": (
                    "has_attachment",
                    "created_at",
                ),
            },
        ),
    )
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    def has_add_permission(self, request):
        """Email logs are created programmatically."""
        return False

    def has_change_permission(self, request, obj=None):
        """Email logs are read-only."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Audit logs are immutable - no deletion allowed."""
        return False


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Admin for notification preferences."""

    list_display = [
        "veterinarian",
        "notify_on_reception",
        "notify_on_report_ready",
        "notify_on_processing",
        "alternative_email",
        "updated_at",
    ]
    list_filter = [
        "notify_on_reception",
        "notify_on_processing",
        "notify_on_report_ready",
        "include_attachments",
    ]
    search_fields = [
        "veterinarian__first_name",
        "veterinarian__last_name",
        "veterinarian__email",
        "alternative_email",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
    ]
    fieldsets = (
        (
            _("Veterinarian"),
            {
                "fields": ("veterinarian",),
            },
        ),
        (
            _("Notification Preferences"),
            {
                "fields": (
                    "notify_on_reception",
                    "notify_on_processing",
                    "notify_on_report_ready",
                ),
            },
        ),
        (
            _("Email Settings"),
            {
                "fields": (
                    "alternative_email",
                    "include_attachments",
                ),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )
    date_hierarchy = "updated_at"
    ordering = ["veterinarian__last_name", "veterinarian__first_name"]
