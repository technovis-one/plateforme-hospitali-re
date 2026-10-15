from django.urls import path

from . import views

app_name = "rdv"

urlpatterns = [
    path("", views.rendezvous, name="rendezvous"),
]
