from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .forms import ConnexionForm, InscriptionPatientForm
from .models import Utilisateur, Patient
from rdv.models import RendezVous
from dossier.models import DossierMedical, Consultation
from facturation.models import Facture

def connexion(request):
    if request.method == 'POST':
        form = ConnexionForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['email'],  
                password=form.cleaned_data['password']
            )
            if user is not None:
                login(request, user)
                return redirige_selon_role(user)
            else:
                messages.error(request, "Email ou mot de passe incorrect.")
    else:
        form = ConnexionForm()
    return render(request, 'comptes/accueil.html', {'form': form})


def redirige_selon_role(user):
    if user.role == Utilisateur.ROLE_PATIENT:
        return redirect('patient')
    elif user.role == Utilisateur.ROLE_MEDECIN:
        return redirect('medecin')
    elif user.role == Utilisateur.ROLE_ADMIN:
        return redirect('admin')
    return redirect('accueil')


def inscription(request):
    if request.method == 'POST':
        form = InscriptionPatientForm(request.POST, request.FILES)
        if form.is_valid():
            patient = form.save()
            login(request, patient, backend='comptes.backends.EmailBackend')
            return redirect('patient')
    else:
        form = InscriptionPatientForm()
    return render(request, 'comptes/inscription.html', {'form': form})


def deconnexion(request):
    logout(request)
    return redirect('accueil')


@login_required
def patient(request):
    if request.user.role != Utilisateur.ROLE_PATIENT:
        messages.error(request, "Accès réservé aux patients.")
        return redirect('accueil')

    patient_obj = Patient.objects.get(pk=request.user.pk)

    rendezvous_list = RendezVous.objects.filter(patient=patient_obj).order_by('-date', '-heure')
    prochain_rdv = RendezVous.objects.filter(
        patient=patient_obj, date__gte=timezone.now().date()
    ).order_by('date', 'heure').first()
    dossier = DossierMedical.objects.filter(patient=patient_obj).first()
    consultations_count = Consultation.objects.filter(rendez_vous__patient=patient_obj).count()
    facture_attente = Facture.objects.filter(
        patient=patient_obj, statut=Facture.STATUT_ATTENTE
    ).order_by('-date').first()

    context = {
        'rendezvous_list': rendezvous_list,
        'prochain_rdv': prochain_rdv,
        'dossier': dossier,
        'consultations_count': consultations_count,
        'facture_attente': facture_attente,
    }
    return render(request, 'comptes/patient.html', context)


@login_required
def medecin(request):
    if request.user.role != Utilisateur.ROLE_MEDECIN:
        messages.error(request, "Accès réservé aux médecins.")
        return redirect('accueil')
    return render(request, 'comptes/medecin.html')


@login_required
def admin(request):
    if request.user.role != Utilisateur.ROLE_ADMIN:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('accueil')
    return render(request, 'comptes/admin.html')

