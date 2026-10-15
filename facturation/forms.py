from decimal import Decimal

from django import forms

from comptes.models import Patient
from dossier.models import Consultation
from .models import Facture


class FactureCreateForm(forms.ModelForm):
    consultation = forms.ModelChoiceField(
        queryset=Consultation.objects.select_related(
            "rendez_vous__patient", "rendez_vous__medecin"
        ).order_by("-date", "-pk"),
        required=False,
        empty_label="Aucune consultation liée",
        label="Consultation (facultatif)",
    )
    montant = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        label="Montant (FCFA)",
    )

    class Meta:
        model = Facture
        fields = ("patient", "consultation", "montant")
        labels = {"patient": "Patient concerné"}
        widgets = {
            "patient": forms.Select(attrs={"class": "nh-invoice-form__input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["patient"].queryset = Patient.objects.order_by("last_name", "first_name")
        self.fields["patient"].widget.attrs["class"] = "nh-invoice-form__input"
        self.fields["consultation"].widget.attrs["class"] = "nh-invoice-form__input"
        self.fields["montant"].widget.attrs.update({
            "class": "nh-invoice-form__input",
            "min": "0.01",
            "step": "0.01",
            "inputmode": "decimal",
        })

    def clean(self):
        cleaned = super().clean()
        patient = cleaned.get("patient")
        consultation = cleaned.get("consultation")
        if patient and consultation:
            if consultation.rendez_vous.patient_id != patient.pk:
                self.add_error("consultation", "Cette consultation appartient à un autre patient.")
            elif Facture.objects.filter(consultation=consultation).exists():
                self.add_error("consultation", "Une facture existe déjà pour cette consultation.")
        return cleaned
