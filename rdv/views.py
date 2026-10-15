from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from comptes.models import Patient, Utilisateur
from .daily import DailyServiceError, create_meeting_access, daily_is_configured
from .forms import RendezVousForm
from .models import RendezVous


@login_required
def rendezvous(request):
    if request.user.role != Utilisateur.ROLE_PATIENT:
        messages.error(request, "La prise de rendez-vous est réservée aux patients.")
        return redirect("accueil")

    patient = Patient.objects.filter(pk=request.user.pk).first()
    if patient is None:
        return render(
            request,
            "rdv/rendez-vous.html",
            {"profile_missing": True},
        )

    if request.method == "POST":
        form = RendezVousForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.patient = patient
            booking.statut = RendezVous.STATUT_ATTENTE
            booking.save()
            messages.success(
                request,
                "Votre demande de rendez-vous a été enregistrée. Elle est en attente de confirmation.",
            )
            return redirect("rdv:rendezvous")
    else:
        form = RendezVousForm()

    today = timezone.localdate()
    appointments = (
        RendezVous.objects.filter(patient=patient)
        .select_related("medecin")
        .order_by("-date", "-heure")
    )
    context = {
        "form": form,
        "profile_missing": False,
        "upcoming_appointments": appointments.filter(date__gte=today).order_by(
            "date", "heure"
        ),
        "past_appointments": appointments.filter(date__lt=today),
    }
    return render(request, "rdv/rendez-vous.html", context)


@never_cache
@login_required
def teleconsultations(request):
    role = request.user.role
    today = timezone.localdate()
    if role == Utilisateur.ROLE_PATIENT:
        patient = Patient.objects.filter(pk=request.user.pk).first()
        if patient is None:
            return render(request, "rdv/teleconsultations.html", {
                "profile_missing": True,
                "is_doctor": False,
                "upcoming_teleconsultations": [],
                "past_teleconsultations": [],
            })
        consultations = RendezVous.objects.filter(
            patient=patient,
            type=RendezVous.TYPE_TELECONSULTATION,
        ).select_related("patient", "medecin")
        is_doctor = False
    elif role == Utilisateur.ROLE_MEDECIN:
        consultations = RendezVous.objects.filter(
            medecin_id=request.user.pk,
            type=RendezVous.TYPE_TELECONSULTATION,
        ).select_related("patient", "medecin")
        is_doctor = True
    else:
        raise Http404

    context = {
        "profile_missing": False,
        "is_doctor": is_doctor,
        "upcoming_teleconsultations": consultations.filter(date__gte=today).order_by(
            "date", "heure"
        )[:50],
        "past_teleconsultations": consultations.filter(date__lt=today).order_by(
            "-date", "-heure"
        )[:20],
    }
    return render(request, "rdv/teleconsultations.html", context)


@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def teleconsultation(request, rdv_id):
    role = request.user.role
    if role not in {Utilisateur.ROLE_PATIENT, Utilisateur.ROLE_MEDECIN}:
        raise Http404

    appointment = (
        RendezVous.objects.select_related("patient", "medecin")
        .filter(pk=rdv_id)
        .first()
    )
    if appointment is None or appointment.type != RendezVous.TYPE_TELECONSULTATION:
        raise Http404

    is_doctor = role == Utilisateur.ROLE_MEDECIN
    if is_doctor and appointment.medecin_id != request.user.pk:
        raise Http404
    if not is_doctor and appointment.patient_id != request.user.pk:
        raise Http404

    local_start = datetime.combine(appointment.date, appointment.heure)
    start = timezone.make_aware(local_start, timezone.get_current_timezone())
    now = timezone.now()
    if timezone.is_naive(now):
        now = timezone.make_aware(now, timezone.get_current_timezone())
    now = timezone.localtime(now)
    start = timezone.localtime(start)
    starts_at = start - timedelta(minutes=15)
    ends_at = start + timedelta(minutes=60)
    in_call_window = starts_at <= now <= ends_at
    can_join = appointment.statut == RendezVous.STATUT_CONFIRME and in_call_window
    daily_configured = daily_is_configured()
    meeting_config = None
    error = None

    if request.method == "POST":
        if not can_join:
            error = "Le rendez-vous doit être confirmé et se trouver dans la plage horaire prévue."
        elif not daily_configured:
            error = "Le service Daily n’est pas configuré sur le serveur."
        else:
            try:
                room_url, token = create_meeting_access(
                    appointment=appointment,
                    role=role,
                    starts_at=starts_at,
                    ends_at=ends_at,
                )
                meeting_config = {"url": room_url, "token": token}
            except DailyServiceError as exc:
                error = str(exc)

    return render(
        request,
        "rdv/teleconsultation.html",
        {
            "appointment": appointment,
            "is_doctor": is_doctor,
            "in_call_window": in_call_window,
            "daily_configured": daily_configured,
            "can_join": can_join and daily_configured,
            "meeting_config": meeting_config,
            "error": error,
        },
    )


@login_required
@require_POST
def confirmer(request, rdv_id):
    if request.user.role != Utilisateur.ROLE_MEDECIN:
        raise Http404
    appointment = RendezVous.objects.filter(
        pk=rdv_id,
        medecin_id=request.user.pk,
        statut=RendezVous.STATUT_ATTENTE,
    ).first()
    if appointment is None:
        messages.error(request, "Ce rendez-vous est introuvable, déjà traité ou ne vous est pas attribué.")
        return redirect("medecin")
    if appointment.date < timezone.localdate():
        messages.error(request, "Un rendez-vous passé ne peut pas être confirmé.")
        return redirect("medecin")
    scheduled_at = timezone.make_aware(
        datetime.combine(appointment.date, appointment.heure),
        timezone.get_current_timezone(),
    )
    if timezone.now() > scheduled_at:
        messages.error(request, "L’heure de début est passée. Ce rendez-vous ne peut plus être confirmé pour lancer une salle.")
        return redirect("medecin")

    updated = RendezVous.objects.filter(
        pk=appointment.pk,
        medecin_id=request.user.pk,
        statut=RendezVous.STATUT_ATTENTE,
    ).update(statut=RendezVous.STATUT_CONFIRME)
    if updated:
        messages.success(request, "Le rendez-vous a été confirmé.")
    else:
        messages.error(request, "Le rendez-vous a déjà été traité. Actualise ton planning.")
    return redirect("medecin")
