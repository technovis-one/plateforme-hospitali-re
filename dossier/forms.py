from django import forms

from .models import Consultation


class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ("compte_rendu", "ordonnance")
        labels = {
            "compte_rendu": "Compte-rendu de consultation",
            "ordonnance": "Ordonnance / prescription",
        }
        help_texts = {
            "compte_rendu": "Saisis les informations nécessaires au suivi du patient.",
            "ordonnance": "Laisse ce champ vide si aucune ordonnance n’est émise.",
        }
        widgets = {
            "compte_rendu": forms.Textarea(attrs={"rows": 7, "autocomplete": "off"}),
            "ordonnance": forms.Textarea(attrs={"rows": 6, "autocomplete": "off"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        compte_rendu = (cleaned_data.get("compte_rendu") or "").strip()
        ordonnance = (cleaned_data.get("ordonnance") or "").strip()
        if not compte_rendu and not ordonnance:
            raise forms.ValidationError(
                "Renseigne le compte-rendu ou l’ordonnance avant l’enregistrement."
            )
        return cleaned_data
