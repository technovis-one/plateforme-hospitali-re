from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from comptes.models import Patient, Utilisateur
from rdv.models import RendezVous

from .forms import ConsultationForm
from .models import Consultation, DossierMedical


@login_required
def dossier_patient(request):
    if request.user.role != Utilisateur.ROLE_PATIENT:
        messages.error(request, "Le dossier médical est réservé aux patients.")
        return redirect("accueil")

    patient = Patient.objects.filter(pk=request.user.pk).first()
    if patient is None:
        return render(
            request,
            "dossier/dossier-patient.html",
            {"profile_missing": True, "record_missing": False, "consultations": []},
        )

    dossier = DossierMedical.objects.filter(patient=patient).first()
    consultations = (
        Consultation.objects.filter(rendez_vous__patient=patient)
        .select_related("rendez_vous__medecin", "rendez_vous")
        .prefetch_related("medicaments")
        .order_by("-date", "-rendez_vous__date", "-rendez_vous__heure")
    )

    return render(
        request,
        "dossier/dossier-patient.html",
        {
            "profile_missing": False,
            "record_missing": dossier is None,
            "dossier": dossier,
            "consultations": consultations,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def consultation_medecin(request, rdv_id):
    if request.user.role != Utilisateur.ROLE_MEDECIN:
        raise Http404

    appointment = get_object_or_404(
        RendezVous.objects.select_related("patient", "medecin"),
        pk=rdv_id,
        medecin_id=request.user.pk,
        statut__in=(RendezVous.STATUT_CONFIRME, RendezVous.STATUT_TERMINE),
    )
    scheduled_at = timezone.make_aware(
        datetime.combine(appointment.date, appointment.heure),
        timezone.get_current_timezone(),
    )
    current_time = timezone.now()
    if timezone.is_naive(current_time):
        current_time = timezone.make_aware(current_time, timezone.get_current_timezone())
    record = Consultation.objects.filter(rendez_vous=appointment).first()
    can_edit = (
        appointment.statut == RendezVous.STATUT_TERMINE
        or current_time >= scheduled_at
    )
    dossier = DossierMedical.objects.filter(patient=appointment.patient).first()

    if request.method == "POST":
        if not can_edit:
            messages.error(request, "Le compte-rendu pourra être saisi à partir de l’heure prévue du rendez-vous.")
            return redirect("dossier:consultation_medecin", rdv_id=appointment.pk)

        with transaction.atomic():
            locked_appointment = get_object_or_404(
                RendezVous.objects.select_for_update().select_related("patient", "medecin"),
                pk=rdv_id,
                medecin_id=request.user.pk,
                statut__in=(RendezVous.STATUT_CONFIRME, RendezVous.STATUT_TERMINE),
            )
            record = Consultation.objects.select_for_update().filter(
                rendez_vous=locked_appointment
            ).first()
            form = ConsultationForm(request.POST, instance=record)
            if form.is_valid():
                record = form.save(commit=False)
                record.rendez_vous = locked_appointment
                record.save()
                messages.success(request, "Le compte-rendu de consultation a été enregistré.")
                return redirect("dossier:consultation_medecin", rdv_id=appointment.pk)
    else:
        form = ConsultationForm(instance=record)

    return render(
        request,
        "dossier/consultation-medecin.html",
        {
            "appointment": appointment,
            "dossier": dossier,
            "consultation": record,
            "form": form,
            "can_edit": can_edit,
        },
    )
