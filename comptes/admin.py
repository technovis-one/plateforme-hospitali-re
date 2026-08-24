from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, Patient, Medecin

admin.site.register(Utilisateur, UserAdmin)
admin.site.register(Patient)
admin.site.register(Medecin)
