from django import forms
from django.utils import timezone

from comptes.models import Medecin
from .models import RendezVous


class RendezVousForm(forms.ModelForm):
    type = forms.ChoiceField(
        label="Mode de consultation",
        choices=(
            (RendezVous.TYPE_PRESENTIEL, "Présentiel"),
            (RendezVous.TYPE_TELECONSULTATION, "Téléconsultation"),
        ),
        widget=forms.Select(attrs={"class": "nh-booking__input"}),
    )
    date = forms.DateField(
        label="Date souhaitée",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            attrs={"class": "nh-booking__input", "type": "date"},
            format="%Y-%m-%d",
        ),
    )
    heure = forms.TimeField(
        label="Heure souhaitée",
        input_formats=["%H:%M", "%H:%M:%S"],
        widget=forms.TimeInput(
            attrs={"class": "nh-booking__input", "type": "time", "step": "900"},
            format="%H:%M",
        ),
    )

    class Meta:
        model = RendezVous
        fields = ("medecin", "date", "heure", "type")
        widgets = {
            "medecin": forms.Select(attrs={"class": "nh-booking__input"}),
            "type": forms.Select(attrs={"class": "nh-booking__input"}),
        }
        labels = {
            "medecin": "Médecin",
            "type": "Mode de consultation",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["medecin"].queryset = Medecin.objects.filter(
            is_active=True,
            role="medecin",
        ).order_by("last_name", "first_name")
        self.fields["medecin"].empty_label = "Choisissez un médecin"
        self.fields["date"].widget.attrs["min"] = timezone.localdate().isoformat()
        for field in self.fields.values():
            field.help_text = ""

    def clean_date(self):
        date_rdv = self.cleaned_data["date"]
        if date_rdv < timezone.localdate():
            raise forms.ValidationError("Choisissez une date à venir.")
        return date_rdv

    def clean(self):
        cleaned_data = super().clean()
        medecin = cleaned_data.get("medecin")
        date_rdv = cleaned_data.get("date")
        heure = cleaned_data.get("heure")

        now = timezone.now()
        local_now = timezone.localtime(now) if timezone.is_aware(now) else now
        if date_rdv and heure and date_rdv == timezone.localdate():
            if heure <= local_now.time().replace(second=0, microsecond=0):
                self.add_error("heure", "Choisissez une heure future.")

        if medecin and date_rdv and heure:
            slot_taken = RendezVous.objects.filter(
                medecin=medecin,
                date=date_rdv,
                heure=heure,
            ).exclude(statut=RendezVous.STATUT_ANNULE).exists()
            if slot_taken:
                self.add_error(
                    "heure",
                    "Ce créneau est déjà demandé. Choisissez une autre heure.",
                )

        return cleaned_data
