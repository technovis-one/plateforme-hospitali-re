from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.contrib import messages
from django.shortcuts import redirect, render

from comptes.models import Patient, Utilisateur
from .forms import FactureCreateForm
from .models import Facture


@login_required
def historique(request):
    user = request.user
    if user.role == Utilisateur.ROLE_PATIENT:
        patient = Patient.objects.filter(pk=user.pk).first()
        if patient is None:
            return render(request, "facturation/historique.html", {
                "profile_missing": True,
                "factures_page": None,
                "is_admin": False,
                "retour_url": "patient",
            })
        factures = Facture.objects.filter(patient=patient).select_related(
            "patient", "consultation__rendez_vous__medecin"
        ).order_by("-date", "-pk")
        is_admin = False
        retour_url = "patient"
    elif user.role == Utilisateur.ROLE_ADMIN:
        factures = Facture.objects.select_related(
            "patient", "consultation__rendez_vous__medecin"
        ).order_by("-date", "-pk")
        is_admin = True
        retour_url = "admin"
    else:
        return redirect("accueil")

    page = Paginator(factures, 20).get_page(request.GET.get("page"))
    context = {
        "profile_missing": False,
        "factures_page": page,
        "is_admin": is_admin,
        "retour_url": retour_url,
        "total_factures": factures.count(),
        "attente_count": factures.filter(statut=Facture.STATUT_ATTENTE).count(),
        "payee_count": factures.filter(statut=Facture.STATUT_PAYEE).count(),
        "annulee_count": factures.filter(statut=Facture.STATUT_ANNULEE).count(),
        "total_montant": factures.exclude(
            statut=Facture.STATUT_ANNULEE
        ).aggregate(total=Sum("montant"))["total"],
    }
    return render(request, "facturation/historique.html", context)


@login_required
def creer(request):
    if request.user.role != Utilisateur.ROLE_ADMIN:
        return redirect("accueil")

    form = FactureCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                facture = form.save(commit=False)
                facture.statut = Facture.STATUT_ATTENTE
                facture.save()
        except IntegrityError:
            form.add_error(
                "consultation",
                "Une facture existe déjà pour cette consultation. Actualise la page avant de réessayer.",
            )
        else:
            messages.success(request, f"La facture #{facture.pk} a été créée avec le statut « En attente ». Aucun paiement n’a été effectué.")
            return redirect("facturation:historique")

    return render(request, "facturation/creer.html", {"form": form})
