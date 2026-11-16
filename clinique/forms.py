from django import forms
from stocks.models import Medicament

from comptes.models import Medecin
from .models import Clinique, DisponibiliteMedecin, MembreEquipe, Salle, Service


class CliniqueForm(forms.ModelForm):
    class Meta:
        model = Clinique
        fields = ("nom", "telephone", "email", "adresse", "ville", "pays", "site_web")
        widgets = {"adresse": forms.TextInput(attrs={"autocomplete": "street-address"})}


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ("nom", "specialite", "description", "actif")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class SalleForm(forms.ModelForm):
    class Meta:
        model = Salle
        fields = ("nom", "code", "service", "capacite", "equipements", "active")
        widgets = {"equipements": forms.Textarea(attrs={"rows": 2})}


class DisponibiliteMedecinForm(forms.ModelForm):
    class Meta:
        model = DisponibiliteMedecin
        fields = ("medecin", "service", "salle", "jour", "heure_debut", "heure_fin", "actif")
        widgets = {"heure_debut": forms.TimeInput(attrs={"type": "time"}), "heure_fin": forms.TimeInput(attrs={"type": "time"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["medecin"].queryset = Medecin.objects.filter(is_active=True).order_by("last_name", "first_name")
        self.fields["service"].queryset = Service.objects.filter(actif=True).order_by("nom")
        self.fields["salle"].queryset = Salle.objects.filter(active=True).order_by("code")


class MembreEquipeForm(forms.ModelForm):
    class Meta:
        model = MembreEquipe
        fields = ("nom", "fonction", "telephone", "email", "service", "actif")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = Service.objects.filter(actif=True).order_by("nom")


class ArticleStockForm(forms.ModelForm):
    stock_initial = forms.IntegerField(min_value=0, initial=0, label="Quantité initiale", help_text="Une entrée d’inventaire sera inscrite dans l’historique si la quantité est supérieure à zéro.")

    class Meta:
        model = Medicament
        fields = ("nom", "categorie", "unite", "seuil_alerte", "date_peremption", "actif")
        widgets = {"date_peremption": forms.DateInput(attrs={"type": "date"})}


class ArticleStockEditForm(forms.ModelForm):
    class Meta:
        model = Medicament
        fields = ("nom", "categorie", "unite", "seuil_alerte", "date_peremption", "actif")
        widgets = {"date_peremption": forms.DateInput(attrs={"type": "date"})}


class MouvementStockForm(forms.Form):
    article = forms.ModelChoiceField(queryset=None, label="Article")
    type_mouvement = forms.ChoiceField(choices=(("entree", "Entrée"), ("sortie", "Sortie")), label="Type")
    quantite = forms.IntegerField(min_value=1, label="Quantité")
    motif = forms.CharField(max_length=180, label="Motif", widget=forms.TextInput(attrs={"placeholder": "Réapprovisionnement, utilisation, correction…"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["article"].queryset = Medicament.objects.filter(actif=True).order_by("nom")
