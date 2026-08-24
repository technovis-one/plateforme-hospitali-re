from django.db import models
from django.db import models


class SessionTelemedecine(models.Model):
    STATUT_OUVERTE = 'ouverte'
    STATUT_TERMINEE = 'terminee'
    STATUT_CHOICES = [
        (STATUT_OUVERTE, 'Ouverte'),
        (STATUT_TERMINEE, 'TerminÃ©e'),
    ]

    rendez_vous = models.OneToOneField(
        'rdv.RendezVous', on_delete=models.CASCADE, related_name='session_telemedecine'
    )
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default=STATUT_OUVERTE)
    date_ouverture = models.DateTimeField(auto_now_add=True)
    date_fermeture = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Session tÃ©lÃ©consultation â€” {self.rendez_vous}"


class Message(models.Model):
    session = models.ForeignKey(
        SessionTelemedecine, on_delete=models.CASCADE, related_name='messages'
    )
    auteur = models.ForeignKey('comptes.Utilisateur', on_delete=models.CASCADE)
    contenu = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True) 

    class Meta:
        ordering = ['date_envoi']

    def __str__(self):
        return f"{self.auteur} â€” {self.date_envoi:%d/%m %H:%M}"
