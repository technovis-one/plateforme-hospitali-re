from django.contrib import admin
# dossier/admin.py
from django.contrib import admin
from .models import DossierMedical, Consultation

admin.site.register(DossierMedical)
admin.site.register(Consultation)
# Register your models here.
