from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import Patient, Utilisateur


INPUT_CLASS = "input input-bordered w-full"


class ConnexionForm(forms.Form):
    email = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "vous@exemple.com",
            }
        ),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "••••••••",
            }
        ),
    )


class InscriptionPatientForm(UserCreationForm):
    photo = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "class": "file-input file-input-bordered w-full",
            }
        ),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "vous@exemple.com",
            }
        ),
    )
    date_naissance = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": INPUT_CLASS,
            }
        ),
    )
    num_tel = forms.CharField(
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "+237 6XX XX XX XX",
            }
        ),
    )
    adresse = forms.CharField(
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "Votre adresse",
            }
        ),
    )

    class Meta:
        model = Patient
        fields = [
            "photo",
            "username",
            "first_name",
            "last_name",
            "email",
            "date_naissance",
            "num_tel",
            "adresse",
            "password1",
            "password2",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": INPUT_CLASS, "placeholder": "Nom d'utilisateur"}
        )
        self.fields["first_name"].widget.attrs.update(
            {"class": INPUT_CLASS, "placeholder": "Prénom"}
        )
        self.fields["last_name"].widget.attrs.update(
            {"class": INPUT_CLASS, "placeholder": "Nom"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": INPUT_CLASS, "placeholder": "••••••••"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": INPUT_CLASS, "placeholder": "••••••••"}
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Utilisateur.objects.filter(email__iexact=email).exists():
            raise ValidationError("Cette adresse e-mail est déjà associée à un compte.")
        return email

    def save(self, commit=True):
        patient = super().save(commit=False)
        patient.role = Patient.ROLE_PATIENT
        patient.is_active = False
        patient.is_staff = False
        patient.is_superuser = False
        if commit:
            patient.save()
        return patient
