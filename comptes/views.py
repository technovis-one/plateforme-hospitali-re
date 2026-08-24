
# comptes/views.py
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ConnexionForm, InscriptionPatientForm
from .models import Utilisateur


def connexion(request):
    if request.method == 'POST':
        form = ConnexionForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['email'],  # le backend cherche par email
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
        form = InscriptionPatientForm(request.POST)
        if form.is_valid():
            patient = form.save()
            login(request, patient)
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
    return render(request, 'comptes/patient.html')


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

