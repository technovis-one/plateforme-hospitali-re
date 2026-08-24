from django.db import models
from django.db import models

class RendezVous(models.Model):
    STATUT_ATTENTE = 'attente'
    STATUT_CONFIRME = 'confirme'
    STATUT_ANNULE = 'annule'
    STATUT_TERMINE = 'termine'
    STATUT_CHOICES = [
        (STATUT_ATTENTE, 'En attente'),
        (STATUT_CONFIRME, 'ConfirmÃ©'),
        (STATUT_ANNULE, 'AnnulÃ©'),
        (STATUT_TERMINE, 'TerminÃ©'),
    ]

    TYPE_PRESENTIEL = 'presentiel'
    TYPE_TELECONSULTATION = 'teleconsultation'
    TYPE_CHOICES = [
        (TYPE_PRESENTIEL, 'PrÃ©sentiel'),
        (TYPE_TELECONSULTATION, 'TÃ©lÃ©consultation'),
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
        return f"RDV {self.patient} avec {self.medecin} le {self.date} Ã  {self.heure}"
