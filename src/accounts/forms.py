import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Address, Histopathologist, User, Veterinarian


class ResendVerificationEmailForm(forms.Form):
    """Form for resending verification email."""

    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(
            attrs={
                "class": "appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm",
                "placeholder": "correo@ejemplo.com",
                "autofocus": True,
            }
        ),
    )


class UserLoginForm(AuthenticationForm):
    """Custom login form using email instead of username."""

    error_messages = {
        "invalid_login": _(
            "Por favor, ingrese un email y contraseña correctos. "
            "Tenga en cuenta que ambos campos pueden distinguir entre mayúsculas y minúsculas. "
            "Si los datos son incorrectos, verifique su información."
        ),
        "inactive": _("Esta cuenta está desactivada."),
    }

    def clean(self):
        """Override clean to check for inactive users and email verification before authentication."""
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username and password:
            # Check if user exists and handle verification status
            try:
                from .models import User

                user = User.objects.get(email=username)

                # Check email verification first (for veterinarians)
                if (
                    user.role == User.Role.VETERINARIO
                    and not user.email_verified
                ):
                    # Log failed login attempt for audit
                    from .models import AuthAuditLog

                    AuthAuditLog.objects.create(
                        user=user,
                        email=user.email,
                        action=AuthAuditLog.Action.LOGIN_FAILED,
                        details="Email not verified",
                    )
                    raise forms.ValidationError(
                        _("Debe verificar su email antes de iniciar sesión."),
                        code="email_not_verified",
                    )

                # Check if account is inactive (for other reasons)
                if not user.is_active:
                    raise forms.ValidationError(
                        self.error_messages["inactive"],
                        code="inactive",
                    )
            except User.DoesNotExist:
                pass  # Let the parent clean() handle this

        return super().clean()

    def confirm_login_allowed(self, user):
        """Check if the given user may log in."""
        # Check email verification first (for veterinarians)
        if user.role == User.Role.VETERINARIO and not user.email_verified:
            # Log failed login attempt for audit
            from .models import AuthAuditLog

            AuthAuditLog.objects.create(
                user=user,
                email=user.email,
                action=AuthAuditLog.Action.LOGIN_FAILED,
                details="Email not verified",
            )
            raise forms.ValidationError(
                _("Debe verificar su email antes de iniciar sesión."),
                code="email_not_verified",
            )

        # Check if account is inactive (for other reasons)
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages["inactive"],
                code="inactive",
            )

    username = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": "correo@ejemplo.com",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": "Contraseña",
            }
        ),
    )
    remember_me = forms.BooleanField(
        label=_("Remember me"),
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition-colors duration-200"
            }
        ),
    )


class VeterinarianRegistrationForm(UserCreationForm):
    """Registration form for veterinarian clients."""

    email = forms.EmailField(
        label=_("Email"),
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": "correo@ejemplo.com",
            }
        ),
    )
    first_name = forms.CharField(
        label=_("First Name"),
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": "Nombre",
            }
        ),
    )
    last_name = forms.CharField(
        label=_("Last Name"),
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": "Apellido",
            }
        ),
    )
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": "Contraseña (mínimo 8 caracteres)",
            }
        ),
        help_text=_("Su contraseña debe tener al menos 8 caracteres."),
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": "Confirmar contraseña",
            }
        ),
        strip=False,
        help_text=_(
            "Ingrese la misma contraseña que antes, para verificación."
        ),
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove username field as we use email
        if "username" in self.fields:
            del self.fields["username"]

    def clean_email(self):
        """Validate email is unique."""
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("Este email ya está registrado."))
        return email.lower()

    def save(self, commit=True):
        """Save user with veterinarian role."""
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower()
        user.username = self.cleaned_data[
            "email"
        ].lower()  # Use email as username
        user.role = User.Role.VETERINARIO
        if commit:
            user.save()
        return user


