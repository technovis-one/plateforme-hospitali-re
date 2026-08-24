from django.db import models
from django.db import models


class Facture(models.Model):
    STATUT_ATTENTE = 'attente'
    STATUT_PAYEE = 'payee'
    STATUT_ANNULEE = 'annulee'
    STATUT_CHOICES = [
        (STATUT_ATTENTE, 'En attente'),
        (STATUT_PAYEE, 'Payée'),
        (STATUT_ANNULEE, 'Annulée'),
    ]

    patient = models.ForeignKey(
        'comptes.Patient', on_delete=models.CASCADE, related_name='factures'
    )
    consultation = models.OneToOneField(
        'dossier.Consultation', on_delete=models.SET_NULL, null=True, blank=True, related_name='facture'
    )
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default=STATUT_ATTENTE)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Facture {self.id} — {self.patient} — {self.montant} FCFA"