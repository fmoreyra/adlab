"""
Forms for work order generation and management.
"""

from datetime import date
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from accounts.models import Veterinarian
from protocols.models import (
    PricingCatalog,
    Protocol,
    WorkOrder,
    WorkOrderService,
)


class WorkOrderSearchForm(forms.Form):
    """Form for searching protocols ready for work order generation."""

    protocol_number = forms.CharField(
        label=_("Número de Protocolo"),
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Ej: HP 24/001 o CT 24/001"),
            }
        ),
        help_text=_("Buscar protocolo por número"),
    )

    veterinarian = forms.ModelChoiceField(
        label=_("Veterinario"),
        queryset=Veterinarian.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        help_text=_("Filtrar por veterinario"),
    )

    status = forms.ChoiceField(
        label=_("Estado"),
        choices=[("", _("Todos"))] + list(Protocol.Status.choices),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        help_text=_("Filtrar por estado del protocolo"),
    )


class ProtocolSelectionForm(forms.Form):
    """Form for selecting multiple protocols to group in a work order."""

    protocols = forms.ModelMultipleChoiceField(
        label=_("Protocolos"),
        queryset=Protocol.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        help_text=_(
            "Seleccione los protocolos a incluir en la orden de trabajo"
        ),
    )

    def __init__(self, *args, veterinarian=None, **kwargs):
        super().__init__(*args, **kwargs)

        if veterinarian:
            # Only show protocols from this veterinarian that are ready
            # and don't already have a work order
            self.fields["protocols"].queryset = (
                Protocol.objects.filter(
                    veterinarian=veterinarian,
                    status__in=[
                        Protocol.Status.READY,
                        Protocol.Status.REPORT_SENT,
                    ],
                    work_order__isnull=True,
                )
                .select_related("veterinarian")
                .order_by("-submission_date")
            )

    def clean_protocols(self):
        """Validate protocol selection."""
        protocols = self.cleaned_data.get("protocols")

        if not protocols:
            raise ValidationError(_("Debe seleccionar al menos un protocolo."))

        # Validate all protocols are from same veterinarian
        veterinarians = set(p.veterinarian for p in protocols)
        if len(veterinarians) > 1:
            raise ValidationError(
                _(
                    "Todos los protocolos deben pertenecer al mismo veterinario."
                )
            )

        # Validate none have existing work orders
        with_orders = [p for p in protocols if p.work_order]
        if with_orders:
            raise ValidationError(
                _("Algunos protocolos ya tienen orden de trabajo asignada.")
            )

        return protocols


class WorkOrderCreateForm(forms.ModelForm):
    """Form for creating a new work order."""

    class Meta:
        model = WorkOrder
        fields = [
            "veterinarian",
            "advance_payment",
            "billing_name",
            "cuit_cuil",
            "iva_condition",
            "observations",
        ]
        widgets = {
            "veterinarian": forms.Select(
                attrs={"class": "form-control", "readonly": "readonly"}
            ),
            "advance_payment": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                    "placeholder": "0.00",
                }
            ),
            "billing_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _(
                        "Dejar vacío para usar nombre del veterinario"
                    ),
                }
            ),
            "cuit_cuil": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "XX-XXXXXXXX-X",
                }
            ),
            "iva_condition": forms.Select(attrs={"class": "form-control"}),
            "observations": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": _("Observaciones adicionales..."),
                }
            ),
        }
        labels = {
            "veterinarian": _("Veterinario"),
            "advance_payment": _("Pago Adelantado (USD)"),
            "billing_name": _("Nombre para Facturación"),
            "cuit_cuil": _("CUIT/CUIL"),
            "iva_condition": _("Condición IVA"),
            "observations": _("Observaciones"),
        }
        help_texts = {
            "advance_payment": _("Monto pagado adelantado (opcional)"),
            "billing_name": _(
                "Opcional: usar si el nombre de facturación difiere del veterinario"
            ),
        }

    def __init__(self, *args, protocols=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.protocols = protocols or []

        # Make veterinarian field disabled (it's determined by protocols)
        if self.protocols:
            veterinarian = self.protocols[0].veterinarian
            self.fields["veterinarian"].initial = veterinarian
            self.fields["veterinarian"].disabled = True

            # Pre-fill billing info from veterinarian if available
            if not self.instance.pk:
                vet_user = veterinarian.user
                self.fields["billing_name"].initial = vet_user.get_full_name()
                if hasattr(veterinarian, "cuit_cuil"):
                    self.fields["cuit_cuil"].initial = veterinarian.cuit_cuil

    def clean_advance_payment(self):
        """Validate advance payment amount."""
        advance = self.cleaned_data.get("advance_payment", Decimal("0"))

        if advance < 0:
            raise ValidationError(
                _("El pago adelantado no puede ser negativo.")
            )

        return advance

    def clean_cuit_cuil(self):
        """Validate CUIT/CUIL format (basic validation)."""
        cuit = self.cleaned_data.get("cuit_cuil", "").strip()

        if cuit:
            # Remove hyphens for validation
            cuit_clean = cuit.replace("-", "")
            if not cuit_clean.isdigit() or len(cuit_clean) != 11:
                raise ValidationError(
                    _(
                        "CUIT/CUIL debe tener 11 dígitos (formato: XX-XXXXXXXX-X)"
                    )
                )

        return cuit


class WorkOrderServiceForm(forms.ModelForm):
    """Form for managing individual work order services."""

    class Meta:
        model = WorkOrderService
        fields = [
            "protocol",
            "description",
            "service_type",
            "quantity",
            "unit_price",
            "discount",
        ]
        widgets = {
            "protocol": forms.Select(attrs={"class": "form-control"}),
            "description": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Descripción del servicio"),
                }
            ),
            "service_type": forms.Select(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                }
            ),
            "unit_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                }
            ),
            "discount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                    "placeholder": "0.00",
                }
            ),
        }

    def clean_quantity(self):
        """Validate quantity is positive."""
        quantity = self.cleaned_data.get("quantity")
        if quantity and quantity < 1:
            raise ValidationError(_("La cantidad debe ser al menos 1."))
        return quantity

    def clean_unit_price(self):
        """Validate unit price is positive."""
        price = self.cleaned_data.get("unit_price")
        if price and price < 0:
            raise ValidationError(_("El precio no puede ser negativo."))
        return price

    def clean_discount(self):
        """Validate discount."""
        discount = self.cleaned_data.get("discount", Decimal("0"))
        if discount < 0:
            raise ValidationError(_("El descuento no puede ser negativo."))
        return discount


