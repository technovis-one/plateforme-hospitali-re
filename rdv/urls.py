from django.urls import path

from . import views

app_name = "rdv"

urlpatterns = [
    path("<int:rdv_id>/confirmer/", views.confirmer, name="confirmer"),
    path("teleconsultations/", views.teleconsultations, name="teleconsultations"),
    path("teleconsultation/<int:rdv_id>/", views.teleconsultation, name="teleconsultation"),
    path("", views.rendezvous, name="rendezvous"),
]
