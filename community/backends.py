from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


def find_accounts(identifier):
    """Accounts matching what someone typed in the login box: an email, or an older account's username."""
    identifier = (identifier or "").strip()
    if not identifier:
        return []
    if "@" in identifier:
        accounts = list(User.objects.filter(email__iexact=identifier).order_by("pk"))
        if accounts:
            return accounts
    return list(User.objects.filter(username__iexact=identifier).order_by("pk")[:1])


def is_locked(user):
    """Accounts lock after too many wrong passwords (site admins are never locked out)."""
    if user.is_superuser:
        return False
    profile = getattr(user, "profile", None)
    return bool(profile and profile.login_locked)


class EmailOrUsernameBackend(ModelBackend):
    """Log in with an email address. Older accounts can still use their username."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        username = (username or kwargs.get(User.USERNAME_FIELD) or "").strip()
        if "@" in username:
            for user in User.objects.filter(email__iexact=username).order_by("pk"):
                if user.check_password(password) and self.user_can_authenticate(user):
                    return user
        return super().authenticate(request, username=username, password=password, **kwargs)

    def user_can_authenticate(self, user):
        return super().user_can_authenticate(user) and not is_locked(user)
