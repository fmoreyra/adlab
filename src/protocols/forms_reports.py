"""
Forms for report generation and management.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.utils.translation import gettext_lazy as _

from accounts.models import LaboratoryStaff
from protocols.form_widgets import (
    TAILWIND_INPUT_CLASS,
    TAILWIND_TEXTAREA_CLASS,
)
from protocols.models import (
    Cassette,
    CassetteObservation,
    Protocol,
    Report,
    ReportImage,
)
from protocols.services.report_image_service import (
    MAX_IMAGES_PER_REPORT,
    ReportImageService,
)


class ReportSearchForm(forms.Form):
    """Form for searching protocols ready for report generation."""

    protocol_number = forms.CharField(
        label=_("Número de Protocolo"),
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": TAILWIND_INPUT_CLASS,
                "placeholder": _("Ej: HP 24/001"),
            }
        ),
        help_text=_("Buscar por número de protocolo"),
    )


class ReportCreateForm(forms.ModelForm):
    """Form for creating a new report."""

    class Meta:
        model = Report
        fields = [
            "laboratory_staff",
            "macroscopic_observations",
            "microscopic_observations",
            "diagnosis",
            "comments",
            "recommendations",
        ]
        widgets = {
            "laboratory_staff": forms.Select(
                attrs={"class": TAILWIND_INPUT_CLASS}
            ),
            "macroscopic_observations": forms.Textarea(
                attrs={
                    "class": TAILWIND_TEXTAREA_CLASS,
                    "rows": 4,
                    "placeholder": _(
                        "Describa las observaciones macroscópicas del material recibido..."
                    ),
                }
            ),
            "microscopic_observations": forms.Textarea(
                attrs={
                    "class": TAILWIND_TEXTAREA_CLASS,
                    "rows": 6,
                    "placeholder": _(
                        "Describa las observaciones microscópicas generales..."
                    ),
                }
            ),
            "diagnosis": forms.Textarea(
                attrs={
                    "class": TAILWIND_TEXTAREA_CLASS,
                    "rows": 3,
                    "placeholder": _(
                        "Ingrese el diagnóstico patológico final..."
                    ),
                }
            ),
            "comments": forms.Textarea(
                attrs={
                    "class": TAILWIND_TEXTAREA_CLASS,
                    "rows": 3,
                    "placeholder": _(
                        "Comentarios adicionales sobre el caso..."
                    ),
                }
            ),
            "recommendations": forms.Textarea(
                attrs={
                    "class": TAILWIND_TEXTAREA_CLASS,
                    "rows": 3,
                    "placeholder": _(
                        "Recomendaciones clínicas para el veterinario..."
                    ),
                }
            ),
        }
        labels = {
            "laboratory_staff": _("Personal de Laboratorio"),
            "macroscopic_observations": _("Observaciones Macroscópicas"),
            "microscopic_observations": _("Observaciones Microscópicas"),
            "diagnosis": _("Diagnóstico"),
            "comments": _("Comentarios"),
            "recommendations": _("Recomendaciones"),
        }

    def __init__(self, *args, protocol=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.protocol = protocol

        # Only show active laboratory staff with report creation permission
        self.fields[
            "laboratory_staff"
        ].queryset = LaboratoryStaff.objects.filter(
            is_active=True, can_create_reports=True
        )

        # Set protocol veterinarian if creating new report
        if protocol and not self.instance.pk:
            self.instance.protocol = protocol
            self.instance.veterinarian = protocol.veterinarian

    def clean_laboratory_staff(self):
        """Ensure the selected staff member can sign reports."""
        laboratory_staff = self.cleaned_data.get("laboratory_staff")
        if not laboratory_staff:
            return laboratory_staff

        if not laboratory_staff.has_signature():
            raise ValidationError(
                _(
                    "El personal seleccionado debe tener firma digital "
                    "cargada en su perfil."
                )
            )

        return laboratory_staff

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
            "cassette": forms.Select(attrs={"class": TAILWIND_INPUT_CLASS}),
            "observations": forms.Textarea(
                attrs={
                    "class": TAILWIND_TEXTAREA_CLASS,
                    "rows": 5,
                    "placeholder": _(
                        "Describa las observaciones microscópicas para este cassette..."
                    ),
                }
            ),
            "partial_diagnosis": forms.Textarea(
                attrs={
                    "class": TAILWIND_TEXTAREA_CLASS,
                    "rows": 2,
                    "placeholder": _(
                        "Diagnóstico específico para este cassette (opcional)..."
                    ),
                }
            ),
            "order": forms.NumberInput(attrs={"class": TAILWIND_INPUT_CLASS}),
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
                    self.fields[
                        "cassette"
                    ].queryset = protocol.histopathology_sample.cassettes.all()
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


class ReportImageForm(forms.ModelForm):
    """Form for uploading a microscopy image on a report."""

    class Meta:
        model = ReportImage
        fields = [
            "cassette",
            "slide",
            "image",
            "description",
            "magnification",
            "technique",
            "order",
        ]
        widgets = {
            "cassette": forms.Select(attrs={"class": TAILWIND_INPUT_CLASS}),
            "slide": forms.Select(attrs={"class": TAILWIND_INPUT_CLASS}),
            "image": forms.ClearableFileInput(
                attrs={
                    "class": TAILWIND_INPUT_CLASS,
                    "accept": "image/jpeg,image/png,image/webp",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": TAILWIND_TEXTAREA_CLASS,
                    "rows": 2,
                    "placeholder": _("Descripción de la imagen..."),
                }
            ),
            "magnification": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT_CLASS,
                    "placeholder": _("Ej: 400x"),
                }
            ),
            "technique": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT_CLASS,
                    "placeholder": _("Ej: H&E"),
                }
            ),
            "order": forms.NumberInput(attrs={"class": TAILWIND_INPUT_CLASS}),
        }
        labels = {
            "cassette": _("Cassette (opcional)"),
            "slide": _("Portaobjetos (opcional)"),
            "image": _("Imagen"),
            "description": _("Descripción"),
            "magnification": _("Magnificación"),
            "technique": _("Técnica"),
            "order": _("Orden"),
        }

    def __init__(self, *args, report=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.report = report
        self.fields["image"].required = False

        if report and report.protocol:
            protocol = report.protocol
            if (
                protocol.analysis_type == Protocol.AnalysisType.HISTOPATHOLOGY
                and hasattr(protocol, "histopathology_sample")
            ):
                self.fields[
                    "cassette"
                ].queryset = protocol.histopathology_sample.cassettes.all()
            else:
                self.fields["cassette"].queryset = Cassette.objects.none()
            self.fields["slide"].queryset = protocol.slides.all()

        if report and not self.instance.pk:
            self.instance.report = report

    def clean_image(self):
        """Validate new uploads; keep existing file when not replaced."""
        image = self.cleaned_data.get("image")
        if image:
            ReportImageService.validate_upload(image)
        return image

    def clean(self):
        """Skip empty extra forms; require image when the row has data."""
        cleaned = super().clean()
        if cleaned.get("DELETE"):
            return cleaned

        if not self.has_changed() and not self.instance.pk:
            return cleaned

        has_file = cleaned.get("image") or (
            self.instance.pk and self.instance.image
        )
        if not has_file:
            raise ValidationError(_("Debe adjuntar un archivo de imagen."))
        return cleaned


class BaseReportImageFormSet(BaseInlineFormSet):
    """Limit total images per report."""

    def clean(self):
        super().clean()
        if any(self.errors):
            return

        active_count = 0
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if form.cleaned_data.get("DELETE"):
                continue
            if form.instance.pk or form.cleaned_data.get("image"):
                active_count += 1

        if active_count > MAX_IMAGES_PER_REPORT:
            raise ValidationError(
                _("No puede adjuntar más de %(max)s imágenes por informe.")
                % {"max": MAX_IMAGES_PER_REPORT}
            )


ReportImageFormSet = inlineformset_factory(
    Report,
    ReportImage,
    form=ReportImageForm,
    formset=BaseReportImageFormSet,
    extra=2,
    can_delete=True,
    max_num=MAX_IMAGES_PER_REPORT,
    fields=[
        "cassette",
        "slide",
        "image",
        "description",
        "magnification",
        "technique",
        "order",
    ],
)


class ReportSendForm(forms.Form):
    """Form for sending a report via email."""

    additional_email = forms.EmailField(
        label=_("Email adicional (opcional)"),
        required=False,
        widget=forms.EmailInput(
            attrs={
                "class": TAILWIND_INPUT_CLASS,
                "placeholder": _("email@ejemplo.com"),
            }
        ),
        help_text=_("Enviar copia a otro destinatario (opcional)"),
    )

    custom_message = forms.CharField(
        label=_("Mensaje personalizado (opcional)"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": TAILWIND_INPUT_CLASS,
                "rows": 3,
                "placeholder": _(
                    "Mensaje adicional para incluir en el email..."
                ),
            }
        ),
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
        additional_email = self.cleaned_data.get(
            "additional_email", ""
        ).strip()
        if additional_email and additional_email == self.veterinarian_email:
            raise ValidationError(
                _(
                    "El email adicional no puede ser el mismo que el del veterinario."
                )
            )
        return additional_email
