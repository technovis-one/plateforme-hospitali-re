from django.contrib import admin

from .models import Clinique, DisponibiliteMedecin, MembreEquipe, Salle, Service


@admin.register(Clinique)
class CliniqueAdmin(admin.ModelAdmin):
    list_display = ("nom", "telephone", "email", "ville", "modifie_le")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("nom", "specialite", "actif")
    list_filter = ("actif",)
    search_fields = ("nom", "specialite")


@admin.register(Salle)
class SalleAdmin(admin.ModelAdmin):
    list_display = ("code", "nom", "service", "capacite", "active")
    list_filter = ("active", "service")
    search_fields = ("code", "nom", "equipements")


@admin.register(DisponibiliteMedecin)
class DisponibiliteMedecinAdmin(admin.ModelAdmin):
    list_display = ("medecin", "jour", "heure_debut", "heure_fin", "service", "salle", "actif")
    list_filter = ("jour", "actif", "service")
    search_fields = ("medecin__first_name", "medecin__last_name", "medecin__email")


@admin.register(MembreEquipe)
class MembreEquipeAdmin(admin.ModelAdmin):
    list_display = ("nom", "fonction", "service", "telephone", "actif")
    list_filter = ("actif", "service")
    search_fields = ("nom", "fonction", "email", "telephone")
