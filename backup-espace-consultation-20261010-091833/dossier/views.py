from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from comptes.models import Patient, Utilisateur
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