class HistopathologistCreationForm(forms.Form):
    """
    Form for creating histopathologist users with complete profile.

    Creates both User account and Histopathologist profile in a single form.
    Used by administrators to create internal laboratory staff.
    """

    # User account fields
    email = forms.EmailField(
        label=_("Email"),
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": "correo@ejemplo.com",
            }
        ),
        help_text=_("Email que usará para iniciar sesión"),
    )
    first_name = forms.CharField(
        label=_("Nombre"),
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": "Nombre",
            }
        ),
    )
    last_name = forms.CharField(
        label=_("Apellido"),
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": "Apellido",
            }
        ),
    )
    password1 = forms.CharField(
        label=_("Contraseña"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": "Contraseña (mínimo 8 caracteres)",
            }
        ),
        help_text=_("La contraseña debe tener al menos 8 caracteres."),
    )
    password2 = forms.CharField(
        label=_("Confirmar contraseña"),
        widget=forms.PasswordInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": "Confirmar contraseña",
            }
        ),
        strip=False,
        help_text=_(
            "Ingrese la misma contraseña que antes, para verificación."
        ),
    )

    # Histopathologist profile fields
    license_number = forms.CharField(
        label=_("Número de matrícula"),
        max_length=50,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": "Ej: HP-12345",
            }
        ),
        help_text=_("Número de matrícula profesional único"),
    )
    position = forms.CharField(
        label=_("Cargo"),
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": "Ej: Profesor Titular, Jefe de TP",
            }
        ),
        help_text=_("Cargo o posición en el laboratorio"),
    )
    specialty = forms.CharField(
        label=_("Especialidad"),
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": "Ej: Patología Veterinaria",
            }
        ),
        help_text=_("Especialidad o área de expertise"),
    )
    phone_number = forms.CharField(
        label=_("Teléfono"),
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": "+54 341 1234567",
            }
        ),
        help_text=_("Número de teléfono de contacto"),
    )
    signature_image = forms.ImageField(
        label=_("Firma digital"),
        required=False,
        widget=forms.FileInput(
            attrs={
                "class": "block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100",
                "accept": "image/*",
            }
        ),
        help_text=_("Imagen de la firma para incluir en informes (opcional)"),
    )

    def clean_email(self):
        """Validate email is unique."""
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email=email).exists():
            raise ValidationError(_("Este email ya está registrado."))
        return email.lower() if email else email

    def clean_license_number(self):
        """Validate license number is unique."""
        license_number = self.cleaned_data.get("license_number")
        if (
            license_number
            and Histopathologist.objects.filter(
                license_number=license_number
            ).exists()
        ):
            raise ValidationError(
                _("Este número de matrícula ya está registrado.")
            )
        return license_number

    def clean(self):
        """Validate password confirmation."""
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError(_("Las contraseñas no coinciden."))

        return cleaned_data

    def save(self):
        """
        Create both User account and Histopathologist profile.

        Returns:
            tuple: (user, histopathologist) instances created
        """
        # Create User account
        user = User.objects.create_user(
            email=self.cleaned_data["email"].lower(),
            username=self.cleaned_data["email"].lower(),
            password=self.cleaned_data["password1"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            role=User.Role.HISTOPATOLOGO,
            is_active=True,
            email_verified=True,  # Internal users don't need verification
            is_staff=True,  # Allow admin access
        )

        # Create Histopathologist profile
        histopathologist = Histopathologist.objects.create(
            user=user,
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            license_number=self.cleaned_data["license_number"],
            position=self.cleaned_data.get("position", ""),
            specialty=self.cleaned_data.get("specialty", ""),
            phone_number=self.cleaned_data.get("phone_number", ""),
            signature_image=self.cleaned_data.get("signature_image"),
        )

        return user, histopathologist


class PasswordResetRequestForm(forms.Form):
    """Form for requesting password reset."""

    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": "correo@ejemplo.com",
                "autofocus": True,
            }
        ),
    )


