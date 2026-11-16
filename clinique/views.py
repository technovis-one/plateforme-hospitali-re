from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from comptes.models import Medecin, Patient, Utilisateur
from dossier.models import Consultation
from facturation.models import Facture
from rdv.models import RendezVous
from stocks.models import Medicament, MouvementStock

from .forms import (
    ArticleStockEditForm,
    ArticleStockForm,
    CliniqueForm,
    DisponibiliteMedecinForm,
    MembreEquipeForm,
    MouvementStockForm,
    SalleForm,
    ServiceForm,
)
from .models import Clinique, DisponibiliteMedecin, MembreEquipe, Salle, Service


def _admin_only(request):
    if not request.user.is_authenticated or request.user.role != Utilisateur.ROLE_ADMIN:
        messages.error(request, "Cette partie est réservée à l’administration de la clinique.")
        return False
    return True


def _profile():
    return Clinique.objects.get_or_create(pk=1, defaults={"nom": "Clinique NovaHospito"})[0]


def _base_context(page_title, active_page):
    return {"page_title": page_title, "active_page": active_page, "clinic_name": _profile().nom}


@login_required
def dashboard(request):
    if not _admin_only(request):
        return redirect("accueil")
    today = timezone.localdate()
    profile = _profile()
    low_stock = Medicament.objects.filter(actif=True, quantite_stock__lte=F("seuil_alerte"))
    expiring = Medicament.objects.filter(
        actif=True,
        date_peremption__isnull=False,
        date_peremption__lte=today + timedelta(days=30),
    )
    expired = Medicament.objects.filter(actif=True, date_peremption__lt=today)
    stock_alerts = Medicament.objects.filter(actif=True).filter(
        Q(quantite_stock__lte=F("seuil_alerte"))
        | Q(date_peremption__isnull=False, date_peremption__lte=today + timedelta(days=30))
    )
    appointments = RendezVous.objects.filter(date=today).exclude(statut=RendezVous.STATUT_ANNULE)
    context = {
        **_base_context("Vue d’ensemble", "overview"),
        "profile": profile,
        "patients_count": Patient.objects.count(),
        "doctors_count": Medecin.objects.filter(is_active=True).count(),
        "team_count": MembreEquipe.objects.filter(actif=True).count(),
        "appointments_today_count": appointments.count(),
        "consultations_today_count": Consultation.objects.filter(rendez_vous__date=today).count(),
        "pending_invoices_count": Facture.objects.filter(statut=Facture.STATUT_ATTENTE).count(),
        "services_count": Service.objects.filter(actif=True).count(),
        "active_rooms_count": Salle.objects.filter(active=True).count(),
        "low_stock_count": low_stock.count(),
        "stock_alert_count": stock_alerts.count(),
        "expiring_count": expiring.count(),
        "expired_count": expired.count(),
        "low_stock_items": low_stock.order_by("quantite_stock", "nom")[:6],
        "expiring_items": expiring.order_by("date_peremption", "nom")[:6],
        "appointments_today": appointments.select_related("patient", "medecin").order_by("heure")[:8],
        "recent_movements": MouvementStock.objects.select_related("article", "cree_par")[:8],
    }
    return render(request, "clinique/dashboard.html", context)


@login_required
def profile(request):
    if not _admin_only(request):
        return redirect("accueil")
    instance = _profile()
    form = CliniqueForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Les coordonnées de la clinique ont été mises à jour.")
        return redirect("clinique:profile")
    return render(request, "clinique/profile.html", {
        **_base_context("Identité et coordonnées", "profile"), "form": form, "profile": instance,
    })


@login_required
def services(request):
    if not _admin_only(request):
        return redirect("accueil")
    form = ServiceForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Le service ou la spécialité a été ajouté.")
        return redirect("clinique:services")
    return render(request, "clinique/services.html", {
        **_base_context("Services et spécialités", "services"),
        "form": form,
        "services": Service.objects.all().prefetch_related("salles", "membres_equipe"),
    })


@login_required
@require_POST
def service_toggle(request, service_id):
    if not _admin_only(request):
        return redirect("accueil")
    service = get_object_or_404(Service, pk=service_id)
    service.actif = not service.actif
    service.save(update_fields=("actif",))
    messages.success(request, f"Le service « {service.nom} » a été mis à jour.")
    return redirect("clinique:services")


@login_required
def service_edit(request, service_id):
    if not _admin_only(request):
        return redirect("accueil")
    service = get_object_or_404(Service, pk=service_id)
    form = ServiceForm(request.POST or None, instance=service)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Le service a été mis à jour.")
        return redirect("clinique:services")
    return render(request, "clinique/edit_form.html", {
        **_base_context("Modifier un service", "services"),
        "form": form, "object_title": service.nom, "return_url": "clinique:services",
    })


@login_required
def staffing(request):
    if not _admin_only(request):
        return redirect("accueil")
    schedule_form = DisponibiliteMedecinForm(request.POST or None, prefix="horaire")
    member_form = MembreEquipeForm(request.POST or None, prefix="equipe")
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "horaire" and schedule_form.is_valid():
            schedule_form.save()
            messages.success(request, "L’horaire du médecin a été enregistré.")
            return redirect("clinique:staffing")
        if action == "equipe" and member_form.is_valid():
            member_form.save()
            messages.success(request, "Le membre de l’équipe a été ajouté.")
            return redirect("clinique:staffing")
    return render(request, "clinique/staffing.html", {
        **_base_context("Équipe, médecins et horaires", "staffing"),
        "schedule_form": schedule_form,
        "member_form": member_form,
        "doctors": Medecin.objects.filter(is_active=True).order_by("last_name", "first_name"),
        "schedules": DisponibiliteMedecin.objects.filter(actif=True).select_related("medecin", "service", "salle"),
        "members": MembreEquipe.objects.filter(actif=True).select_related("service"),
        "services": Service.objects.filter(actif=True),
    })


