from django.urls import path

from . import views

app_name = "facturation"

urlpatterns = [
    path("nouvelle/", views.creer, name="creer"),
    path("", views.historique, name="historique"),
]