class PasswordResetConfirmForm(forms.Form):
    """Form for setting new password."""

    password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": "Nueva contraseña",
                "autofocus": True,
            }
        ),
        strip=False,
        help_text=_("Su contraseña debe tener al menos 8 caracteres."),
    )
    password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200",
                "placeholder": "Confirmar nueva contraseña",
            }
        ),
    )

    def clean_password2(self):
        """Validate passwords match."""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(_("Las contraseñas no coinciden."))
        return password2

    def clean_password1(self):
        """Validate password strength."""
        password1 = self.cleaned_data.get("password1")
        if len(password1) < 8:
            raise ValidationError(
                _("La contraseña debe tener al menos 8 caracteres.")
            )
        return password1


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile information."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "block w-full h-10 px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                }
            ),
        }

    def clean_email(self):
        """Validate email is unique (excluding current user)."""
        email = self.cleaned_data.get("email")
        if (
            User.objects.filter(email=email)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise ValidationError(_("Este email ya está en uso."))
        return email.lower()


class VeterinarianProfileForm(forms.ModelForm):
    """Form for creating/editing veterinarian profile."""

    class Meta:
        model = Veterinarian
        fields = [
            "first_name",
            "last_name",
            "license_number",
            "dni",
            "cuil_cuit",
            "phone",
            "email",
        ]
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "placeholder": "Juan",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "placeholder": "Pérez",
                }
            ),
            "license_number": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "placeholder": "MP-12345",
                }
            ),
            "dni": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "placeholder": "12345678",
                }
            ),
            "cuil_cuit": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "placeholder": "20-12345678-9",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "placeholder": "+54 342 1234567",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "placeholder": "vet@example.com",
                }
            ),
        }
        labels = {
            "first_name": _("First Name"),
            "last_name": _("Last Name"),
            "license_number": _("License Number (Matrícula)"),
            "dni": _("DNI"),
            "cuil_cuit": _("CUIL/CUIT"),
            "phone": _("Phone"),
            "email": _("Email"),
        }
        help_texts = {
            "license_number": _(
                "Format: MP-XXXXX (example: MP-12345) (optional)"
            ),
            "dni": _("Documento Nacional de Identidad (7-8 dígitos)"),
            "cuil_cuit": _(
                "Código Único de Identificación Laboral. Formato: XX-XXXXXXXX-X"
            ),
            "phone": _("Argentine format: +54 XXX XXXXXXX"),
        }

    def clean_license_number(self):
        """Validate license number format (optional)."""
        license_number = (
            self.cleaned_data.get("license_number", "").strip().upper()
        )

        # If empty, return empty (field is now optional)
        if not license_number:
            return license_number

        # Validate format (MP-XXXXX or similar provincial patterns)
        # Accept various provincial prefixes followed by numbers
        pattern = r"^[A-Z]{2,3}-\d{4,6}$"
        if not re.match(pattern, license_number):
            raise ValidationError(
                _(
                    "Invalid license number format. Expected format: MP-12345 (province code + dash + numbers)"
                )
            )

        return license_number

    def clean_dni(self):
        """Validate DNI format (mandatory)."""
        dni = self.cleaned_data.get("dni", "").strip()

        # DNI is mandatory
        if not dni:
            raise ValidationError(_("DNI is required"))

        # Validate DNI format (7-8 digits)
        if not re.match(r"^\d{7,8}$", dni):
            raise ValidationError(_("DNI must contain 7-8 digits"))

        return dni

    def clean_cuil_cuit(self):
        """Validate CUIL/CUIT format (optional)."""
        cuil_cuit = self.cleaned_data.get("cuil_cuit", "").strip()

        # If empty, return empty (field is optional)
        if not cuil_cuit:
            return cuil_cuit

        # Validate format XX-XXXXXXXX-X
        pattern = r"^\d{2}-\d{8}-\d{1}$"
        if not re.match(pattern, cuil_cuit):
            raise ValidationError(
                _("Invalid CUIL/CUIT format. Expected format: XX-XXXXXXXX-X")
            )

        return cuil_cuit

    def clean_phone(self):
        """Validate phone number format."""
        phone = self.cleaned_data.get("phone", "").strip()

        # Basic validation for Argentine phone format
        # Accept formats like: +54 342 1234567, +54 11 12345678, etc.
        pattern = r"^\+54\s\d{2,4}\s\d{6,8}$"
        if not re.match(pattern, phone):
            raise ValidationError(
                _(
                    "Invalid phone format. Expected: +54 XXX XXXXXXX (example: +54 342 1234567)"
                )
            )

        return phone

    def clean_email(self):
        """Validate email uniqueness."""
        email = self.cleaned_data.get("email", "").strip().lower()

        # Check uniqueness (excluding current instance if editing)
        qs = Veterinarian.objects.filter(email=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError(_("This email is already registered."))

        return email


class AddressForm(forms.ModelForm):
    """Form for creating/editing address."""

    class Meta:
        model = Address
        fields = [
            "province",
            "locality",
            "street",
            "number",
            "floor",
            "apartment",
            "postal_code",
            "notes",
        ]
        widgets = {
            "province": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "placeholder": "Santa Fe",
                }
            ),
            "locality": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "placeholder": "Esperanza",
                }
            ),
            "street": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "placeholder": "San Martín",
                }
            ),
            "number": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "placeholder": "1234",
                }
            ),
            "floor": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "placeholder": "2",
                }
            ),
            "apartment": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "placeholder": "A",
                }
            ),
            "postal_code": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "placeholder": "3080",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "rows": "3",
                    "placeholder": "Additional address information...",
                }
            ),
        }
        labels = {
            "province": _("Province"),
            "locality": _("Locality"),
            "street": _("Street"),
            "number": _("Number"),
            "floor": _("Floor"),
            "apartment": _("Apartment"),
            "postal_code": _("Postal Code"),
            "notes": _("Notes"),
        }