@login_required
def schedule_edit(request, schedule_id):
    if not _admin_only(request):
        return redirect("accueil")
    schedule = get_object_or_404(DisponibiliteMedecin, pk=schedule_id)
    form = DisponibiliteMedecinForm(request.POST or None, instance=schedule)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "L’horaire médecin a été mis à jour.")
        return redirect("clinique:staffing")
    return render(request, "clinique/edit_form.html", {
        **_base_context("Modifier un horaire", "staffing"),
        "form": form, "object_title": str(schedule), "return_url": "clinique:staffing",
    })


@login_required
def team_member_edit(request, member_id):
    if not _admin_only(request):
        return redirect("accueil")
    member = get_object_or_404(MembreEquipe, pk=member_id)
    form = MembreEquipeForm(request.POST or None, instance=member)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "La fiche du membre d’équipe a été mise à jour.")
        return redirect("clinique:staffing")
    return render(request, "clinique/edit_form.html", {
        **_base_context("Modifier un membre d’équipe", "staffing"),
        "form": form, "object_title": member.nom, "return_url": "clinique:staffing",
    })


@login_required
def rooms(request):
    if not _admin_only(request):
        return redirect("accueil")
    form = SalleForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "La salle a été enregistrée.")
        return redirect("clinique:rooms")
    return render(request, "clinique/rooms.html", {
        **_base_context("Salles", "rooms"), "form": form,
        "rooms": Salle.objects.select_related("service").all(),
    })


@login_required
@require_POST
def room_toggle(request, room_id):
    if not _admin_only(request):
        return redirect("accueil")
    room = get_object_or_404(Salle, pk=room_id)
    room.active = not room.active
    room.save(update_fields=("active",))
    messages.success(request, f"L’état de la salle {room.code} a été mis à jour.")
    return redirect("clinique:rooms")


@login_required
def room_edit(request, room_id):
    if not _admin_only(request):
        return redirect("accueil")
    room = get_object_or_404(Salle, pk=room_id)
    form = SalleForm(request.POST or None, instance=room)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "La salle a été mise à jour.")
        return redirect("clinique:rooms")
    return render(request, "clinique/edit_form.html", {
        **_base_context("Modifier une salle", "rooms"),
        "form": form, "object_title": room.code, "return_url": "clinique:rooms",
    })


@login_required
def stock(request):
    if not _admin_only(request):
        return redirect("accueil")
    article_form = ArticleStockForm(prefix="article")
    movement_form = MouvementStockForm(prefix="mouvement")
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "article":
            article_form = ArticleStockForm(request.POST, prefix="article")
            if article_form.is_valid():
                with transaction.atomic():
                    initial_quantity = article_form.cleaned_data["stock_initial"]
                    item = article_form.save(commit=False)
                    item.quantite_stock = initial_quantity
                    item.save()
                    if initial_quantity:
                        MouvementStock.objects.create(
                            article=item,
                            type_mouvement=MouvementStock.ENTREE,
                            quantite=initial_quantity,
                            motif="Stock initial",
                            cree_par=request.user,
                        )
                messages.success(request, "L’article a été ajouté au stock.")
                return redirect("clinique:stock")
        elif action == "mouvement":
            movement_form = MouvementStockForm(request.POST, prefix="mouvement")
            if movement_form.is_valid():
                data = movement_form.cleaned_data
                with transaction.atomic():
                    item = Medicament.objects.select_for_update().get(pk=data["article"].pk)
                    quantity = data["quantite"]
                    if data["type_mouvement"] == MouvementStock.SORTIE and item.quantite_stock < quantity:
                        movement_form.add_error("quantite", "La sortie dépasse la quantité actuellement en stock.")
                    else:
                        if data["type_mouvement"] == MouvementStock.ENTREE:
                            item.quantite_stock = F("quantite_stock") + quantity
                        else:
                            item.quantite_stock = F("quantite_stock") - quantity
                        item.save(update_fields=("quantite_stock", "modifie_le"))
                        item.refresh_from_db(fields=("quantite_stock",))
                        MouvementStock.objects.create(
                            article=item,
                            type_mouvement=data["type_mouvement"],
                            quantite=quantity,
                            motif=data["motif"],
                            cree_par=request.user,
                        )
                        messages.success(request, "Le mouvement de stock a été enregistré.")
                        return redirect("clinique:stock")
    today = timezone.localdate()
    items = Medicament.objects.all().order_by("nom")
    return render(request, "clinique/stock.html", {
        **_base_context("Gestion des stocks", "stock"),
        "article_form": article_form,
        "movement_form": movement_form,
        "items": items,
        "items_count": items.count(),
        "low_stock_count": items.filter(actif=True, quantite_stock__lte=F("seuil_alerte")).count(),
        "expired_count": items.filter(actif=True, date_peremption__lt=today).count(),
        "movements": MouvementStock.objects.select_related("article", "cree_par")[:50],
    })


@login_required
def stock_article_edit(request, article_id):
    if not _admin_only(request):
        return redirect("accueil")
    article = get_object_or_404(Medicament, pk=article_id)
    form = ArticleStockEditForm(request.POST or None, instance=article)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Les informations de l’article ont été mises à jour. La quantité reste traçable via les mouvements.")
        return redirect("clinique:stock")
    return render(request, "clinique/stock_article_edit.html", {
        **_base_context("Modifier un article", "stock"), "form": form, "article": article,
    })
