"""URL configuration for NovaHospito project."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("rendez-vous/", include("rdv.urls")),
    path("dossier-medical/", include("dossier.urls")),
    path("", include("comptes.urls")),
]
