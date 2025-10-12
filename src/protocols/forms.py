from datetime import date

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from protocols.models import (
    Cassette,
    CytologySample,
    HistopathologySample,
    Protocol,
    Slide,
)

# Valid species choices
SPECIES_CHOICES = [
    ("", _("Seleccionar especie")),
    ("Canino", _("Canino")),
    ("Felino", _("Felino")),
    ("Bovino", _("Bovino")),
    ("Equino", _("Equino")),
    ("Ovino", _("Ovino")),
    ("Caprino", _("Caprino")),
    ("Porcino", _("Porcino")),
    ("Aviar", _("Aviar")),
    ("Otro", _("Otro")),
]

# Cytology technique choices
CYTOLOGY_TECHNIQUE_CHOICES = [
    ("", _("Seleccionar técnica")),
    (
        "Punción aspiración con aguja fina (PAAF)",
        _("Punción aspiración con aguja fina (PAAF)"),
    ),
    ("Hisopado", _("Hisopado")),
    ("Raspado", _("Raspado")),
    ("Impronta", _("Impronta")),
    ("Lavado", _("Lavado")),
    ("Otro", _("Otro")),
]


class ProtocolForm(forms.ModelForm):
    """Base form for Protocol model with common fields."""

    species = forms.ChoiceField(
        label=_("Especie"),
        choices=SPECIES_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white"
            }
        ),
    )

    class Meta:
        model = Protocol
        fields = [
            "species",
            "breed",
            "sex",
            "age",
            "animal_identification",
            "owner_last_name",
            "owner_first_name",
            "presumptive_diagnosis",
            "clinical_history",
            "academic_interest",
            "submission_date",
        ]
        widgets = {
            "species": forms.Select(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white"
                }
            ),
            "breed": forms.TextInput(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                }
            ),
            "sex": forms.Select(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white"
                }
            ),
            "age": forms.TextInput(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                    "placeholder": _("ej: 2 años, 6 meses"),
                }
            ),
            "animal_identification": forms.TextInput(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                }
            ),
            "owner_last_name": forms.TextInput(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                }
            ),
            "owner_first_name": forms.TextInput(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                }
            ),
            "presumptive_diagnosis": forms.Textarea(
                attrs={
                    "class": "block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 resize-none",
                    "rows": 3,
                }
            ),
            "clinical_history": forms.Textarea(
                attrs={
                    "class": "block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 resize-none",
                    "rows": 4,
                }
            ),
            "academic_interest": forms.CheckboxInput(
                attrs={
                    "class": "h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition-colors duration-200"
                }
            ),
            "submission_date": forms.DateInput(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                    "type": "date",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default submission date to today
        if not self.instance.pk:
            self.fields["submission_date"].initial = date.today()


class CytologyProtocolForm(forms.Form):
    """
    Combined form for creating a cytology protocol with sample information.
    """

    # Protocol fields
    species = forms.ChoiceField(
        label=_("Especie"),
        choices=SPECIES_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white"
            }
        ),
    )
    breed = forms.CharField(
        label=_("Raza"),
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
            }
        ),
    )
    sex = forms.ChoiceField(
        label=_("Sexo"),
        choices=[("", _("Seleccionar sexo"))] + list(Protocol.Sex.choices),
        required=False,
        widget=forms.Select(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white"
            }
        ),
    )
    age = forms.CharField(
        label=_("Edad"),
        max_length=50,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": _("ej: 2 años, 6 meses"),
            }
        ),
    )
    animal_identification = forms.CharField(
        label=_("Identificación del Animal"),
        max_length=200,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
            }
        ),
    )
    owner_last_name = forms.CharField(
        label=_("Apellido del Propietario"),
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
            }
        ),
    )
    owner_first_name = forms.CharField(
        label=_("Nombre del Propietario"),
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
            }
        ),
    )
    presumptive_diagnosis = forms.CharField(
        label=_("Diagnóstico Presuntivo"),
        widget=forms.Textarea(
            attrs={
                "class": "block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 resize-none",
                "rows": 3,
            }
        ),
    )
    clinical_history = forms.CharField(
        label=_("Historia Clínica"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 resize-none",
                "rows": 4,
            }
        ),
    )
    academic_interest = forms.BooleanField(
        label=_("Interés Académico"),
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition-colors duration-200"
            }
        ),
        help_text=_("Permitir uso con fines académicos/investigación"),
    )
    submission_date = forms.DateField(
        label=_("Fecha de Remisión"),
        initial=date.today,
        widget=forms.DateInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "type": "date",
            }
        ),
    )

    # Cytology sample fields
    technique_used = forms.ChoiceField(
        label=_("Técnica Utilizada"),
        choices=CYTOLOGY_TECHNIQUE_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white"
            }
        ),
    )
    sampling_site = forms.CharField(
        label=_("Sitio de Muestreo"),
        max_length=200,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
            }
        ),
        help_text=_("Ubicación anatómica de la muestra"),
    )
    number_of_slides = forms.IntegerField(
        label=_("Número de Portaobjetos"),
        initial=1,
        min_value=1,
        widget=forms.NumberInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
            }
        ),
    )
    observations = forms.CharField(
        label=_("Observaciones"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 resize-none",
                "rows": 3,
            }
        ),
    )

    def clean_species(self):
        """Validate species selection."""
        species = self.cleaned_data.get("species")
        if not species:
            raise ValidationError(_("Por favor seleccione una especie"))
        return species

    def clean_technique_used(self):
        """Validate technique selection."""
        technique = self.cleaned_data.get("technique_used")
        if not technique:
            raise ValidationError(_("Por favor seleccione una técnica"))
        return technique

    def save(self, veterinarian, commit=True):
        """
        Create Protocol and CytologySample instances.

        Args:
            veterinarian: Veterinarian instance
            commit: Whether to save to database

        Returns:
            Protocol instance
        """
        # Create protocol
        protocol = Protocol(
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            veterinarian=veterinarian,
            species=self.cleaned_data["species"],
            breed=self.cleaned_data.get("breed", ""),
            sex=self.cleaned_data.get("sex", ""),
            age=self.cleaned_data.get("age", ""),
            animal_identification=self.cleaned_data["animal_identification"],
            owner_last_name=self.cleaned_data.get("owner_last_name", ""),
            owner_first_name=self.cleaned_data.get("owner_first_name", ""),
            presumptive_diagnosis=self.cleaned_data["presumptive_diagnosis"],
            clinical_history=self.cleaned_data.get("clinical_history", ""),
            academic_interest=self.cleaned_data.get(
                "academic_interest", False
            ),
            submission_date=self.cleaned_data["submission_date"],
            status=Protocol.Status.DRAFT,
        )

        if commit:
            protocol.save()

            # Create cytology sample
            CytologySample.objects.create(
                protocol=protocol,
                veterinarian=veterinarian,
                technique_used=self.cleaned_data["technique_used"],
                sampling_site=self.cleaned_data["sampling_site"],
                number_of_slides=self.cleaned_data["number_of_slides"],
                observations=self.cleaned_data.get("observations", ""),
            )

        return protocol


