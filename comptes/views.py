from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
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

    patient_obj = Patient.objects.filter(pk=request.user.pk).first()
    if patient_obj is None:
        messages.error(request, "La fiche patient de ce compte n’est pas encore disponible.")
        return redirect('accueil')

    rendezvous_list = RendezVous.objects.filter(patient=patient_obj).order_by('-date', '-heure')
    prochain_rdv = RendezVous.objects.filter(
        patient=patient_obj, date__gte=timezone.localdate()
    ).order_by('date', 'heure').first()
    next_teleconsultation = RendezVous.objects.filter(
        patient=patient_obj,
        type=RendezVous.TYPE_TELECONSULTATION,
        statut=RendezVous.STATUT_CONFIRME,
        date__gte=timezone.localdate(),
    ).order_by('date', 'heure').first()
    dossier = DossierMedical.objects.filter(patient=patient_obj).first()
    consultations_count = Consultation.objects.filter(rendez_vous__patient=patient_obj).count()
    facture_attente = Facture.objects.filter(
        patient=patient_obj, statut=Facture.STATUT_ATTENTE
    ).order_by('-date').first()
    factures_count = Facture.objects.filter(patient=patient_obj).count()

    context = {
        'rendezvous_list': rendezvous_list,
        'prochain_rdv': prochain_rdv,
        'dossier': dossier,
        'consultations_count': consultations_count,
        'facture_attente': facture_attente,
        'factures_count': factures_count,
        'next_teleconsultation': next_teleconsultation,
    }
    return render(request, 'comptes/patient.html', context)


def _doctor_access(request):
    if request.user.role != Utilisateur.ROLE_MEDECIN:
        messages.error(request, "Accès réservé aux médecins.")
        return False
    return True


def _doctor_patients(user, today):
    doctor_records = RendezVous.objects.filter(medecin_id=user.pk).exclude(
        statut=RendezVous.STATUT_ANNULE
    )
    patient_ids = doctor_records.order_by().values("patient_id")
    visit_history = (
        RendezVous.objects.filter(medecin_id=user.pk, date__lte=today)
        .exclude(statut=RendezVous.STATUT_ANNULE)
        .order_by("-date", "-heure")
    )
    patients = (
        Patient.objects.filter(pk__in=patient_ids)
        .order_by("last_name", "first_name")
        .prefetch_related(Prefetch("rendezvous", queryset=visit_history, to_attr="doctor_visits"))
    )
    return patients, patients.count()


@login_required
def medecin(request):
    """Espace planning : rendez-vous du jour et indicateurs médecin."""
    if not _doctor_access(request):
        return redirect("accueil")
    today = timezone.localdate()
    today_records = RendezVous.objects.filter(medecin_id=request.user.pk, date=today)
    appointments = (
        today_records.exclude(statut=RendezVous.STATUT_ANNULE)
        .select_related("patient")
        .order_by("heure")
    )
    return render(request, "comptes/medecin.html", {
        "active_page": "planning",
        "page_title": "Mon planning",
        "today": today,
        "today_appointments": appointments,
        "today_appointment_count": appointments.count(),
        "today_patient_count": appointments.order_by().values("patient_id").distinct().count(),
        "today_teleconsultation_count": appointments.filter(type=RendezVous.TYPE_TELECONSULTATION).count(),
        "pending_appointments_count": RendezVous.objects.filter(
            medecin_id=request.user.pk,
            date__gte=today,
            statut=RendezVous.STATUT_ATTENTE,
        ).count(),
    })


@login_required
def medecin_patients(request):
    """Patients ayant des rendez-vous non annulés attribués au médecin connecté."""
    if not _doctor_access(request):
        return redirect("accueil")
    today = timezone.localdate()
    patients, patient_count = _doctor_patients(request.user, today)
    return render(request, "comptes/medecin/patients.html", {
        "active_page": "patients",
        "page_title": "Mes patients",
        "doctor_patients": patients,
        "doctor_patients_count": patient_count,
        "today": today,
    })


@login_required
def medecin_demandes(request):
    """Demandes futures/en cours qui attendent la confirmation du médecin."""
    if not _doctor_access(request):
        return redirect("accueil")
    today = timezone.localdate()
    pending = (
        RendezVous.objects.filter(
            medecin_id=request.user.pk,
            date__gte=today,
            statut=RendezVous.STATUT_ATTENTE,
        )
        .select_related("patient")
        .order_by("date", "heure")
    )
    return render(request, "comptes/medecin/demandes.html", {
        "active_page": "demandes",
        "page_title": "Demandes à confirmer",
        "pending_appointments": pending,
        "pending_appointments_count": pending.count(),
        "today": today,
    })


@login_required
def medecin_consultations(request):
    """Rendez-vous confirmés/terminés et comptes-rendus associés au médecin."""
    if not _doctor_access(request):
        return redirect("accueil")
    today = timezone.localdate()
    appointment_queryset = (
        RendezVous.objects.filter(
            medecin_id=request.user.pk,
            statut__in=(RendezVous.STATUT_CONFIRME, RendezVous.STATUT_TERMINE),
        )
        .select_related("patient")
        .order_by("-date", "-heure")
    )
    appointments_count = appointment_queryset.count()
    appointments = appointment_queryset[:100]
    record_queryset = (
        Consultation.objects.filter(rendez_vous__medecin_id=request.user.pk)
        .select_related("rendez_vous", "rendez_vous__patient")
        .order_by("-date", "-pk")
    )
    records_count = record_queryset.count()
    records = record_queryset[:50]
    return render(request, "comptes/medecin/consultations.html", {
        "active_page": "consultation",
        "page_title": "Consultations",
        "consultation_appointments": appointments,
        "consultation_appointments_count": appointments_count,
        "recent_consultations": records,
        "consultations_count": records_count,
        "today": today,
    })


@login_required
def admin(request):
    if request.user.role != Utilisateur.ROLE_ADMIN:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('accueil')
    return redirect('clinique:dashboard')
