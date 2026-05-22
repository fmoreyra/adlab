"""
Forms for the pages app.
"""

from django import forms

from pages.models import DashboardAnnouncement


class DashboardAnnouncementForm(forms.Form):
    """Admin form for editing the dashboard communication banner."""

    message = forms.CharField(
        label="Mensaje",
        widget=forms.Textarea(
            attrs={
                "class": (
                    "w-full rounded-lg border border-gray-300 px-3 py-2 "
                    "font-mono text-sm focus:border-purple-500 "
                    "focus:ring-purple-500"
                ),
                "rows": 12,
                "placeholder": "Escriba el aviso en Markdown...",
            }
        ),
        required=False,
        help_text="Máximo 4000 caracteres. Use Markdown para formato.",
    )
    is_active = forms.BooleanField(
        label="Mostrar aviso en los dashboards",
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "rounded border-gray-300 text-purple-600"}
        ),
    )

    def clean_message(self):
        """Validate message length."""
        message = self.cleaned_data.get("message", "")
        if len(message) > DashboardAnnouncement.MAX_MESSAGE_LENGTH:
            raise forms.ValidationError(
                f"El mensaje no puede superar "
                f"{DashboardAnnouncement.MAX_MESSAGE_LENGTH} caracteres."
            )
        return message