class HistopathologyProtocolForm(forms.Form):
    """
    Combined form for creating a histopathology protocol with sample information.
    """

    # Protocol fields
    species = forms.ChoiceField(
        label=_("Especie"),
        choices=SPECIES_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white"
            }
        ),
    )
    breed = forms.CharField(
        label=_("Raza"),
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
            }
        ),
    )
    sex = forms.ChoiceField(
        label=_("Sexo"),
        choices=[("", _("Seleccionar sexo"))] + list(Protocol.Sex.choices),
        required=False,
        widget=forms.Select(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white"
            }
        ),
    )
    age = forms.CharField(
        label=_("Edad"),
        max_length=50,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": _("ej: 2 años, 6 meses"),
            }
        ),
    )
    animal_identification = forms.CharField(
        label=_("Identificación del Animal"),
        max_length=200,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
            }
        ),
    )
    owner_last_name = forms.CharField(
        label=_("Apellido del Propietario"),
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
            }
        ),
    )
    owner_first_name = forms.CharField(
        label=_("Nombre del Propietario"),
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
            }
        ),
    )
    presumptive_diagnosis = forms.CharField(
        label=_("Diagnóstico Presuntivo"),
        widget=forms.Textarea(
            attrs={
                "class": "block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 resize-none",
                "rows": 3,
            }
        ),
    )
    clinical_history = forms.CharField(
        label=_("Historia Clínica"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 resize-none",
                "rows": 4,
            }
        ),
    )
    academic_interest = forms.BooleanField(
        label=_("Interés Académico"),
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition-colors duration-200"
            }
        ),
        help_text=_("Permitir uso con fines académicos/investigación"),
    )
    submission_date = forms.DateField(
        label=_("Fecha de Remisión"),
        initial=date.today,
        widget=forms.DateInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "type": "date",
            }
        ),
    )

    # Histopathology sample fields
    material_submitted = forms.CharField(
        label=_("Material Remitido"),
        widget=forms.Textarea(
            attrs={
                "class": "block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 resize-none",
                "rows": 3,
            }
        ),
        help_text=_("Descripción de las muestras de tejido/órganos"),
    )
    number_of_containers = forms.IntegerField(
        label=_("Número de Frascos"),
        initial=1,
        min_value=1,
        widget=forms.NumberInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
            }
        ),
    )
    preservation = forms.CharField(
        label=_("Conservación"),
        max_length=100,
        initial="Formol 10%",
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
            }
        ),
    )
    observations = forms.CharField(
        label=_("Observaciones"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 resize-none",
                "rows": 3,
            }
        ),
    )

    def clean_species(self):
        """Validate species selection."""
        species = self.cleaned_data.get("species")
        if not species:
            raise ValidationError(_("Por favor seleccione una especie"))
        return species

    def save(self, veterinarian, commit=True):
        """
        Create Protocol and HistopathologySample instances.

        Args:
            veterinarian: Veterinarian instance
            commit: Whether to save to database

        Returns:
            Protocol instance
        """
        # Create protocol
        protocol = Protocol(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            veterinarian=veterinarian,
            species=self.cleaned_data["species"],
            breed=self.cleaned_data.get("breed", ""),
            sex=self.cleaned_data.get("sex", ""),
            age=self.cleaned_data.get("age", ""),
            animal_identification=self.cleaned_data["animal_identification"],
            owner_last_name=self.cleaned_data.get("owner_last_name", ""),
            owner_first_name=self.cleaned_data.get("owner_first_name", ""),
            presumptive_diagnosis=self.cleaned_data["presumptive_diagnosis"],
            clinical_history=self.cleaned_data.get("clinical_history", ""),
            academic_interest=self.cleaned_data.get(
                "academic_interest", False
            ),
            submission_date=self.cleaned_data["submission_date"],
            status=Protocol.Status.DRAFT,
        )

        if commit:
            protocol.save()

            # Create histopathology sample
            HistopathologySample.objects.create(
                protocol=protocol,
                veterinarian=veterinarian,
                material_submitted=self.cleaned_data["material_submitted"],
                number_of_containers=self.cleaned_data["number_of_containers"],
                preservation=self.cleaned_data["preservation"],
                observations=self.cleaned_data.get("observations", ""),
            )

        return protocol


