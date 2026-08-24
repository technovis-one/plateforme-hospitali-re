from django.db import models
from django.db import models

class RendezVous(models.Model):
    STATUT_ATTENTE = 'attente'
    STATUT_CONFIRME = 'confirme'
    STATUT_ANNULE = 'annule'
    STATUT_TERMINE = 'termine'
    STATUT_CHOICES = [
        (STATUT_ATTENTE, 'En attente'),
        (STATUT_CONFIRME, 'Confirmé'),
        (STATUT_ANNULE, 'Annulé'),
        (STATUT_TERMINE, 'Terminé'),
    ]

    TYPE_PRESENTIEL = 'presentiel'
    TYPE_TELECONSULTATION = 'teleconsultation'
    TYPE_CHOICES = [
        (TYPE_PRESENTIEL, 'Présentiel'),
        (TYPE_TELECONSULTATION, 'Téléconsultation'),
    ]

    patient = models.ForeignKey(
        'comptes.Patient', on_delete=models.CASCADE, related_name='rendezvous'
    )
    medecin = models.ForeignKey(
        'comptes.Medecin', on_delete=models.CASCADE, related_name='rendezvous'
    )
    date = models.DateField()
    heure = models.TimeField()
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default=STATUT_ATTENTE)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_PRESENTIEL)

    def __str__(self):
        return f"RDV {self.patient} avec {self.medecin} le {self.date} à {self.heure}"
# Create your models here.
