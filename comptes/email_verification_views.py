import binascii
import logging

from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.http import require_http_methods

from .forms import InscriptionPatientForm
from .models import Patient, Utilisateur

logger = logging.getLogger(__name__)


def _send_patient_verification(request, patient):
    uid = urlsafe_base64_encode(force_bytes(patient.pk))
    token = default_token_generator.make_token(patient)
    confirmation_url = request.build_absolute_uri(
        reverse("confirmer_email", kwargs={"uidb64": uid, "token": token})
    )
    sent = send_mail(
        "Confirmez votre adresse e-mail — NovaHospito",
        "Pour activer votre compte patient NovaHospito, ouvrez ce lien :\n\n"
        f"{confirmation_url}\n\nCe lien expire selon le délai de sécurité configuré (3 jours par défaut).",
        None,
        [patient.email],
        fail_silently=False,
    )
    if sent != 1:
        raise RuntimeError("Le courriel de confirmation n'a pas été accepté par le backend.")


def inscription(request):
    if request.method == "POST":
        form = InscriptionPatientForm(request.POST, request.FILES)
        if form.is_valid():
            patient = form.save(commit=False)
            # Le formulaire impose le rôle patient et aucun privilège du personnel.
            patient.role = Utilisateur.ROLE_PATIENT
            patient.is_active = False
            patient.is_staff = False
            patient.is_superuser = False
            patient.save()
            try:
                _send_patient_verification(request, patient)
            except Exception:
                if patient.photo:
                    patient.photo.delete(save=False)
                patient.delete()
                messages.error(
                    request,
                    "L’e-mail de confirmation n’a pas pu être envoyé. Vérifiez la configuration de messagerie, puis réessayez.",
                )
                return render(request, "comptes/inscription.html", {"form": form}, status=503)
            messages.success(
                request,
                "Votre demande de compte est enregistrée. Ouvrez le lien envoyé à votre adresse e-mail pour l’activer.",
            )
            return redirect("inscription_en_attente")
    else:
        form = InscriptionPatientForm()
    return render(request, "comptes/inscription.html", {"form": form})


def inscription_en_attente(request):
    return render(request, "comptes/inscription-en-attente.html")


class SafePasswordResetView(PasswordResetView):
    template_name = "comptes/mot-de-passe-oublie.html"
    email_template_name = "comptes/password_reset_email.html"
    subject_template_name = "comptes/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except Exception:
            # Keep the response generic to avoid revealing whether an account exists.
            logger.exception("Password reset email delivery failed.")
            messages.error(
                self.request,
                "Le service d’envoi du courriel est indisponible. Vérifiez la messagerie configurée ou réessayez plus tard.",
            )
            return redirect("password_reset")


def password_reset(request):
    return SafePasswordResetView.as_view()(request)


def password_reset_done(request):
    return PasswordResetDoneView.as_view(
        template_name="comptes/mot-de-passe-envoye.html"
    )(request)


def password_reset_confirm(request, uidb64, token):
    return PasswordResetConfirmView.as_view(
        template_name="comptes/nouveau-mot-de-passe.html"
    )(request, uidb64=uidb64, token=token)


def password_reset_complete(request):
    return PasswordResetCompleteView.as_view(
        template_name="comptes/mot-de-passe-reinitialise.html"
    )(request)


@require_http_methods(["GET", "POST"])
def confirmer_email(request, uidb64, token):
    patient = None
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        candidate = Utilisateur.objects.get(pk=uid)
        if (
            candidate.role == Utilisateur.ROLE_PATIENT
            and Patient.objects.filter(pk=candidate.pk).exists()
        ):
            patient = candidate
    except (TypeError, ValueError, OverflowError, binascii.Error, Utilisateur.DoesNotExist):
        patient = None

    if patient is None:
        state = "invalid"
    elif patient.is_active:
        state = "already"
    elif not default_token_generator.check_token(patient, token):
        state = "invalid"
    elif request.method == "POST":
        patient.is_active = True
        patient.save(update_fields=("is_active",))
        messages.success(request, "Adresse confirmée. Vous pouvez maintenant vous connecter.")
        return redirect("accueil")
    else:
        state = "confirm"

    return render(request, "comptes/confirmer-email.html", {"state": state})