class ProtocolEditForm(forms.ModelForm):
    """Form for editing existing protocols (drafts only)."""

    species = forms.ChoiceField(
        label=_("Especie"),
        choices=SPECIES_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white"
            }
        ),
    )

    class Meta:
        model = Protocol
        fields = [
            "species",
            "breed",
            "sex",
            "age",
            "animal_identification",
            "owner_last_name",
            "owner_first_name",
            "presumptive_diagnosis",
            "clinical_history",
            "academic_interest",
            "submission_date",
        ]
        widgets = {
            "breed": forms.TextInput(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                }
            ),
            "sex": forms.Select(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white"
                }
            ),
            "age": forms.TextInput(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                }
            ),
            "animal_identification": forms.TextInput(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                }
            ),
            "owner_last_name": forms.TextInput(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                }
            ),
            "owner_first_name": forms.TextInput(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                }
            ),
            "presumptive_diagnosis": forms.Textarea(
                attrs={
                    "class": "block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 resize-none",
                    "rows": 3,
                }
            ),
            "clinical_history": forms.Textarea(
                attrs={
                    "class": "block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 resize-none",
                    "rows": 4,
                }
            ),
            "academic_interest": forms.CheckboxInput(
                attrs={
                    "class": "h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition-colors duration-200"
                }
            ),
            "submission_date": forms.DateInput(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                    "type": "date",
                }
            ),
        }


