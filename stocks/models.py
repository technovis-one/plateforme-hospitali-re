from django.db import models
from django.db import models


class Medicament(models.Model):
    nom = models.CharField(max_length=150)
    quantite_stock = models.PositiveIntegerField(default=0)
    seuil_alerte = models.PositiveIntegerField(default=10)
    date_peremption = models.DateField()

    def __str__(self):
        return self.nom


class Prescription(models.Model):
    """Classe d'association Consultation <-> Medicament (quantitÃ©, posologie)."""
    consultation = models.ForeignKey('dossier.Consultation', on_delete=models.CASCADE)
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)
    posologie = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.medicament} x{self.quantite} ({self.consultation})"
