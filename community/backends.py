from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

from .limits import client_ip, too_many


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


def login_key(identifier):
    """One counter per account, whether they typed the email or the old username."""
    accounts = find_accounts(identifier)
    if accounts:
        return f"user-{accounts[0].pk}"
    return (identifier or "").strip().lower() or "blank"


def login_throttled(request, identifier):
    """Too many wrong passwords lately for this account (from anywhere) or from this connection (any account).
    This applies to everyone, admins included, on every login page."""
    return too_many("login-fail-account", login_key(identifier)) or too_many("login-fail-ip", client_ip(request))


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
        if login_throttled(request, username):
            return None
        if "@" in username:
            for user in User.objects.filter(email__iexact=username).order_by("pk"):
                if user.check_password(password) and self.user_can_authenticate(user):
                    return user
        return super().authenticate(request, username=username, password=password, **kwargs)

    def user_can_authenticate(self, user):
        return super().user_can_authenticate(user) and not is_locked(user)