class CytologySampleEditForm(forms.ModelForm):
    """Form for editing cytology sample details."""

    technique_used = forms.ChoiceField(
        label=_("Técnica Utilizada"),
        choices=CYTOLOGY_TECHNIQUE_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white"
            }
        ),
    )

    class Meta:
        model = CytologySample
        fields = [
            "technique_used",
            "sampling_site",
            "number_of_slides",
            "observations",
        ]
        widgets = {
            "sampling_site": forms.TextInput(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                }
            ),
            "number_of_slides": forms.NumberInput(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                }
            ),
            "observations": forms.Textarea(
                attrs={
                    "class": "block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 resize-none",
                    "rows": 3,
                }
            ),
        }


class HistopathologySampleEditForm(forms.ModelForm):
    """Form for editing histopathology sample details."""

    class Meta:
        model = HistopathologySample
        fields = [
            "material_submitted",
            "number_of_containers",
            "preservation",
            "observations",
        ]
        widgets = {
            "material_submitted": forms.Textarea(
                attrs={
                    "class": "block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 resize-none",
                    "rows": 3,
                }
            ),
            "number_of_containers": forms.NumberInput(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                }
            ),
            "preservation": forms.TextInput(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                }
            ),
            "observations": forms.Textarea(
                attrs={
                    "class": "block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 resize-none",
                    "rows": 3,
                }
            ),
        }


# ============================================================================
# RECEPTION FORMS
# ============================================================================


class ReceptionSearchForm(forms.Form):
    """Form to search for protocols by temporary code."""

    temporary_code = forms.CharField(
        label=_("Código temporal"),
        max_length=50,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200-lg",
                "placeholder": _("Ej: TMP-HP-20241010-001"),
                "autofocus": True,
            }
        ),
        help_text=_(
            "Ingrese el código temporal que aparece en el protocolo impreso"
        ),
    )

    def clean_temporary_code(self):
        """Validate and normalize temporary code."""
        code = self.cleaned_data.get("temporary_code", "").strip().upper()
        if not code:
            raise ValidationError(_("El código temporal es requerido"))
        return code


