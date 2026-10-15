from django.urls import path

from . import views

app_name = "dossier"

urlpatterns = [
    path("", views.dossier_patient, name="medical"),
    path("consultation/<int:rdv_id>/", views.consultation_medecin, name="consultation_medecin"),
]
