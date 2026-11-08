"""Stop scripts from hammering the site: count recent attempts and say no once there are too many.

The counts are kept in the database, so they work no matter which server process answers the request.
"""
from datetime import timedelta

from django.utils import timezone

from .models import RateLimitHit

KEEP_FOR = timedelta(days=1)

# name: (how many, within how long)
LIMITS = {
    "login-fail-account": (5, timedelta(minutes=15)),   # wrong passwords for one account, from anywhere
    "login-fail-ip": (20, timedelta(minutes=15)),       # wrong passwords from one connection, any account
    "report": (10, timedelta(hours=1)),
    "signup": (5, timedelta(hours=1)),
    "contact": (5, timedelta(hours=1)),
    "ai-search": (20, timedelta(hours=1)),
    "map-photo": (20, timedelta(hours=1)),
    "reset-request": (10, timedelta(hours=1)),
}


def client_ip(request):
    """The visitor's address. PythonAnywhere passes the real one in X-Real-IP."""
    if request is None:
        return "unknown"
    return (request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR") or "unknown").strip()[:64]


def _key(name, who):
    return f"{name}:{str(who).lower()}"[:200]


def too_many(name, who):
    """True if this person has already used up their tries for now."""
    limit, window = LIMITS[name]
    since = timezone.now() - window
    return RateLimitHit.objects.filter(key=_key(name, who), created_at__gte=since).count() >= limit


def record(name, who):
    RateLimitHit.objects.create(key=_key(name, who))
    RateLimitHit.objects.filter(created_at__lt=timezone.now() - KEEP_FOR).delete()


def allow(name, who):
    """Check and count in one step. Returns False when they've hit the limit."""
    if too_many(name, who):
        return False
    record(name, who)
    return True


def clear(name, who):
    RateLimitHit.objects.filter(key=_key(name, who)).delete()
