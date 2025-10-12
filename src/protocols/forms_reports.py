"""
Forms for report generation and management.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from accounts.models import Histopathologist
from protocols.models import Cassette, CassetteObservation, Protocol, Report


class ReportSearchForm(forms.Form):
    """Form for searching protocols ready for report generation."""

    protocol_number = forms.CharField(
        label=_("Número de Protocolo"),
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": _("Ej: HP 24/001"),
        }),
        help_text=_("Buscar por número de protocolo"),
    )


class ReportCreateForm(forms.ModelForm):
    """Form for creating a new report."""

    class Meta:
        model = Report
        fields = [
            "histopathologist",
            "macroscopic_observations",
            "microscopic_observations",
            "diagnosis",
            "comments",
            "recommendations",
        ]
        widgets = {
            "histopathologist": forms.Select(attrs={"class": "form-control"}),
            "macroscopic_observations": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": _("Describa las observaciones macroscópicas del material recibido..."),
            }),
            "microscopic_observations": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": _("Describa las observaciones microscópicas generales..."),
            }),
            "diagnosis": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": _("Ingrese el diagnóstico patológico final..."),
            }),
            "comments": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": _("Comentarios adicionales sobre el caso..."),
            }),
            "recommendations": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": _("Recomendaciones clínicas para el veterinario..."),
            }),
        }
        labels = {
            "histopathologist": _("Histopatólogo"),
            "macroscopic_observations": _("Observaciones Macroscópicas"),
            "microscopic_observations": _("Observaciones Microscópicas"),
            "diagnosis": _("Diagnóstico"),
            "comments": _("Comentarios"),
            "recommendations": _("Recomendaciones"),
        }

    def __init__(self, *args, protocol=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.protocol = protocol
        
        # Only show active histopathologists
        self.fields["histopathologist"].queryset = (
            Histopathologist.objects.filter(is_active=True)
        )
        
        # Set protocol veterinarian if creating new report
        if protocol and not self.instance.pk:
            self.instance.protocol = protocol
            self.instance.veterinarian = protocol.veterinarian

    def clean_diagnosis(self):
        """Ensure diagnosis is not empty."""
        diagnosis = self.cleaned_data.get("diagnosis", "").strip()
        if not diagnosis:
            raise ValidationError(
                _("El diagnóstico es obligatorio para generar el informe.")
            )
        return diagnosis


class CassetteObservationForm(forms.ModelForm):
    """Form for adding observations to a cassette."""

    class Meta:
        model = CassetteObservation
        fields = ["cassette", "observations", "partial_diagnosis", "order"]
        widgets = {
            "cassette": forms.Select(attrs={"class": "form-control"}),
            "observations": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": _("Describa las observaciones microscópicas para este cassette..."),
            }),
            "partial_diagnosis": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": _("Diagnóstico específico para este cassette (opcional)..."),
            }),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }
        labels = {
            "cassette": _("Cassette"),
            "observations": _("Observaciones Microscópicas"),
            "partial_diagnosis": _("Diagnóstico Parcial"),
            "order": _("Orden de Presentación"),
        }

    def __init__(self, *args, report=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.report = report
        
        # Filter cassettes to only show those from the protocol
        if report and report.protocol:
            protocol = report.protocol
            if protocol.analysis_type == Protocol.AnalysisType.HISTOPATHOLOGY:
                if hasattr(protocol, "histopathology_sample"):
                    self.fields["cassette"].queryset = (
                        protocol.histopathology_sample.cassettes.all()
                    )
                else:
                    self.fields["cassette"].queryset = Cassette.objects.none()
            else:
                self.fields["cassette"].queryset = Cassette.objects.none()
        
        # Set report instance
        if report and not self.instance.pk:
            self.instance.report = report

    def clean_observations(self):
        """Ensure observations are not empty."""
        observations = self.cleaned_data.get("observations", "").strip()
        if not observations:
            raise ValidationError(
                _("Las observaciones son obligatorias para cada cassette.")
            )
        return observations


# =============================================================================
# FORMSETS FOR CASSETTE OBSERVATIONS
# =============================================================================

CassetteObservationFormSet = inlineformset_factory(
    Report,
    CassetteObservation,
    form=CassetteObservationForm,
    extra=1,
    can_delete=True,
    fields=["cassette", "observations", "partial_diagnosis", "order"],
)


class ReportSendForm(forms.Form):
    """Form for sending a report via email."""

    additional_email = forms.EmailField(
        label=_("Email adicional (opcional)"),
        required=False,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": _("email@ejemplo.com"),
        }),
        help_text=_("Enviar copia a otro destinatario (opcional)"),
    )
    
    custom_message = forms.CharField(
        label=_("Mensaje personalizado (opcional)"),
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": _("Mensaje adicional para incluir en el email..."),
        }),
        help_text=_("Mensaje personalizado para el veterinario"),
    )
    
    include_work_order = forms.BooleanField(
        label=_("Incluir Orden de Trabajo"),
        required=False,
        initial=False,
        help_text=_("Adjuntar la orden de trabajo en el mismo email"),
    )

    def __init__(self, *args, veterinarian_email=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.veterinarian_email = veterinarian_email

    def clean_additional_email(self):
        """Validate additional email is different from veterinarian email."""
        additional_email = self.cleaned_data.get("additional_email", "").strip()
        if additional_email and additional_email == self.veterinarian_email:
            raise ValidationError(
                _("El email adicional no puede ser el mismo que el del veterinario.")
            )
        return additional_email

