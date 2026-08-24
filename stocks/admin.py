from django.contrib import admin
# stocks/admin.py
from django.contrib import admin
from .models import Medicament, Prescription

admin.site.register(Medicament)
admin.site.register(Prescription)
# Register your models here.
