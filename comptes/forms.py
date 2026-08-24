from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Patient


class ConnexionForm(forms.Form):
    email = forms.EmailField(label="Adresse email")
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)


class InscriptionPatientForm(UserCreationForm):
    email = forms.EmailField(required=True)
    date_naissance = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    num_tel = forms.CharField(max_length=20)
    adresse = forms.CharField(max_length=255)

    class Meta:
        model = Patient
        fields = ['username', 'first_name', 'last_name', 'email',
                   'date_naissance', 'num_tel', 'adresse', 'password1', 'password2']

    def save(self, commit=True):
        patient = super().save(commit=False)
        patient.role = Patient.ROLE_PATIENT
        if commit:
            patient.save()
        return patient