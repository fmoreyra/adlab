"""
Forms for veterinarian approval admin tools.
"""

from django import forms

from accounts.models import VeterinarianPendingApprovalSettings

INPUT_CLASS = (
    "block w-full rounded-lg border border-gray-300 px-3 py-2 "
    "focus:border-purple-500 focus:ring-purple-500"
)


class VeterinarianPendingApprovalSettingsForm(forms.Form):
    """Admin form for editing the pending-approval contact screen."""

    title = forms.CharField(
        label="Título",
        max_length=200,
        widget=forms.TextInput(attrs={"class": INPUT_CLASS}),
    )
    message = forms.CharField(
        label="Mensaje",
        widget=forms.Textarea(
            attrs={
                "class": f"{INPUT_CLASS} font-mono text-sm",
                "rows": 10,
                "placeholder": "Instrucciones para el veterinario...",
            }
        ),
        required=False,
        help_text="Máximo 4000 caracteres. Use Markdown para formato.",
    )
    contact_phone = forms.CharField(
        label="Teléfono de contacto",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={"class": INPUT_CLASS}),
    )
    contact_email = forms.EmailField(
        label="Email de contacto",
        required=False,
        widget=forms.EmailInput(attrs={"class": INPUT_CLASS}),
    )
    is_active = forms.BooleanField(
        label="Mostrar contenido personalizado",
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "rounded border-gray-300 text-purple-600"}
        ),
    )

    def clean_message(self):
        """Validate message length."""
        message = self.cleaned_data.get("message", "")
        if (
            len(message)
            > VeterinarianPendingApprovalSettings.MAX_MESSAGE_LENGTH
        ):
            raise forms.ValidationError(
                f"El mensaje no puede superar "
                f"{VeterinarianPendingApprovalSettings.MAX_MESSAGE_LENGTH} "
                "caracteres."
            )
        return message


class AdminVeterinarianSearchForm(forms.Form):
    """Search form for admin veterinarian management."""

    query = forms.CharField(
        label="Buscar veterinario",
        required=False,
        help_text="Nombre, apellido, email, matrícula o CUIL.",
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "Ej: Pérez, MP-12345, vet@example.com",
                "autofocus": True,
            }
        ),
    )
    status = forms.ChoiceField(
        label="Estado",
        required=False,
        choices=[
            ("pending", "Pendientes"),
            ("enabled", "Habilitados"),
            ("inactive", "Inactivos"),
            ("all", "Todos"),
        ],
        widget=forms.Select(attrs={"class": INPUT_CLASS}),
    )


class AdminVeterinarianActionForm(forms.Form):
    """Hidden fields for admin veterinarian row actions."""

    veterinarian_id = forms.IntegerField(widget=forms.HiddenInput())
    action = forms.ChoiceField(
        choices=[
            ("approve", "Habilitar"),
            ("delete", "Eliminar"),
            ("reactivate", "Reactivar"),
        ],
        widget=forms.HiddenInput(),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )
    confirm_delete = forms.BooleanField(
        required=False,
        widget=forms.HiddenInput(),
    )
