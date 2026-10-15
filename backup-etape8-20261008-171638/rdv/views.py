from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from comptes.models import Patient, Utilisateur
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