class ReceptionForm(forms.Form):
    """Form to record sample reception details."""

    sample_condition = forms.ChoiceField(
        label=_("Condición de la muestra"),
        choices=Protocol.SampleCondition.choices,
        initial=Protocol.SampleCondition.OPTIMAL,
        widget=forms.RadioSelect(
            attrs={
                "class": "h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition-colors duration-200"
            }
        ),
        help_text=_("Evalúe el estado de la muestra al recibirla"),
    )

    reception_notes = forms.CharField(
        label=_("Observaciones de recepción"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "rows": 3,
                "placeholder": _(
                    "Observaciones sobre el estado de la muestra, etiquetado, etc."
                ),
            }
        ),
    )

    discrepancies = forms.CharField(
        label=_("Discrepancias"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "rows": 3,
                "placeholder": _(
                    "Diferencias entre lo declarado en el protocolo y lo recibido"
                ),
            }
        ),
        help_text=_(
            "Indique si la cantidad, estado o descripción difiere de lo esperado"
        ),
    )

    def __init__(self, *args, protocol=None, **kwargs):
        """Initialize form with protocol-specific fields."""
        super().__init__(*args, **kwargs)
        self.protocol = protocol

        if protocol:
            # Add analysis-specific fields
            if protocol.analysis_type == Protocol.AnalysisType.CYTOLOGY:
                self.fields["number_slides_received"] = forms.IntegerField(
                    label=_("Portaobjetos recibidos"),
                    min_value=0,
                    widget=forms.NumberInput(
                        attrs={
                            "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                        }
                    ),
                    help_text=_("Cantidad de portaobjetos recibidos"),
                )
                # Set initial value from protocol
                if hasattr(protocol, "cytology_sample"):
                    self.fields[
                        "number_slides_received"
                    ].initial = protocol.cytology_sample.number_of_slides

            elif (
                protocol.analysis_type == Protocol.AnalysisType.HISTOPATHOLOGY
            ):
                self.fields["number_jars_received"] = forms.IntegerField(
                    label=_("Frascos recibidos"),
                    min_value=0,
                    widget=forms.NumberInput(
                        attrs={
                            "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                        }
                    ),
                    help_text=_("Cantidad de frascos recibidos"),
                )
                # Set initial value from protocol
                if hasattr(protocol, "histopathology_sample"):
                    self.fields[
                        "number_jars_received"
                    ].initial = (
                        protocol.histopathology_sample.number_of_containers
                    )

    def clean(self):
        """Validate reception data."""
        cleaned_data = super().clean()

        # If sample condition is rejected, require notes
        condition = cleaned_data.get("sample_condition")
        notes = cleaned_data.get("reception_notes", "").strip()

        if condition == Protocol.SampleCondition.REJECTED and not notes:
            raise ValidationError(
                {
                    "reception_notes": _(
                        "Debe indicar el motivo del rechazo de la muestra"
                    ),
                }
            )

        # Check for quantity discrepancies
        if self.protocol:
            if self.protocol.analysis_type == Protocol.AnalysisType.CYTOLOGY:
                expected = (
                    getattr(
                        self.protocol.cytology_sample, "number_of_slides", 0
                    )
                    if hasattr(self.protocol, "cytology_sample")
                    else 0
                )
                received = cleaned_data.get("number_slides_received", 0)
                if expected != received and not cleaned_data.get(
                    "discrepancies"
                ):
                    self.add_error(
                        "discrepancies",
                        _(
                            "Se esperaban %(expected)d portaobjetos pero se recibieron %(received)d. "
                            "Por favor documente esta discrepancia."
                        )
                        % {"expected": expected, "received": received},
                    )

            elif (
                self.protocol.analysis_type
                == Protocol.AnalysisType.HISTOPATHOLOGY
            ):
                expected = (
                    getattr(
                        self.protocol.histopathology_sample,
                        "number_of_containers",
                        0,
                    )
                    if hasattr(self.protocol, "histopathology_sample")
                    else 0
                )
                received = cleaned_data.get("number_jars_received", 0)
                if expected != received and not cleaned_data.get(
                    "discrepancies"
                ):
                    self.add_error(
                        "discrepancies",
                        _(
                            "Se esperaban %(expected)d frascos pero se recibieron %(received)d. "
                            "Por favor documente esta discrepancia."
                        )
                        % {"expected": expected, "received": received},
                    )

        return cleaned_data


class DiscrepancyReportForm(forms.Form):
    """Form to report discrepancies in sample reception."""

    DISCREPANCY_TYPE_CHOICES = [
        ("", _("Seleccionar tipo")),
        ("quantity", _("Cantidad de muestras no coincide")),
        ("missing_label", _("Muestra sin etiquetar")),
        ("damaged", _("Muestra dañada")),
        ("wrong_sample", _("Muestra no coincide con descripción")),
        ("other", _("Otro")),
    ]

    discrepancy_type = forms.ChoiceField(
        label=_("Tipo de discrepancia"),
        choices=DISCREPANCY_TYPE_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white"
            }
        ),
    )

    expected = forms.CharField(
        label=_("Esperado"),
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
            }
        ),
        help_text=_("Qué se esperaba según el protocolo"),
    )

    received = forms.CharField(
        label=_("Recibido"),
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
            }
        ),
        help_text=_("Qué se recibió realmente"),
    )

    description = forms.CharField(
        label=_("Descripción detallada"),
        widget=forms.Textarea(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "rows": 4,
            }
        ),
    )

    action_taken = forms.ChoiceField(
        label=_("Acción tomada"),
        choices=[
            ("notify", _("Notificar al veterinario")),
            ("accept", _("Aceptar con observación")),
            ("reject", _("Rechazar muestra")),
            ("pending", _("Pendiente de resolución")),
        ],
        widget=forms.RadioSelect(
            attrs={
                "class": "h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition-colors duration-200"
            }
        ),
    )

    def clean(self):
        """Validate discrepancy report."""
        cleaned_data = super().clean()
        discrepancy_type = cleaned_data.get("discrepancy_type")

        # For quantity discrepancies, require expected and received values
        if discrepancy_type == "quantity" and (
            not cleaned_data.get("expected")
            or not cleaned_data.get("received")
        ):
            raise ValidationError(
                _(
                    "Para discrepancias de cantidad, debe indicar tanto lo esperado como lo recibido"
                )
            )

        return cleaned_data