class PricingCatalogForm(forms.ModelForm):
    """Form for managing pricing catalog entries."""

    class Meta:
        model = PricingCatalog
        fields = [
            "service_type",
            "description",
            "price",
            "valid_from",
            "valid_until",
            "observations",
        ]
        widgets = {
            "service_type": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Ej: histopatologia_2a5_piezas"),
                }
            ),
            "description": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _(
                        "Ej: Análisis histopatológico (2-5 piezas)"
                    ),
                }
            ),
            "price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                    "placeholder": "0.00",
                }
            ),
            "valid_from": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "valid_until": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "observations": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
        }
        labels = {
            "service_type": _("Tipo de Servicio"),
            "description": _("Descripción"),
            "price": _("Precio (USD)"),
            "valid_from": _("Válido Desde"),
            "valid_until": _("Válido Hasta"),
            "observations": _("Observaciones"),
        }
        help_texts = {
            "service_type": _(
                "Identificador único del servicio (sin espacios)"
            ),
            "valid_from": _("Fecha desde la cual este precio es válido"),
            "valid_until": _("Dejar vacío si no tiene fecha de expiración"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default valid_from to today if creating new
        if not self.instance.pk:
            self.fields["valid_from"].initial = date.today()

    def clean_price(self):
        """Validate price is positive."""
        price = self.cleaned_data.get("price")
        if price and price < 0:
            raise ValidationError(_("El precio no puede ser negativo."))
        return price

    def clean_service_type(self):
        """Validate service type format."""
        service_type = self.cleaned_data.get("service_type", "").strip()

        # Ensure no spaces (use underscores)
        if " " in service_type:
            raise ValidationError(
                _(
                    "El tipo de servicio no puede contener espacios. Use guiones bajos (_)."
                )
            )

        return service_type.lower()

    def clean(self):
        """Validate date range."""
        cleaned_data = super().clean()
        valid_from = cleaned_data.get("valid_from")
        valid_until = cleaned_data.get("valid_until")

        if valid_from and valid_until and valid_until < valid_from:
            raise ValidationError(
                {
                    "valid_until": _(
                        "La fecha final debe ser posterior a la fecha inicial."
                    )
                }
            )

        return cleaned_data


class WorkOrderFilterForm(forms.Form):
    """Form for filtering work orders in list view."""

    order_number = forms.CharField(
        label=_("Número de Orden"),
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Ej: OT-2024-001"),
            }
        ),
    )

    veterinarian = forms.ModelChoiceField(
        label=_("Veterinario"),
        queryset=Veterinarian.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    status = forms.ChoiceField(
        label=_("Estado"),
        choices=[("", _("Todos"))] + list(WorkOrder.Status.choices),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    payment_status = forms.ChoiceField(
        label=_("Estado de Pago"),
        choices=[("", _("Todos"))] + list(WorkOrder.PaymentStatus.choices),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    date_from = forms.DateField(
        label=_("Desde"),
        required=False,
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
            }
        ),
    )

    date_to = forms.DateField(
        label=_("Hasta"),
        required=False,
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
            }
        ),
    )
