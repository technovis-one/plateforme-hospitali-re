from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import MultipleObjectsReturned


class EmailBackend(ModelBackend):
    """Authentifie par adresse e-mail, en minuscules ou majuscules, les comptes actifs uniquement."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        email = kwargs.get("email") or username
        if not email or not password:
            return None
        try:
            user = UserModel._default_manager.get(email__iexact=email.strip())
        except (UserModel.DoesNotExist, MultipleObjectsReturned):
            UserModel().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
