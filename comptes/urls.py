from django.urls import path
from . import views

urlpatterns = [
    path('', views.connexion, name='accueil'),
    path('inscription/', views.inscription, name='inscription'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('patient/', views.patient, name='patient'),
    path('medecin/', views.medecin, name='medecin'),
    path('admin-espace/', views.admin, name='admin'),
]