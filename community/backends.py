from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class EmailOrUsernameBackend(ModelBackend):
    """Log in with an email address. Older accounts can still use their username."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        username = (username or kwargs.get(User.USERNAME_FIELD) or "").strip()
        if "@" in username:
            for user in User.objects.filter(email__iexact=username).order_by("pk"):
                if user.check_password(password) and self.user_can_authenticate(user):
                    return user
        return super().authenticate(request, username=username, password=password, **kwargs)