# ============================================================================
# PROCESSING FORMS (STEP 05)
# ============================================================================


class CassetteForm(forms.ModelForm):
    """Form for creating cassettes for histopathology samples."""

    class Meta:
        model = Cassette
        fields = [
            "material_incluido",
            "tipo_cassette",
            "color_cassette",
            "observaciones",
        ]
        widgets = {
            "material_incluido": forms.Textarea(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                    "rows": 2,
                    "placeholder": _(
                        "Ej: Fragmento de hígado con lesión nodular de 2cm"
                    ),
                }
            ),
            "tipo_cassette": forms.Select(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white"
                }
            ),
            "color_cassette": forms.Select(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white"
                }
            ),
            "observaciones": forms.Textarea(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                    "rows": 2,
                }
            ),
        }


class BulkCassetteForm(forms.Form):
    """Form for creating multiple cassettes at once."""

    # Number of cassettes to create
    number_of_cassettes = forms.IntegerField(
        label=_("Número de cassettes"),
        min_value=1,
        max_value=20,
        initial=1,
        widget=forms.NumberInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
            }
        ),
        help_text=_("Cantidad de cassettes a crear (máximo 20)"),
    )


class CassetteStageUpdateForm(forms.Form):
    """Form for updating cassette processing stage."""

    STAGE_CHOICES = [
        ("encasetado", _("Encasetado")),
        ("fijacion", _("Fijación")),
        ("inclusion", _("Inclusión")),
        ("entacado", _("Entacado")),
    ]

    etapa = forms.ChoiceField(
        label=_("Etapa de procesamiento"),
        choices=STAGE_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white"
            }
        ),
    )

    observaciones = forms.CharField(
        label=_("Observaciones"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "rows": 3,
                "placeholder": _(
                    "Observaciones sobre esta etapa del procesamiento"
                ),
            }
        ),
    )


class SlideForm(forms.ModelForm):
    """Form for creating slides."""

    class Meta:
        model = Slide
        fields = [
            "campo",
            "tecnica_coloracion",
            "observaciones",
        ]
        widgets = {
            "campo": forms.NumberInput(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                }
            ),
            "tecnica_coloracion": forms.TextInput(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                    "placeholder": _("Ej: Hematoxilina-Eosina, PAS, Masson"),
                }
            ),
            "observaciones": forms.Textarea(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                    "rows": 2,
                }
            ),
        }