class VeterinarianProfileCompleteForm(forms.Form):
    """
    Combined form for completing veterinarian profile during registration.
    Includes both veterinarian details and address.
    """

    # Veterinarian fields
    first_name = forms.CharField(
        label=_("First Name"),
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "placeholder": "Juan",
            }
        ),
    )
    last_name = forms.CharField(
        label=_("Last Name"),
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "placeholder": "Pérez",
            }
        ),
    )
    license_number = forms.CharField(
        label=_("License Number (Matrícula)"),
        max_length=50,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "placeholder": "MP-12345",
            }
        ),
        help_text=_("Format: MP-XXXXX (example: MP-12345) (optional)"),
    )
    dni = forms.CharField(
        label=_("DNI"),
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "placeholder": "12345678",
            }
        ),
        help_text=_("Documento Nacional de Identidad (7-8 dígitos)"),
    )
    cuil_cuit = forms.CharField(
        label=_("CUIL/CUIT"),
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "placeholder": "20-12345678-9",
            }
        ),
        help_text=_(
            "Código Único de Identificación Laboral. Formato: XX-XXXXXXXX-X"
        ),
    )
    phone = forms.CharField(
        label=_("Phone"),
        max_length=50,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "placeholder": "+54 342 1234567",
            }
        ),
        help_text=_("Argentine format: +54 XXX XXXXXXX"),
    )

    # Address fields
    province = forms.CharField(
        label=_("Province"),
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "placeholder": "Santa Fe",
            }
        ),
    )
    locality = forms.CharField(
        label=_("Locality"),
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "placeholder": "Esperanza",
            }
        ),
    )
    street = forms.CharField(
        label=_("Street"),
        max_length=200,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "placeholder": "San Martín",
            }
        ),
    )
    number = forms.CharField(
        label=_("Number"),
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "placeholder": "1234",
            }
        ),
    )
    floor = forms.CharField(
        label=_("Floor"),
        max_length=10,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "placeholder": "2",
            }
        ),
    )
    apartment = forms.CharField(
        label=_("Apartment"),
        max_length=10,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "placeholder": "A",
            }
        ),
    )
    postal_code = forms.CharField(
        label=_("Postal Code"),
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "placeholder": "3080",
            }
        ),
    )
    notes = forms.CharField(
        label=_("Additional Notes"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "rows": "3",
                "placeholder": "Additional address information...",
            }
        ),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        # Pre-fill email from user account
        if hasattr(user, "email"):
            self.initial["email"] = user.email

    def clean_license_number(self):
        """Validate license number format and uniqueness (optional)."""
        license_number = (
            self.cleaned_data.get("license_number", "").strip().upper()
        )

        # If empty, return empty (field is now optional)
        if not license_number:
            return license_number

        # Validate format (MP-XXXXX or similar provincial patterns)
        pattern = r"^[A-Z]{2,3}-\d{4,6}$"
        if not re.match(pattern, license_number):
            raise ValidationError(
                _(
                    "Invalid license number format. Expected format: MP-12345 (province code + dash + numbers)"
                )
            )

        # Check uniqueness
        if Veterinarian.objects.filter(license_number=license_number).exists():
            raise ValidationError(
                _("This license number is already registered.")
            )

        return license_number

    def clean_dni(self):
        """Validate DNI format (mandatory)."""
        dni = self.cleaned_data.get("dni", "").strip()

        # DNI is mandatory
        if not dni:
            raise ValidationError(_("DNI is required"))

        # Validate DNI format (7-8 digits)
        if not re.match(r"^\d{7,8}$", dni):
            raise ValidationError(_("DNI must contain 7-8 digits"))

        # Check uniqueness
        if Veterinarian.objects.filter(dni=dni).exists():
            raise ValidationError(_("This DNI is already registered."))

        return dni

    def clean_phone(self):
        """Validate phone number format."""
        phone = self.cleaned_data.get("phone", "").strip()

        # Basic validation for Argentine phone format
        pattern = r"^\+54\s\d{2,4}\s\d{6,8}$"
        if not re.match(pattern, phone):
            raise ValidationError(
                _(
                    "Invalid phone format. Expected: +54 XXX XXXXXXX (example: +54 342 1234567)"
                )
            )

        return phone

    def clean_cuil_cuit(self):
        """Validate CUIL/CUIT format."""
        cuil_cuit = self.cleaned_data.get("cuil_cuit", "").strip()

        # Validate format XX-XXXXXXXX-X
        pattern = r"^\d{2}-\d{8}-\d{1}$"
        if not re.match(pattern, cuil_cuit):
            raise ValidationError(
                _("Invalid CUIL/CUIT format. Expected format: XX-XXXXXXXX-X")
            )

        return cuil_cuit

    def save(self):
        """Create veterinarian profile and address."""
        # Create veterinarian profile
        veterinarian = Veterinarian.objects.create(
            user=self.user,
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            license_number=self.cleaned_data.get("license_number", ""),
            dni=self.cleaned_data.get("dni", ""),
            cuil_cuit=self.cleaned_data["cuil_cuit"],
            phone=self.cleaned_data["phone"],
            email=self.user.email,
        )

        # Create address
        Address.objects.create(
            veterinarian=veterinarian,
            province=self.cleaned_data["province"],
            locality=self.cleaned_data["locality"],
            street=self.cleaned_data["street"],
            number=self.cleaned_data["number"],
            floor=self.cleaned_data.get("floor", ""),
            apartment=self.cleaned_data.get("apartment", ""),
            postal_code=self.cleaned_data.get("postal_code", ""),
            notes=self.cleaned_data.get("notes", ""),
        )

        return veterinarian


