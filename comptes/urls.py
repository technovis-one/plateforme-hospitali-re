from django.urls import path
from . import views
from . import email_verification_views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', views.connexion, name='accueil'),
    path('inscription/', email_verification_views.inscription, name='inscription'),
    path('confirmer-email/<uidb64>/<token>/', email_verification_views.confirmer_email, name='confirmer_email'),
    path('mot-de-passe-reinitialise/', email_verification_views.password_reset_complete, name='password_reset_complete'),
    path('mot-de-passe-oublie/confirmer/<uidb64>/<token>/', email_verification_views.password_reset_confirm, name='password_reset_confirm'),
    path('mot-de-passe-oublie/envoye/', email_verification_views.password_reset_done, name='password_reset_done'),
    path('mot-de-passe-oublie/', email_verification_views.password_reset, name='password_reset'),
    path('inscription/confirmation/', email_verification_views.inscription_en_attente, name='inscription_en_attente'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('patient/', views.patient, name='patient'),
    path('medecin/', views.medecin, name='medecin'),
    path('medecin/patients/', views.medecin_patients, name='medecin_patients'),
    path('medecin/demandes/', views.medecin_demandes, name='medecin_demandes'),
    path('medecin/consultations/', views.medecin_consultations, name='medecin_consultations'),
    path('admin-espace/', views.admin, name='admin'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)