class CytologySlideForm(forms.Form):
    """Form for creating cytology slides."""

    numero_slides = forms.IntegerField(
        label=_("Número de portaobjetos"),
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
            }
        ),
        help_text=_("Cantidad de portaobjetos a crear"),
    )

    tecnica_coloracion = forms.CharField(
        label=_("Técnica de coloración"),
        max_length=200,
        initial="Diff-Quick",
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": _("Ej: Diff-Quick, Papanicolau"),
            }
        ),
    )

    observaciones = forms.CharField(
        label=_("Observaciones"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "rows": 2,
            }
        ),
    )


class HistopathologySlideForm(forms.Form):
    """Form for creating histopathology slides with cassette association."""

    cassette_ids = forms.MultipleChoiceField(
        label=_("Cassettes a incluir"),
        widget=forms.CheckboxSelectMultiple(
            attrs={
                "class": "h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition-colors duration-200"
            }
        ),
        help_text=_(
            "Seleccione uno o más cassettes para montar en este portaobjetos"
        ),
    )

    tecnica_coloracion = forms.CharField(
        label=_("Técnica de coloración"),
        max_length=200,
        initial="Hematoxilina-Eosina",
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": _("Ej: Hematoxilina-Eosina, PAS, Masson"),
            }
        ),
    )

    campo = forms.IntegerField(
        label=_("Campo"),
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
            }
        ),
        help_text=_("Número de campo del portaobjetos"),
    )

    observaciones = forms.CharField(
        label=_("Observaciones"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "rows": 2,
            }
        ),
    )

    def __init__(self, *args, cassette_choices=None, **kwargs):
        """Initialize form with available cassettes."""
        super().__init__(*args, **kwargs)
        if cassette_choices:
            self.fields["cassette_ids"].choices = cassette_choices

    def clean_cassette_ids(self):
        """Validate that at least one cassette is selected."""
        cassette_ids = self.cleaned_data.get("cassette_ids", [])
        if not cassette_ids:
            raise ValidationError(_("Debe seleccionar al menos un cassette"))
        if len(cassette_ids) > 3:
            raise ValidationError(
                _("No se pueden montar más de 3 cassettes en un portaobjetos")
            )
        return cassette_ids


class SlideStageUpdateForm(forms.Form):
    """Form for updating slide processing stage."""

    STAGE_CHOICES = [
        ("montaje", _("Montaje")),
        ("coloracion", _("Coloración")),
    ]

    etapa = forms.ChoiceField(
        label=_("Etapa de procesamiento"),
        choices=STAGE_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white"
            }
        ),
    )

    observaciones = forms.CharField(
        label=_("Observaciones"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "rows": 3,
                "placeholder": _(
                    "Observaciones sobre esta etapa del procesamiento"
                ),
            }
        ),
    )


class SlideQualityForm(forms.Form):
    """Form for assessing slide quality."""

    calidad = forms.ChoiceField(
        label=_("Calidad del portaobjetos"),
        choices=Slide.Quality.choices,
        widget=forms.RadioSelect(
            attrs={
                "class": "h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition-colors duration-200"
            }
        ),
        help_text=_("Evalúe la calidad del corte y coloración"),
    )

    observaciones = forms.CharField(
        label=_("Observaciones"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "rows": 3,
                "placeholder": _(
                    "Comentarios sobre la calidad del portaobjetos"
                ),
            }
        ),
    )

    def clean_observaciones(self):
        """Require observations for deficient quality."""
        observaciones = self.cleaned_data.get("observaciones", "").strip()
        calidad = self.data.get("calidad")

        if calidad == Slide.Quality.DEFICIENTE and not observaciones:
            raise ValidationError(
                _("Debe indicar el motivo de la calidad deficiente")
            )

        return observaciones
