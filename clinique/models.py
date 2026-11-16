from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Clinique(models.Model):
    """Profil d’établissement. Le tableau de bord utilise la ligne singleton pk=1."""
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    nom = models.CharField(max_length=180, default="Clinique NovaHospito")
    telephone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    ville = models.CharField(max_length=120, blank=True)
    pays = models.CharField(max_length=120, blank=True)
    site_web = models.URLField(blank=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Clinique"
        verbose_name_plural = "Clinique"

    def __str__(self):
        return self.nom


class Service(models.Model):
    nom = models.CharField(max_length=120, unique=True)
    specialite = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("nom",)
        verbose_name = "Service clinique"
        verbose_name_plural = "Services cliniques"

    def __str__(self):
        return self.nom


class Salle(models.Model):
    nom = models.CharField(max_length=120)
    code = models.CharField(max_length=32, unique=True)
    service = models.ForeignKey(Service, null=True, blank=True, on_delete=models.SET_NULL, related_name="salles")
    capacite = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    equipements = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ("code",)
        verbose_name = "Salle"
        verbose_name_plural = "Salles"

    def __str__(self):
        return f"{self.code} — {self.nom}"


class DisponibiliteMedecin(models.Model):
    JOURS = (
        (0, "Lundi"), (1, "Mardi"), (2, "Mercredi"), (3, "Jeudi"),
        (4, "Vendredi"), (5, "Samedi"), (6, "Dimanche"),
    )
    medecin = models.ForeignKey("comptes.Medecin", on_delete=models.CASCADE, related_name="disponibilites_clinique")
    service = models.ForeignKey(Service, null=True, blank=True, on_delete=models.SET_NULL, related_name="disponibilites")
    salle = models.ForeignKey(Salle, null=True, blank=True, on_delete=models.SET_NULL, related_name="disponibilites")
    jour = models.PositiveSmallIntegerField(choices=JOURS)
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ("jour", "heure_debut", "medecin__last_name")
        verbose_name = "Horaire médecin"
        verbose_name_plural = "Horaires médecins"

    def clean(self):
        if self.heure_debut and self.heure_fin and self.heure_fin <= self.heure_debut:
            raise ValidationError({"heure_fin": "L’heure de fin doit être après l’heure de début."})

    def __str__(self):
        return f"{self.medecin} — {self.get_jour_display()} {self.heure_debut:%H:%M}-{self.heure_fin:%H:%M}"


class MembreEquipe(models.Model):
    nom = models.CharField(max_length=120)
    fonction = models.CharField(max_length=120)
    telephone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    service = models.ForeignKey(Service, null=True, blank=True, on_delete=models.SET_NULL, related_name="membres_equipe")
    actif = models.BooleanField(default=True)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("nom",)
        verbose_name = "Membre de l’équipe"
        verbose_name_plural = "Membres de l’équipe"

    def __str__(self):
        return f"{self.nom} — {self.fonction}"
