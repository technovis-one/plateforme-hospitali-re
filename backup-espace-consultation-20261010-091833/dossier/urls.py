from django.urls import path

from . import views

app_name = "dossier"

urlpatterns = [
    path("", views.dossier_patient, name="medical"),
]