class VeterinarianProfileEditForm(forms.ModelForm):
    """
    Form for editing veterinarian profile with address.
    """

    # Address fields
    province = forms.CharField(
        label=_("Province"),
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "placeholder": "Santa Fe",
            }
        ),
    )
    locality = forms.CharField(
        label=_("Locality"),
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "placeholder": "Esperanza",
            }
        ),
    )
    street = forms.CharField(
        label=_("Street"),
        max_length=200,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "placeholder": "San Martín",
            }
        ),
    )
    number = forms.CharField(
        label=_("Number"),
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "placeholder": "1234",
            }
        ),
    )
    floor = forms.CharField(
        label=_("Floor"),
        max_length=10,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "placeholder": "2",
            }
        ),
    )
    apartment = forms.CharField(
        label=_("Apartment"),
        max_length=10,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "placeholder": "A",
            }
        ),
    )
    postal_code = forms.CharField(
        label=_("Postal Code"),
        max_length=10,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "placeholder": "3080",
            }
        ),
    )
    notes = forms.CharField(
        label=_("Notes"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                "rows": "3",
                "placeholder": "Additional address information...",
            }
        ),
    )

    class Meta:
        model = Veterinarian
        fields = [
            "first_name",
            "last_name",
            "license_number",
            "dni",
            "cuil_cuit",
            "phone",
            "email",
        ]
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "placeholder": "Juan",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "placeholder": "Pérez",
                }
            ),
            "license_number": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "placeholder": "MP-12345",
                }
            ),
            "dni": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "placeholder": "12345678",
                }
            ),
            "cuil_cuit": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "placeholder": "20-12345678-9",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "placeholder": "+54 342 1234567",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "placeholder": "vet@example.com",
                }
            ),
        }
        labels = {
            "first_name": _("First Name"),
            "last_name": _("Last Name"),
            "license_number": _("License Number (Matrícula)"),
            "dni": _("DNI"),
            "cuil_cuit": _("CUIL/CUIT"),
            "phone": _("Phone"),
            "email": _("Email"),
        }
        help_texts = {
            "license_number": _(
                "Format: MP-XXXXX (example: MP-12345) (optional)"
            ),
            "dni": _("Documento Nacional de Identidad (7-8 dígitos)"),
            "cuil_cuit": _(
                "Código Único de Identificación Laboral. Formato: XX-XXXXXXXX-X"
            ),
            "phone": _("Argentine format: +54 XXX XXXXXXX"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize address fields with current values
        if self.instance and self.instance.pk:
            try:
                address = self.instance.address
                if address:
                    self.fields["province"].initial = address.province
                    self.fields["locality"].initial = address.locality
                    self.fields["street"].initial = address.street
                    self.fields["number"].initial = address.number
                    self.fields["floor"].initial = address.floor
                    self.fields["apartment"].initial = address.apartment
                    self.fields["postal_code"].initial = address.postal_code
                    self.fields["notes"].initial = address.notes
            except Address.DoesNotExist:
                pass

    def clean_license_number(self):
        """Validate license number format (optional)."""
        license_number = (
            self.cleaned_data.get("license_number", "").strip().upper()
        )

        # If empty, return empty (field is now optional)
        if not license_number:
            return license_number

        # Validate format (MP-XXXXX or similar provincial patterns)
        # Accept various provincial prefixes followed by numbers
        pattern = r"^[A-Z]{2,3}-\d{4,6}$"
        if not re.match(pattern, license_number):
            raise ValidationError(
                _(
                    "Invalid license number format. Expected format: MP-12345 (province code + dash + numbers)"
                )
            )

        return license_number

    def clean_cuil_cuit(self):
        """Validate CUIL/CUIT format."""
        cuil_cuit = self.cleaned_data.get("cuil_cuit", "").strip()

        # Validate format XX-XXXXXXXX-X
        pattern = r"^\d{2}-\d{8}-\d{1}$"
        if not re.match(pattern, cuil_cuit):
            raise ValidationError(
                _("Invalid CUIL/CUIT format. Expected format: XX-XXXXXXXX-X")
            )

        return cuil_cuit

    def clean_phone(self):
        """Validate phone number format."""
        phone = self.cleaned_data.get("phone", "").strip()

        # Basic validation for Argentine phone format
        # Accept formats like: +54 342 1234567, +54 11 12345678, etc.
        pattern = r"^\+54\s\d{2,4}\s\d{6,8}$"
        if not re.match(pattern, phone):
            raise ValidationError(
                _(
                    "Invalid phone format. Expected: +54 XXX XXXXXXX (example: +54 342 1234567)"
                )
            )

        return phone

    def clean_email(self):
        """Validate email uniqueness."""
        email = self.cleaned_data.get("email", "").strip().lower()

        # Check uniqueness (excluding current instance if editing)
        qs = Veterinarian.objects.filter(email=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError(_("This email is already registered."))

        return email

    def save(self, commit=True):
        """Save veterinarian and address."""
        veterinarian = super().save(commit=commit)

        if commit:
            # Update or create address
            try:
                address = veterinarian.address
                address.province = self.cleaned_data["province"]
                address.locality = self.cleaned_data["locality"]
                address.street = self.cleaned_data["street"]
                address.number = self.cleaned_data["number"]
                address.floor = self.cleaned_data.get("floor", "")
                address.apartment = self.cleaned_data.get("apartment", "")
                address.postal_code = self.cleaned_data.get("postal_code", "")
                address.notes = self.cleaned_data.get("notes", "")
                address.save()
            except Address.DoesNotExist:
                # Create new address
                Address.objects.create(
                    veterinarian=veterinarian,
                    province=self.cleaned_data["province"],
                    locality=self.cleaned_data["locality"],
                    street=self.cleaned_data["street"],
                    number=self.cleaned_data["number"],
                    floor=self.cleaned_data.get("floor", ""),
                    apartment=self.cleaned_data.get("apartment", ""),
                    postal_code=self.cleaned_data.get("postal_code", ""),
                    notes=self.cleaned_data.get("notes", ""),
                )

        return veterinarian
