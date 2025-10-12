import uuid
from datetime import date

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Protocol(models.Model):
    """
    Protocol submitted by veterinarians for sample analysis.
    Each protocol represents one sample submission (cytology or histopathology).
    """

    class AnalysisType(models.TextChoices):
        CYTOLOGY = "cytology", _("Citología")
        HISTOPATHOLOGY = "histopathology", _("Histopatología")

    class Sex(models.TextChoices):
        MALE = "male", _("Macho")
        FEMALE = "female", _("Hembra")
        UNKNOWN = "unknown", _("Indeterminado")

    class Status(models.TextChoices):
        DRAFT = "draft", _("Borrador")
        SUBMITTED = "submitted", _("Enviado")
        RECEIVED = "received", _("Recibido")
        PROCESSING = "processing", _("En procesamiento")
        READY = "ready", _("Listo")
        REPORT_SENT = "report_sent", _("Informe enviado")

    # External UUID for public access
    external_id = models.UUIDField(
        _("ID externo"),
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        help_text=_("UUID único para acceso público al protocolo"),
    )
    
    # Tracking codes
    temporary_code = models.CharField(
        _("código temporal"),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text=_(
            "Código de seguimiento pre-recepción (ej: TMP-CT-20241010-456)"
        ),
    )
    protocol_number = models.CharField(
        _("número de protocolo"),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Número de protocolo final (ej: HP 24/001 o CT 24/001)"),
    )

    # Basic info
    analysis_type = models.CharField(
        _("tipo de análisis"),
        max_length=20,
        choices=AnalysisType.choices,
    )

    # Relationships
    veterinarian = models.ForeignKey(
        "accounts.Veterinarian",
        on_delete=models.PROTECT,
        related_name="protocols",
        verbose_name=_("veterinario"),
    )
    work_order = models.ForeignKey(
        "protocols.WorkOrder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="protocols",
        verbose_name=_("orden de trabajo"),
    )

    # Animal/Patient data (no separate entity per design decision IV.3.3)
    species = models.CharField(_("especie"), max_length=100)
    breed = models.CharField(_("raza"), max_length=100, blank=True)
    sex = models.CharField(
        _("sexo"),
        max_length=20,
        choices=Sex.choices,
        blank=True,
    )
    age = models.CharField(
        _("edad"),
        max_length=50,
        blank=True,
        help_text=_('Ejemplo: "2 años", "6 meses"'),
    )
    animal_identification = models.CharField(
        _("identificación animal"),
        max_length=200,
        help_text=_("Nombre, número de caravana u otro identificador"),
    )
    owner_last_name = models.CharField(
        _("apellido propietario"), max_length=100, blank=True
    )
    owner_first_name = models.CharField(
        _("nombre propietario"), max_length=100, blank=True
    )

    # Clinical information
    presumptive_diagnosis = models.TextField(_("diagnóstico presuntivo"))
    clinical_history = models.TextField(_("historia clínica"), blank=True)
    academic_interest = models.BooleanField(
        _("interés académico"),
        default=False,
        help_text=_("Permitir uso con fines académicos/investigación"),
    )

    # Dates and status
    submission_date = models.DateField(_("fecha de remisión"))
    reception_date = models.DateTimeField(
        _("fecha de recepción"), null=True, blank=True
    )
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_protocols",
        verbose_name=_("recibido por"),
        help_text=_("Usuario que recepcionó la muestra"),
    )
    status = models.CharField(
        _("estado"),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    # Reception information
    class SampleCondition(models.TextChoices):
        OPTIMAL = "optimal", _("Óptima")
        ACCEPTABLE = "acceptable", _("Aceptable")
        SUBOPTIMAL = "suboptimal", _("Subóptima")
        REJECTED = "rejected", _("Rechazada")

    sample_condition = models.CharField(
        _("condición de la muestra"),
        max_length=20,
        choices=SampleCondition.choices,
        blank=True,
        help_text=_("Estado de la muestra al momento de recepción"),
    )
    reception_notes = models.TextField(
        _("observaciones de recepción"),
        blank=True,
        help_text=_("Observaciones sobre la muestra al recibirla"),
    )
    discrepancies = models.TextField(
        _("discrepancias"),
        blank=True,
        help_text=_("Diferencias entre lo declarado y lo recibido"),
    )

    # Metadata
    created_at = models.DateTimeField(_("creado el"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizado el"), auto_now=True)

    class Meta:
        verbose_name = _("protocolo")
        verbose_name_plural = _("protocolos")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["temporary_code"]),
            models.Index(fields=["protocol_number"]),
            models.Index(fields=["veterinarian", "-submission_date"]),
            models.Index(fields=["status", "-submission_date"]),
            models.Index(fields=["analysis_type", "-submission_date"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        if self.protocol_number:
            return f"{self.protocol_number} - {self.animal_identification}"
        elif self.temporary_code:
            return f"{self.temporary_code} - {self.animal_identification}"
        return f"Protocol #{self.id} - {self.animal_identification}"

    def save(self, *args, **kwargs):
        """Override save to generate temporary code on creation."""
        if (
            not self.pk
            and not self.temporary_code
            and self.status != self.Status.DRAFT
        ):
            self.temporary_code = self.generate_temporary_code()
        super().save(*args, **kwargs)

    def generate_temporary_code(self):
        """
        Generate unique temporary tracking code.
        Format: TMP-{TYPE}-{YYYYMMDD}-{ID}

        Returns:
            str: Generated temporary code
        """
        type_prefix = (
            "CT" if self.analysis_type == self.AnalysisType.CYTOLOGY else "HP"
        )
        date_str = date.today().strftime("%Y%m%d")

        # Get next ID by counting existing protocols for today
        today_protocols = Protocol.objects.filter(
            temporary_code__contains=f"TMP-{type_prefix}-{date_str}"
        ).count()
        next_id = today_protocols + 1

        return f"TMP-{type_prefix}-{date_str}-{next_id:03d}"

    def assign_protocol_number(self):
        """
        Assign final protocol number upon sample reception using ProtocolCounter.
        Format: {TYPE} {YY}/{NRO}

        Returns:
            str: Generated protocol number
        """
        if self.protocol_number:
            return self.protocol_number

        # Use ProtocolCounter to get next sequential number
        # This is defined later in the file but will be available at runtime
        from protocols.models import ProtocolCounter

        formatted_number, _ = ProtocolCounter.get_next_number(
            analysis_type=self.analysis_type,
            year=date.today().year,
        )

        self.protocol_number = formatted_number
        self.save(update_fields=["protocol_number"])
        return self.protocol_number

    def submit(self):
        """
        Submit a draft protocol.
        Generates temporary code and changes status to SUBMITTED.
        """
        if self.status != self.Status.DRAFT:
            raise ValueError("Only draft protocols can be submitted")

        if not self.temporary_code:
            self.temporary_code = self.generate_temporary_code()

        self.status = self.Status.SUBMITTED
        self.save(update_fields=["status", "temporary_code"])

    def receive(
        self,
        received_by=None,
        sample_condition=None,
        reception_notes="",
        discrepancies="",
    ):
        """
        Mark protocol as received and assign final protocol number.

        Args:
            received_by: User who received the sample
            sample_condition: Condition of the sample
            reception_notes: Notes about the reception
            discrepancies: Any discrepancies found
        """
        if self.status not in [self.Status.SUBMITTED, self.Status.DRAFT]:
            raise ValueError(
                "Only submitted or draft protocols can be received"
            )

        self.reception_date = timezone.now()
        self.received_by = received_by
        self.sample_condition = (
            sample_condition or self.SampleCondition.OPTIMAL
        )
        self.reception_notes = reception_notes
        self.discrepancies = discrepancies
        self.status = self.Status.RECEIVED

        if not self.protocol_number:
            self.assign_protocol_number()

        self.save(
            update_fields=[
                "reception_date",
                "received_by",
                "sample_condition",
                "reception_notes",
                "discrepancies",
                "status",
            ]
        )

    def get_owner_full_name(self):
        """Return owner's full name."""
        if self.owner_first_name and self.owner_last_name:
            return f"{self.owner_first_name} {self.owner_last_name}".strip()
        return self.owner_first_name or self.owner_last_name or ""

    @property
    def is_editable(self):
        """Check if protocol can be edited by veterinarian."""
        return self.status == self.Status.DRAFT

    @property
    def is_deletable(self):
        """Check if protocol can be deleted by veterinarian."""
        return self.status == self.Status.DRAFT


class CytologySample(models.Model):
    """
    Cytology sample information.
    Each protocol of type CYTOLOGY has one associated CytologySample.
    """

    protocol = models.OneToOneField(
        Protocol,
        on_delete=models.CASCADE,
        related_name="cytology_sample",
        verbose_name=_("protocolo"),
    )
    veterinarian = models.ForeignKey(
        "accounts.Veterinarian",
        on_delete=models.PROTECT,
        related_name="cytology_samples",
        verbose_name=_("veterinario"),
    )

    # Sample details
    technique_used = models.CharField(
        _("técnica utilizada"),
        max_length=200,
        help_text=_(
            "Ej: Punción aspiración con aguja fina (PAAF), hisopado, raspado, etc."
        ),
    )
    sampling_site = models.CharField(
        _("sitio de muestreo"),
        max_length=200,
        help_text=_("Ubicación anatómica de la muestra"),
    )
    number_of_slides = models.IntegerField(
        _("número de portaobjetos"),
        default=1,
        help_text=_("Cantidad de portaobjetos enviados"),
    )
    number_slides_received = models.IntegerField(
        _("número de portaobjetos recibidos"),
        null=True,
        blank=True,
        help_text=_("Cantidad real de portaobjetos recibidos"),
    )
    observations = models.TextField(_("observaciones"), blank=True)

    # Metadata
    created_at = models.DateTimeField(_("creado el"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizado el"), auto_now=True)

    class Meta:
        verbose_name = _("muestra de citología")
        verbose_name_plural = _("muestras de citología")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Cytology: {self.sampling_site} ({self.technique_used})"


class HistopathologySample(models.Model):
    """
    Histopathology sample information.
    Each protocol of type HISTOPATHOLOGY has one associated HistopathologySample.
    """

    protocol = models.OneToOneField(
        Protocol,
        on_delete=models.CASCADE,
        related_name="histopathology_sample",
        verbose_name=_("protocolo"),
    )
    veterinarian = models.ForeignKey(
        "accounts.Veterinarian",
        on_delete=models.PROTECT,
        related_name="histopathology_samples",
        verbose_name=_("veterinario"),
    )

    # Sample details
    material_submitted = models.TextField(
        _("material remitido"),
        help_text=_("Descripción de las muestras de tejido/órganos"),
    )
    number_of_containers = models.IntegerField(
        _("número de frascos"),
        default=1,
        help_text=_("Cantidad de frascos/contenedores enviados"),
    )
    number_jars_received = models.IntegerField(
        _("número de frascos recibidos"),
        null=True,
        blank=True,
        help_text=_("Cantidad real de frascos recibidos"),
    )
    preservation = models.CharField(
        _("conservación"),
        max_length=100,
        default="Formol 10%",
        help_text=_("Método de conservación utilizado"),
    )
    observations = models.TextField(_("observaciones"), blank=True)

    # Metadata
    created_at = models.DateTimeField(_("creado el"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizado el"), auto_now=True)

    class Meta:
        verbose_name = _("muestra de histopatología")
        verbose_name_plural = _("muestras de histopatología")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Histopathology: {self.material_submitted[:50]}"


class PricingCatalog(models.Model):
    """
    Pricing catalog for laboratory services.
    Maintains current prices for different service types.
    """

    service_type = models.CharField(
        _("tipo de servicio"),
        max_length=100,
        unique=True,
        help_text=_("Identificador único del servicio"),
    )
    description = models.CharField(
        _("descripción"),
        max_length=500,
        help_text=_("Descripción del servicio"),
    )
    price = models.DecimalField(
        _("precio"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Precio en USD"),
    )
    valid_from = models.DateField(
        _("vigente desde"),
        help_text=_("Fecha desde la cual este precio es válido"),
    )
    valid_until = models.DateField(
        _("vigente hasta"),
        null=True,
        blank=True,
        help_text=_("Fecha hasta la cual este precio es válido"),
    )
    observations = models.TextField(
        _("observaciones"),
        blank=True,
    )
    created_at = models.DateTimeField(_("creado el"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizado el"), auto_now=True)

    class Meta:
        verbose_name = _("catálogo de precios")
        verbose_name_plural = _("catálogos de precios")
        ordering = ["service_type"]
        indexes = [
            models.Index(fields=["service_type"]),
            models.Index(fields=["valid_from", "valid_until"]),
        ]

    def __str__(self):
        return f"{self.description} - ${self.price}"

    @classmethod
    def get_current_price(cls, service_type):
        """
        Get current valid price for a service type.

        Args:
            service_type: Service type identifier

        Returns:
            PricingCatalog instance or None
        """
        today = date.today()
        return cls.objects.filter(
            service_type=service_type,
            valid_from__lte=today,
        ).filter(
            models.Q(valid_until__gte=today) | models.Q(valid_until__isnull=True)
        ).first()

    def is_valid(self, check_date=None):
        """Check if price is valid on given date."""
        if check_date is None:
            check_date = date.today()
        
        if check_date < self.valid_from:
            return False
        
        return not (self.valid_until and check_date > self.valid_until)


class WorkOrderCounter(models.Model):
    """
    Track sequential work order numbering per year.
    Ensures unique, sequential work order numbers.
    """

    year = models.IntegerField(
        _("año"),
        unique=True,
        help_text=_("Año para el contador"),
    )
    last_number = models.IntegerField(
        _("último número"),
        default=0,
        help_text=_("Último número de orden de trabajo asignado"),
    )

    class Meta:
        verbose_name = _("contador de orden de trabajo")
        verbose_name_plural = _("contadores de orden de trabajo")
        indexes = [
            models.Index(fields=["year"]),
        ]

    def __str__(self):
        return f"OT {self.year}: {self.last_number}"

    @classmethod
    def get_next_number(cls, year=None):
        """
        Get the next work order number for a given year.

        Args:
            year: Year for the counter (defaults to current year)

        Returns:
            tuple: (formatted_number, counter_instance)
        """
        from django.db import transaction

        if year is None:
            year = date.today().year

        with transaction.atomic():
            # Get or create counter for this year
            counter, created = cls.objects.select_for_update().get_or_create(
                year=year,
                defaults={"last_number": 0},
            )

            # Increment counter
            counter.last_number += 1
            counter.save()

            # Format work order number: OT-YYYY-NNN
            formatted_number = f"OT-{year}-{counter.last_number:03d}"

            return formatted_number, counter


class WorkOrder(models.Model):
    """
    Work Order (Orden de Trabajo) for billing laboratory services.
    Groups one or more protocols for invoicing.
    """

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", _("Pendiente")
        PARTIAL = "partial", _("Pagado Parcial")
        PAID = "paid", _("Pagado Completo")

    class Status(models.TextChoices):
        DRAFT = "draft", _("Borrador")
        ISSUED = "issued", _("Emitida")
        SENT = "sent", _("Enviada")
        INVOICED = "invoiced", _("Facturada")

    class IVACondition(models.TextChoices):
        RESPONSABLE_INSCRIPTO = "responsable_inscripto", _("Responsable Inscripto")
        MONOTRIBUTISTA = "monotributista", _("Monotributista")
        EXENTO = "exento", _("Exento")

    # Basic identification
    order_number = models.CharField(
        _("número de orden"),
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_("Número único de orden de trabajo (ej: OT-2024-001)"),
    )
    issue_date = models.DateField(
        _("fecha de emisión"),
        default=date.today,
        help_text=_("Fecha de emisión de la orden de trabajo"),
    )
    veterinarian = models.ForeignKey(
        "accounts.Veterinarian",
        on_delete=models.PROTECT,
        related_name="work_orders",
        verbose_name=_("veterinario"),
    )

    # Financial information
    total_amount = models.DecimalField(
        _("monto total"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("Monto total de la orden"),
    )
    advance_payment = models.DecimalField(
        _("pago adelantado"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("Pago adelantado recibido"),
    )
    balance_due = models.DecimalField(
        _("saldo pendiente"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("Saldo pendiente de pago"),
    )
    payment_status = models.CharField(
        _("estado de pago"),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    # Billing details
    billing_name = models.CharField(
        _("nombre de facturación"),
        max_length=200,
        blank=True,
        help_text=_("Nombre para facturación (si difiere del veterinario)"),
    )
    cuit_cuil = models.CharField(
        _("CUIT/CUIL"),
        max_length=20,
        blank=True,
        help_text=_("CUIT o CUIL del cliente"),
    )
    iva_condition = models.CharField(
        _("condición IVA"),
        max_length=30,
        choices=IVACondition.choices,
        blank=True,
    )

    # Files
    pdf_path = models.CharField(
        _("ruta del PDF"),
        max_length=500,
        blank=True,
        help_text=_("Ruta del archivo PDF de la orden"),
    )

    # Status tracking
    status = models.CharField(
        _("estado"),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    sent_date = models.DateTimeField(
        _("fecha de envío"),
        null=True,
        blank=True,
        help_text=_("Fecha en que se envió la orden a finanzas"),
    )
    invoiced_date = models.DateTimeField(
        _("fecha de facturación"),
        null=True,
        blank=True,
        help_text=_("Fecha en que se facturó"),
    )

    # Additional information
    observations = models.TextField(
        _("observaciones"),
        blank=True,
    )

    # Metadata
    created_at = models.DateTimeField(_("creado el"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizado el"), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_work_orders",
        verbose_name=_("creado por"),
    )

    class Meta:
        verbose_name = _("orden de trabajo")
        verbose_name_plural = _("órdenes de trabajo")
        ordering = ["-issue_date", "-created_at"]
        indexes = [
            models.Index(fields=["order_number"]),
            models.Index(fields=["veterinarian", "-issue_date"]),
            models.Index(fields=["status", "-issue_date"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.order_number} - {self.veterinarian}"

    def save(self, *args, **kwargs):
        """Override save to generate order number and calculate balance."""
        # Generate order number if not set
        if not self.pk and not self.order_number:
            self.order_number = self.generate_order_number()
        
        # Calculate balance due
        self.balance_due = self.total_amount - self.advance_payment
        
        # Update payment status
        if self.balance_due <= 0:
            self.payment_status = self.PaymentStatus.PAID
        elif self.advance_payment > 0:
            self.payment_status = self.PaymentStatus.PARTIAL
        else:
            self.payment_status = self.PaymentStatus.PENDING
        
        super().save(*args, **kwargs)

    def generate_order_number(self):
        """
        Generate unique work order number.
        Format: OT-YYYY-NNN

        Returns:
            str: Generated order number
        """
        formatted_number, _ = WorkOrderCounter.get_next_number(
            year=date.today().year
        )
        return formatted_number

    def can_edit(self):
        """Check if work order can be edited."""
        return self.status == self.Status.DRAFT

    def can_delete(self):
        """Check if work order can be deleted."""
        return self.status == self.Status.DRAFT

    def issue(self):
        """Mark work order as issued."""
        if self.status != self.Status.DRAFT:
            raise ValueError("Only draft work orders can be issued")
        self.status = self.Status.ISSUED
        self.save(update_fields=["status"])

    def mark_as_sent(self):
        """Mark work order as sent to finance."""
        if self.status not in [self.Status.ISSUED, self.Status.DRAFT]:
            raise ValueError("Only draft or issued work orders can be sent")
        self.status = self.Status.SENT
        self.sent_date = timezone.now()
        self.save(update_fields=["status", "sent_date"])

    def mark_as_invoiced(self):
        """Mark work order as invoiced."""
        if self.status != self.Status.SENT:
            raise ValueError("Only sent work orders can be marked as invoiced")
        self.status = self.Status.INVOICED
        self.invoiced_date = timezone.now()
        self.save(update_fields=["status", "invoiced_date"])

    def get_billing_name(self):
        """Get the name to use for billing."""
        if self.billing_name:
            return self.billing_name
        return self.veterinarian.user.get_full_name()

    def calculate_total(self):
        """Calculate total from service line items."""
        total = sum(
            service.subtotal - service.discount
            for service in self.services.all()
        )
        return total

    def generate_pdf_filename(self):
        """Generate standardized PDF filename."""
        order_num = self.order_number.replace("-", "_")
        return f"{order_num}.pdf"


class WorkOrderService(models.Model):
    """
    Service line item for a work order.
    Each line represents one protocol's service with pricing.
    """

    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name="services",
        verbose_name=_("orden de trabajo"),
    )
    protocol = models.ForeignKey(
        Protocol,
        on_delete=models.PROTECT,
        related_name="work_order_services",
        verbose_name=_("protocolo"),
    )
    
    # Service details
    description = models.CharField(
        _("descripción"),
        max_length=500,
        help_text=_("Descripción del servicio"),
    )
    service_type = models.CharField(
        _("tipo de servicio"),
        max_length=100,
        help_text=_("Tipo de servicio prestado"),
    )
    quantity = models.IntegerField(
        _("cantidad"),
        default=1,
    )
    unit_price = models.DecimalField(
        _("precio unitario"),
        max_digits=10,
        decimal_places=2,
    )
    subtotal = models.DecimalField(
        _("subtotal"),
        max_digits=10,
        decimal_places=2,
    )
    discount = models.DecimalField(
        _("descuento"),
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    class Meta:
        verbose_name = _("servicio de orden de trabajo")
        verbose_name_plural = _("servicios de orden de trabajo")
        ordering = ["id"]
        indexes = [
            models.Index(fields=["work_order"]),
            models.Index(fields=["protocol"]),
        ]

    def __str__(self):
        return f"{self.work_order.order_number} - {self.description}"

    def save(self, *args, **kwargs):
        """Override save to calculate subtotal."""
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class ProtocolStatusHistory(models.Model):
    """
    Track status changes for protocols.
    Provides timeline of protocol progression.
    """

    protocol = models.ForeignKey(
        Protocol,
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name=_("protocolo"),
    )
    status = models.CharField(
        _("estado"),
        max_length=20,
        choices=Protocol.Status.choices,
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="protocol_status_changes",
        verbose_name=_("cambiado por"),
    )
    description = models.TextField(_("descripción"), blank=True)
    changed_at = models.DateTimeField(_("cambiado el"), auto_now_add=True)

    class Meta:
        verbose_name = _("historial de estado del protocolo")
        verbose_name_plural = _("historiales de estado del protocolo")
        ordering = ["-changed_at"]
        indexes = [
            models.Index(fields=["protocol", "-changed_at"]),
        ]

    def __str__(self):
        return f"{self.protocol} - {self.get_status_display()} at {self.changed_at}"

    @classmethod
    def log_status_change(
        cls, protocol, new_status, changed_by=None, description=""
    ):
        """
        Helper method to log status changes.

        Args:
            protocol: Protocol instance
            new_status: New status value
            changed_by: User who made the change
            description: Optional description of the change
        """
        return cls.objects.create(
            protocol=protocol,
            status=new_status,
            changed_by=changed_by,
            description=description,
        )


class ReceptionLog(models.Model):
    """
    Track all reception actions and events.
    Provides audit trail for sample reception process.
    """

    class Action(models.TextChoices):
        RECEIVED = "received", _("Recibido")
        REJECTED = "rejected", _("Rechazado")
        DISCREPANCY_REPORTED = (
            "discrepancy_reported",
            _("Discrepancia reportada"),
        )
        CONDITION_NOTED = "condition_noted", _("Condición anotada")

    protocol = models.ForeignKey(
        Protocol,
        on_delete=models.CASCADE,
        related_name="reception_logs",
        verbose_name=_("protocolo"),
    )
    action = models.CharField(
        _("acción"),
        max_length=100,
        choices=Action.choices,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="reception_actions",
        verbose_name=_("usuario"),
    )
    notes = models.TextField(
        _("observaciones"),
        blank=True,
    )
    created_at = models.DateTimeField(_("creado el"), auto_now_add=True)

    class Meta:
        verbose_name = _("registro de recepción")
        verbose_name_plural = _("registros de recepción")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["protocol", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.protocol} - {self.get_action_display()} - {self.created_at}"

    @classmethod
    def log_action(cls, protocol, action, user=None, notes=""):
        """
        Helper method to log reception actions.

        Args:
            protocol: Protocol instance
            action: Action type
            user: User who performed the action
            notes: Optional notes
        """
        return cls.objects.create(
            protocol=protocol,
            action=action,
            user=user,
            notes=notes,
        )


class ProtocolCounter(models.Model):
    """
    Track sequential protocol numbering per type and year.
    Ensures unique, sequential protocol numbers.
    """

    analysis_type = models.CharField(
        _("tipo de análisis"),
        max_length=20,
        choices=Protocol.AnalysisType.choices,
    )
    year = models.IntegerField(
        _("año"),
        help_text=_("Año para el contador"),
    )
    last_number = models.IntegerField(
        _("último número"),
        default=0,
        help_text=_("Último número de protocolo asignado"),
    )

    class Meta:
        verbose_name = _("contador de protocolo")
        verbose_name_plural = _("contadores de protocolo")
        unique_together = [["analysis_type", "year"]]
        indexes = [
            models.Index(fields=["analysis_type", "year"]),
        ]

    def __str__(self):
        prefix = (
            "CT"
            if self.analysis_type == Protocol.AnalysisType.CYTOLOGY
            else "HP"
        )
        return f"{prefix} {self.year}: {self.last_number}"

    @classmethod
    def get_next_number(cls, analysis_type, year=None):
        """
        Get the next protocol number for a given type and year.

        Args:
            analysis_type: Type of analysis (cytology or histopathology)
            year: Year for the counter (defaults to current year)

        Returns:
            tuple: (formatted_number, counter_instance)
        """
        from django.db import transaction

        if year is None:
            year = date.today().year

        with transaction.atomic():
            # Get or create counter for this type and year
            counter, created = cls.objects.select_for_update().get_or_create(
                analysis_type=analysis_type,
                year=year,
                defaults={"last_number": 0},
            )

            # Increment counter
            counter.last_number += 1
            counter.save()

            # Format protocol number
            prefix = (
                "CT"
                if analysis_type == Protocol.AnalysisType.CYTOLOGY
                else "HP"
            )
            year_short = str(year)[-2:]
            formatted_number = (
                f"{prefix} {year_short}/{counter.last_number:03d}"
            )

            return formatted_number, counter


class Cassette(models.Model):
    """
    Cassette for histopathology processing.
    Each cassette contains tissue material from a histopathology sample.
    """

    class CassetteType(models.TextChoices):
        NORMAL = "normal", _("Normal")
        MULTICORTE = "multicorte", _("Multicorte")
        COLORACION_ESPECIAL = "coloracion_especial", _("Coloración especial")

    class CassetteColor(models.TextChoices):
        BLANCO = "blanco", _("Blanco")
        AMARILLO = "amarillo", _("Amarillo")
        NARANJA = "naranja", _("Naranja")

    class Status(models.TextChoices):
        PENDIENTE = "pendiente", _("Pendiente")
        EN_PROCESO = "en_proceso", _("En proceso")
        COMPLETADO = "completado", _("Completado")

    histopathology_sample = models.ForeignKey(
        HistopathologySample,
        on_delete=models.CASCADE,
        related_name="cassettes",
        verbose_name=_("muestra de histopatología"),
    )
    codigo_cassette = models.CharField(
        _("código de cassette"),
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_("Ej: HP 24/123-C1"),
    )
    material_incluido = models.TextField(
        _("material incluido"),
        help_text=_("Descripción del tejido incluido en el cassette"),
    )
    tipo_cassette = models.CharField(
        _("tipo de cassette"),
        max_length=50,
        choices=CassetteType.choices,
        default=CassetteType.NORMAL,
    )
    color_cassette = models.CharField(
        _("color del cassette"),
        max_length=20,
        choices=CassetteColor.choices,
        default=CassetteColor.BLANCO,
    )

    # Processing stages
    fecha_encasetado = models.DateTimeField(
        _("fecha de encasetado"),
        null=True,
        blank=True,
        help_text=_("Fecha en que se colocó el tejido en el cassette"),
    )
    fecha_fijacion = models.DateTimeField(
        _("fecha de fijación"),
        null=True,
        blank=True,
        help_text=_("Fecha de inicio de fijación"),
    )
    fecha_inclusion = models.DateTimeField(
        _("fecha de inclusión"),
        null=True,
        blank=True,
        help_text=_("Fecha de inclusión en parafina"),
    )
    fecha_entacado = models.DateTimeField(
        _("fecha de entacado"),
        null=True,
        blank=True,
        help_text=_("Fecha de creación del taco de parafina"),
    )

    # Status and observations
    estado = models.CharField(
        _("estado"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDIENTE,
    )
    observaciones = models.TextField(_("observaciones"), blank=True)

    # Metadata
    created_at = models.DateTimeField(_("creado el"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizado el"), auto_now=True)

    class Meta:
        verbose_name = _("cassette")
        verbose_name_plural = _("cassettes")
        ordering = ["codigo_cassette"]
        indexes = [
            models.Index(fields=["codigo_cassette"]),
            models.Index(fields=["histopathology_sample", "created_at"]),
            models.Index(fields=["estado"]),
        ]

    def __str__(self):
        return f"{self.codigo_cassette}"

    def save(self, *args, **kwargs):
        """Override save to generate cassette code if not set."""
        if not self.codigo_cassette:
            self.codigo_cassette = self.generate_cassette_code()
        super().save(*args, **kwargs)

    def generate_cassette_code(self):
        """
        Generate unique cassette code.
        Format: {PROTOCOL_NUMBER}-C{CASSETTE_NUMBER}

        Returns:
            str: Generated cassette code
        """
        protocol_number = self.histopathology_sample.protocol.protocol_number
        if not protocol_number:
            raise ValueError(
                "Protocol must have a protocol_number before creating cassettes"
            )

        # Get next cassette number for this protocol
        existing_cassettes = Cassette.objects.filter(
            histopathology_sample=self.histopathology_sample
        ).count()
        next_number = existing_cassettes + 1

        return f"{protocol_number}-C{next_number}"

    def update_stage(self, stage, timestamp=None):
        """
        Update a processing stage with timestamp.

        Args:
            stage: Stage name (encasetado, fijacion, inclusion, entacado)
            timestamp: Datetime for the stage (defaults to now)
        """
        if timestamp is None:
            timestamp = timezone.now()

        stage_fields = {
            "encasetado": "fecha_encasetado",
            "fijacion": "fecha_fijacion",
            "inclusion": "fecha_inclusion",
            "entacado": "fecha_entacado",
        }

        if stage not in stage_fields:
            raise ValueError(f"Invalid stage: {stage}")

        setattr(self, stage_fields[stage], timestamp)

        # Update status
        if stage == "entacado":
            self.estado = self.Status.COMPLETADO
        else:
            self.estado = self.Status.EN_PROCESO

        self.save(update_fields=[stage_fields[stage], "estado", "updated_at"])


class Slide(models.Model):
    """
    Portaobjetos (slide) for microscopic analysis.
    Can be associated with cytology samples directly or with cassettes via junction table.
    """

    class Status(models.TextChoices):
        PENDIENTE = "pendiente", _("Pendiente")
        MONTADO = "montado", _("Montado")
        COLOREADO = "coloreado", _("Coloreado")
        LISTO = "listo", _("Listo")

    class Quality(models.TextChoices):
        EXCELENTE = "excelente", _("Excelente")
        BUENA = "buena", _("Buena")
        ACEPTABLE = "aceptable", _("Aceptable")
        DEFICIENTE = "deficiente", _("Deficiente")

    protocol = models.ForeignKey(
        Protocol,
        on_delete=models.CASCADE,
        related_name="slides",
        verbose_name=_("protocolo"),
    )
    codigo_portaobjetos = models.CharField(
        _("código de portaobjetos"),
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_("Ej: HP 24/123-S1 o CT 24/089-S1"),
    )

    # For cytology (direct link to sample)
    cytology_sample = models.ForeignKey(
        CytologySample,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="slides",
        verbose_name=_("muestra de citología"),
    )

    # Processing info
    campo = models.IntegerField(
        _("campo"),
        null=True,
        blank=True,
        help_text=_("Número de campo del portaobjetos"),
    )
    tecnica_coloracion = models.CharField(
        _("técnica de coloración"),
        max_length=200,
        default="Hematoxilina-Eosina",
        help_text=_("Técnica de coloración utilizada"),
    )
    fecha_montaje = models.DateTimeField(
        _("fecha de montaje"),
        null=True,
        blank=True,
    )
    fecha_coloracion = models.DateTimeField(
        _("fecha de coloración"),
        null=True,
        blank=True,
    )
    calidad = models.CharField(
        _("calidad"),
        max_length=20,
        choices=Quality.choices,
        blank=True,
        help_text=_("Calidad del portaobjetos"),
    )

    # Status
    estado = models.CharField(
        _("estado"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDIENTE,
    )
    observaciones = models.TextField(_("observaciones"), blank=True)

    # Metadata
    created_at = models.DateTimeField(_("creado el"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizado el"), auto_now=True)

    class Meta:
        verbose_name = _("portaobjetos")
        verbose_name_plural = _("portaobjetos")
        ordering = ["codigo_portaobjetos"]
        indexes = [
            models.Index(fields=["codigo_portaobjetos"]),
            models.Index(fields=["protocol", "created_at"]),
            models.Index(fields=["estado"]),
        ]

    def __str__(self):
        return f"{self.codigo_portaobjetos}"

    def save(self, *args, **kwargs):
        """Override save to generate slide code if not set."""
        if not self.codigo_portaobjetos:
            self.codigo_portaobjetos = self.generate_slide_code()
        super().save(*args, **kwargs)

    def generate_slide_code(self):
        """
        Generate unique slide code.
        Format: {PROTOCOL_NUMBER}-S{SLIDE_NUMBER}

        Returns:
            str: Generated slide code
        """
        protocol_number = self.protocol.protocol_number
        if not protocol_number:
            raise ValueError(
                "Protocol must have a protocol_number before creating slides"
            )

        # Get next slide number for this protocol
        existing_slides = Slide.objects.filter(protocol=self.protocol).count()
        next_number = existing_slides + 1

        return f"{protocol_number}-S{next_number}"

    def update_stage(self, stage, timestamp=None):
        """
        Update a processing stage with timestamp.

        Args:
            stage: Stage name (montaje, coloracion)
            timestamp: Datetime for the stage (defaults to now)
        """
        if timestamp is None:
            timestamp = timezone.now()

        stage_fields = {
            "montaje": "fecha_montaje",
            "coloracion": "fecha_coloracion",
        }

        if stage not in stage_fields:
            raise ValueError(f"Invalid stage: {stage}")

        setattr(self, stage_fields[stage], timestamp)

        # Update status
        if stage == "montaje":
            self.estado = self.Status.MONTADO
        elif stage == "coloracion":
            self.estado = self.Status.COLOREADO

        self.save(update_fields=[stage_fields[stage], "estado", "updated_at"])

    def mark_ready(self):
        """Mark slide as ready for analysis."""
        self.estado = self.Status.LISTO
        self.save(update_fields=["estado", "updated_at"])


class CassetteSlide(models.Model):
    """
    Junction table for Many-to-Many relationship between Cassettes and Slides.
    Allows multiple cassettes to be mounted on one slide.
    """

    class Position(models.TextChoices):
        SUPERIOR = "superior", _("Superior")
        INFERIOR = "inferior", _("Inferior")
        COMPLETO = "completo", _("Completo")

    cassette = models.ForeignKey(
        Cassette,
        on_delete=models.CASCADE,
        related_name="cassette_slides",
        verbose_name=_("cassette"),
    )
    slide = models.ForeignKey(
        Slide,
        on_delete=models.CASCADE,
        related_name="cassette_slides",
        verbose_name=_("portaobjetos"),
    )
    posicion = models.CharField(
        _("posición"),
        max_length=20,
        choices=Position.choices,
        default=Position.COMPLETO,
        help_text=_("Posición del cassette en el portaobjetos"),
    )
    coloracion = models.CharField(
        _("coloración"),
        max_length=200,
        blank=True,
        help_text=_(
            "Coloración específica para este cassette en este portaobjetos"
        ),
    )
    requiere_multicorte = models.BooleanField(
        _("requiere multicorte"),
        default=False,
    )
    observaciones = models.TextField(_("observaciones"), blank=True)
    created_at = models.DateTimeField(_("creado el"), auto_now_add=True)

    class Meta:
        verbose_name = _("cassette-portaobjetos")
        verbose_name_plural = _("cassette-portaobjetos")
        unique_together = [["cassette", "slide"]]
        indexes = [
            models.Index(fields=["cassette"]),
            models.Index(fields=["slide"]),
        ]

    def __str__(self):
        return f"{self.cassette.codigo_cassette} → {self.slide.codigo_portaobjetos}"


class ProcessingLog(models.Model):
    """
    Log all processing actions and events.
    Provides complete audit trail for sample processing.
    """

    class Stage(models.TextChoices):
        ENCASETADO = "encasetado", _("Encasetado")
        FIJACION = "fijacion", _("Fijación")
        INCLUSION = "inclusion", _("Inclusión")
        ENTACADO = "entacado", _("Entacado")
        CORTE = "corte", _("Corte")
        MONTAJE = "montaje", _("Montaje")
        COLORACION = "coloracion", _("Coloración")

    protocol = models.ForeignKey(
        Protocol,
        on_delete=models.CASCADE,
        related_name="processing_logs",
        verbose_name=_("protocolo"),
    )
    cassette = models.ForeignKey(
        Cassette,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="processing_logs",
        verbose_name=_("cassette"),
    )
    slide = models.ForeignKey(
        Slide,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="processing_logs",
        verbose_name=_("portaobjetos"),
    )
    etapa = models.CharField(
        _("etapa"),
        max_length=50,
        choices=Stage.choices,
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="processing_actions",
        verbose_name=_("usuario"),
    )
    fecha_inicio = models.DateTimeField(
        _("fecha de inicio"),
        default=timezone.now,
    )
    fecha_fin = models.DateTimeField(
        _("fecha de fin"),
        null=True,
        blank=True,
    )
    observaciones = models.TextField(_("observaciones"), blank=True)
    created_at = models.DateTimeField(_("creado el"), auto_now_add=True)

    class Meta:
        verbose_name = _("registro de procesamiento")
        verbose_name_plural = _("registros de procesamiento")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["protocol", "-created_at"]),
            models.Index(fields=["cassette", "-created_at"]),
            models.Index(fields=["slide", "-created_at"]),
            models.Index(fields=["usuario", "-created_at"]),
        ]

    def __str__(self):
        if self.cassette:
            return f"{self.protocol} - {self.cassette.codigo_cassette} - {self.get_etapa_display()}"
        elif self.slide:
            return f"{self.protocol} - {self.slide.codigo_portaobjetos} - {self.get_etapa_display()}"
        return f"{self.protocol} - {self.get_etapa_display()}"

    @classmethod
    def log_action(
        cls,
        protocol,
        etapa,
        usuario=None,
        cassette=None,
        slide=None,
        observaciones="",
    ):
        """
        Helper method to log processing actions.

        Args:
            protocol: Protocol instance
            etapa: Processing stage
            usuario: User who performed the action
            cassette: Optional cassette instance
            slide: Optional slide instance
            observaciones: Optional observations
        """
        return cls.objects.create(
            protocol=protocol,
            etapa=etapa,
            usuario=usuario,
            cassette=cassette,
            slide=slide,
            observaciones=observaciones,
        )


class Report(models.Model):
    """
    Pathology report generated by histopathologist.
    Contains observations, diagnosis, and conclusions for a protocol.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", _("Borrador")
        FINALIZED = "finalized", _("Finalizado")
        SENT = "sent", _("Enviado")

    class EmailStatus(models.TextChoices):
        PENDING = "pending", _("Pendiente")
        SENT = "sent", _("Enviado")
        FAILED = "failed", _("Fallido")
        BOUNCED = "bounced", _("Rebotado")

    protocol = models.ForeignKey(
        Protocol,
        on_delete=models.PROTECT,
        related_name="reports",
        verbose_name=_("protocolo"),
    )
    histopathologist = models.ForeignKey(
        "accounts.Histopathologist",
        on_delete=models.PROTECT,
        related_name="reports",
        verbose_name=_("histopatólogo"),
    )
    veterinarian = models.ForeignKey(
        "accounts.Veterinarian",
        on_delete=models.PROTECT,
        related_name="received_reports",
        verbose_name=_("veterinario"),
    )

    # Content
    macroscopic_observations = models.TextField(
        _("observaciones macroscópicas"),
        blank=True,
        help_text=_("Descripción macroscópica del material recibido"),
    )
    microscopic_observations = models.TextField(
        _("observaciones microscópicas"),
        blank=True,
        help_text=_("Observaciones microscópicas generales"),
    )
    diagnosis = models.TextField(
        _("diagnóstico"),
        help_text=_("Diagnóstico patológico final"),
    )
    comments = models.TextField(
        _("comentarios"),
        blank=True,
        help_text=_("Comentarios adicionales sobre el caso"),
    )
    recommendations = models.TextField(
        _("recomendaciones"),
        blank=True,
        help_text=_("Recomendaciones clínicas para el veterinario"),
    )

    # Metadata
    report_date = models.DateField(
        _("fecha del informe"),
        default=date.today,
        help_text=_("Fecha de emisión del informe"),
    )
    version = models.IntegerField(
        _("versión"),
        default=1,
        help_text=_("Número de versión del informe"),
    )
    status = models.CharField(
        _("estado"),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    # Files
    pdf_path = models.CharField(
        _("ruta del PDF"),
        max_length=500,
        blank=True,
        help_text=_("Ruta del archivo PDF generado"),
    )
    pdf_hash = models.CharField(
        _("hash del PDF"),
        max_length=64,
        blank=True,
        help_text=_("SHA-256 hash para verificar integridad"),
    )

    # Sending info
    sent_date = models.DateTimeField(
        _("fecha de envío"),
        null=True,
        blank=True,
    )
    sent_to_email = models.EmailField(
        _("enviado a"),
        blank=True,
        help_text=_("Email al que se envió el informe"),
    )
    email_status = models.CharField(
        _("estado del email"),
        max_length=20,
        choices=EmailStatus.choices,
        default=EmailStatus.PENDING,
    )
    email_error = models.TextField(
        _("error de email"),
        blank=True,
        help_text=_("Detalles del error si el envío falló"),
    )

    # Timestamps
    created_at = models.DateTimeField(_("creado el"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizado el"), auto_now=True)

    class Meta:
        verbose_name = _("informe")
        verbose_name_plural = _("informes")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["protocol"]),
            models.Index(fields=["histopathologist", "-created_at"]),
            models.Index(fields=["veterinarian", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["-report_date"]),
        ]

    def __str__(self):
        return f"Informe {self.protocol.protocol_number} - v{self.version}"

    def generate_pdf_filename(self):
        """Generate standardized PDF filename."""
        protocol_num = self.protocol.protocol_number.replace(" ", "_").replace("/", "_")
        return f"Informe_{protocol_num}_v{self.version}.pdf"

    def can_edit(self):
        """Check if report can be edited."""
        return self.status == self.Status.DRAFT

    def can_delete(self):
        """Check if report can be deleted."""
        return self.status == self.Status.DRAFT

    def finalize(self):
        """Mark report as finalized."""
        if self.status != self.Status.DRAFT:
            raise ValueError("Only draft reports can be finalized")
        self.status = self.Status.FINALIZED
        self.save(update_fields=["status"])

    def mark_as_sent(self, email):
        """Mark report as sent."""
        self.status = self.Status.SENT
        self.sent_date = timezone.now()
        self.sent_to_email = email
        self.email_status = self.EmailStatus.SENT
        self.save(update_fields=["status", "sent_date", "sent_to_email", "email_status"])


class CassetteObservation(models.Model):
    """
    Microscopic observations for a specific cassette in a report.
    Each cassette can have detailed observations and partial diagnosis.
    """

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="cassette_observations",
        verbose_name=_("informe"),
    )
    cassette = models.ForeignKey(
        Cassette,
        on_delete=models.CASCADE,
        related_name="observations",
        verbose_name=_("cassette"),
    )
    observations = models.TextField(
        _("observaciones"),
        help_text=_("Observaciones microscópicas del cassette"),
    )
    partial_diagnosis = models.TextField(
        _("diagnóstico parcial"),
        blank=True,
        help_text=_("Diagnóstico específico para este cassette"),
    )
    order = models.IntegerField(
        _("orden"),
        default=0,
        help_text=_("Orden de presentación en el informe"),
    )

    created_at = models.DateTimeField(_("creado el"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizado el"), auto_now=True)

    class Meta:
        verbose_name = _("observación de cassette")
        verbose_name_plural = _("observaciones de cassettes")
        ordering = ["order", "cassette__codigo_cassette"]
        indexes = [
            models.Index(fields=["report", "order"]),
            models.Index(fields=["cassette"]),
        ]
        unique_together = [["report", "cassette"]]

    def __str__(self):
        return f"{self.report} - {self.cassette.codigo_cassette}"


class ReportImage(models.Model):
    """
    Microscopy images attached to a report.
    Can be associated with specific cassettes or slides.
    """

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("informe"),
    )
    cassette = models.ForeignKey(
        Cassette,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="report_images",
        verbose_name=_("cassette"),
    )
    slide = models.ForeignKey(
        Slide,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="report_images",
        verbose_name=_("portaobjetos"),
    )
    image_path = models.CharField(
        _("ruta de imagen"),
        max_length=500,
        help_text=_("Ruta del archivo de imagen"),
    )
    description = models.TextField(
        _("descripción"),
        blank=True,
        help_text=_("Descripción de lo que muestra la imagen"),
    )
    magnification = models.CharField(
        _("magnificación"),
        max_length=50,
        blank=True,
        help_text=_("Ej: 400x, 100x"),
    )
    technique = models.CharField(
        _("técnica"),
        max_length=100,
        blank=True,
        help_text=_("Ej: H&E, PAS, Tricrómico de Masson"),
    )
    order = models.IntegerField(
        _("orden"),
        default=0,
        help_text=_("Orden de presentación en el informe"),
    )

    created_at = models.DateTimeField(_("creado el"), auto_now_add=True)

    class Meta:
        verbose_name = _("imagen de informe")
        verbose_name_plural = _("imágenes de informe")
        ordering = ["order", "created_at"]
        indexes = [
            models.Index(fields=["report", "order"]),
            models.Index(fields=["cassette"]),
            models.Index(fields=["slide"]),
        ]

    def __str__(self):
        if self.cassette:
            return f"{self.report} - {self.cassette.codigo_cassette} - Imagen"
        elif self.slide:
            return f"{self.report} - {self.slide.codigo_portaobjetos} - Imagen"
        return f"{self.report} - Imagen"


class EmailLog(models.Model):
    """
    High-level email logging for business records.
    Tracks all emails sent through the system with Celery task integration.
    """

    class EmailType(models.TextChoices):
        EMAIL_VERIFICATION = "email_verification", _("Verificación de Email")
        PASSWORD_RESET = "password_reset", _("Restablecimiento de Contraseña")
        SAMPLE_RECEPTION = "sample_reception", _("Recepción de Muestra")
        REPORT_READY = "report_ready", _("Informe Listo")
        WORK_ORDER = "work_order", _("Orden de Trabajo")
        CUSTOM = "custom", _("Notificación Personalizada")

    class Status(models.TextChoices):
        QUEUED = "queued", _("En Cola")
        SENT = "sent", _("Enviado")
        FAILED = "failed", _("Fallido")
        BOUNCED = "bounced", _("Rebotado")

    # Email details
    email_type = models.CharField(
        _("tipo de email"),
        max_length=50,
        choices=EmailType.choices,
    )
    recipient_email = models.EmailField(
        _("email del destinatario"),
    )
    recipient = models.ForeignKey(
        "accounts.Veterinarian",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emails_received",
        verbose_name=_("destinatario"),
    )
    subject = models.CharField(
        _("asunto"),
        max_length=500,
    )

    # Related objects
    protocol = models.ForeignKey(
        Protocol,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emails",
        verbose_name=_("protocolo"),
    )
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emails",
        verbose_name=_("orden de trabajo"),
    )

    # Celery task tracking
    celery_task_id = models.CharField(
        _("ID de tarea Celery"),
        max_length=255,
        unique=True,
        db_index=True,
    )

    # Status
    status = models.CharField(
        _("estado"),
        max_length=20,
        choices=Status.choices,
        default=Status.QUEUED,
    )
    sent_at = models.DateTimeField(
        _("enviado el"),
        null=True,
        blank=True,
    )
    error_message = models.TextField(
        _("mensaje de error"),
        blank=True,
    )

    # Metadata
    has_attachment = models.BooleanField(
        _("tiene adjunto"),
        default=False,
    )
    created_at = models.DateTimeField(
        _("creado el"),
        auto_now_add=True,
    )

    class Meta:
        verbose_name = _("log de email")
        verbose_name_plural = _("logs de email")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email_type", "-created_at"]),
            models.Index(fields=["recipient_email", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["celery_task_id"]),
        ]

    def __str__(self):
        return f"{self.get_email_type_display()} a {self.recipient_email} ({self.get_status_display()})"


class NotificationPreference(models.Model):
    """
    Per-veterinarian notification preferences.
    Allows veterinarians to control which notifications they receive.
    """

    veterinarian = models.OneToOneField(
        "accounts.Veterinarian",
        on_delete=models.CASCADE,
        related_name="notification_preferences",
        verbose_name=_("veterinario"),
    )

    # Notification preferences
    notify_on_reception = models.BooleanField(
        _("notificar en recepción"),
        default=True,
        help_text=_("Notificar cuando la muestra es recibida"),
    )
    notify_on_processing = models.BooleanField(
        _("notificar en procesamiento"),
        default=False,
        help_text=_("Notificar en cambios de estado"),
    )
    notify_on_report_ready = models.BooleanField(
        _("notificar cuando informe esté listo"),
        default=True,
        help_text=_("Notificar cuando el informe esté disponible"),
    )

    # Alternative email
    alternative_email = models.EmailField(
        _("email alternativo"),
        blank=True,
        help_text=_("Enviar notificaciones a este email en su lugar"),
    )

    # Attachment preferences
    include_attachments = models.BooleanField(
        _("incluir adjuntos"),
        default=True,
        help_text=_("Incluir PDFs en los emails"),
    )

    # Timestamps
    updated_at = models.DateTimeField(_("actualizado el"), auto_now=True)
    created_at = models.DateTimeField(_("creado el"), auto_now_add=True)

    class Meta:
        verbose_name = _("preferencia de notificación")
        verbose_name_plural = _("preferencias de notificación")

    def __str__(self):
        return f"Preferencias para {self.veterinarian.get_full_name()}"

    def get_recipient_email(self):
        """
        Get the email to send to (alternative or default).

        Returns:
            str: Email address to use for notifications
        """
        return self.alternative_email or self.veterinarian.email

    def should_send(self, email_type):
        """
        Check if notification should be sent for this type.

        Args:
            email_type: Type of email notification

        Returns:
            bool: True if notification should be sent
        """
        type_map = {
            "sample_reception": self.notify_on_reception,
            "report_ready": self.notify_on_report_ready,
            "processing": self.notify_on_processing,
        }
        return type_map.get(email_type, True)  # Default to True for other types
