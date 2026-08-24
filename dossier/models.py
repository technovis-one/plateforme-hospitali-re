from django.db import models
# dossier/models.py
from django.db import models


class DossierMedical(models.Model):
    patient = models.OneToOneField(
        'comptes.Patient', on_delete=models.CASCADE, related_name='dossier_medical'
    )
    antecedents = models.TextField(blank=True)
    allergies = models.TextField(blank=True)

    def __str__(self):
        return f"Dossier médical de {self.patient}"


class Consultation(models.Model):
    rendez_vous = models.OneToOneField(
        'rdv.RendezVous', on_delete=models.CASCADE, related_name='consultation'
    )
    compte_rendu = models.TextField(blank=True)
    ordonnance = models.TextField(blank=True)
    date = models.DateField(auto_now_add=True)
    medicaments = models.ManyToManyField(          # ← c'est cette ligne
        'stocks.Medicament', through='stocks.Prescription', related_name='consultations'
    )

    def __str__(self):
        return f"Consultation du {self.date} — {self.rendez_vous.patient}"