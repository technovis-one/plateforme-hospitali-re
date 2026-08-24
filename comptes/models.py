from django.db import models
# comptes/models.py
from django.contrib.auth.models import AbstractUser

class Utilisateur(AbstractUser):
    """Classe mère — remplace le User par défaut de Django."""

    ROLE_PATIENT = 'patient'
    ROLE_MEDECIN = 'medecin'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_PATIENT, 'Patient'),
        (ROLE_MEDECIN, 'Médecin'),
        (ROLE_ADMIN, 'Administrateur'),
    ]

    email = models.EmailField(unique=True)
    role  = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"

class Patient(Utilisateur):
    """Hérite d'Utilisateur (héritage multi-tables Django)."""
    date_naissance = models.DateField()
    num_tel = models.CharField(max_length=20)
    adresse = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

class Medecin(Utilisateur):
    """Hérite d'Utilisateur (héritage multi-tables Django)."""
    specialite = models.CharField(max_length=100)
    num_rpps = models.CharField(max_length=20, unique=True)
    planning = models.TextField(blank=True)

    class Meta:
        verbose_name = "Médecin"
        verbose_name_plural = "Médecins"

# Create your models here.