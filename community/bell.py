"""The notification bell: what goes in it, and who gets it."""
from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from .models import Notification


def short(text, length=60):
    text = " ".join((text or "").split())
    return text if len(text) <= length else text[: length - 1].rstrip() + "…"


def notify(user, text, url="", icon="bi-bell", key=""):
    """Add one notification for one member. With a key, the same notification is never added twice."""
    if not user or not user.is_active:
        return None
    if key and Notification.objects.filter(user=user, key=key).exists():
        return None
    return Notification.objects.create(user=user, text=text[:255], url=url[:300], icon=icon, key=key[:120])


def notify_many(users, text, url="", icon="bi-bell", key=""):
    """Same notification for many members at once (new announcement, new event...)."""
    rows = [Notification(user=u, text=text[:255], url=url[:300], icon=icon, key=key[:120]) for u in users if u.is_active]
    Notification.objects.bulk_create(rows)
    return len(rows)


def admins():
    return User.objects.filter(Q(is_staff=True) | Q(is_superuser=True), is_active=True)


def notify_admins(text, url="", icon="bi-shield-exclamation", key=""):
    for admin in admins():
        notify(admin, text, url, icon, key)


def everyone_except(user=None):
    people = User.objects.filter(is_active=True)
    return people.exclude(pk=user.pk) if user else people


def purge_old():
    Notification.objects.filter(created_at__lt=timezone.now() - Notification.KEEP_FOR).delete()


def admin_url(app_model):
    """Link to an admin list page, e.g. 'community_listing'."""
    return reverse(f"admin:{app_model}_changelist")


# --- Island Chat: someone answered your question -------------------------------------------------

ANSWER_WINDOW = timedelta(hours=6)


def chat_answered(message):
    """When someone posts in the chat, tell people who asked a question there in the last 6 hours.
    Each question gets one notification, from the first person who answers it."""
    from .models import ChatMessage
    since = message.created_at - ANSWER_WINDOW
    questions = (ChatMessage.objects.filter(created_at__gte=since, created_at__lt=message.created_at,
                                            moderation_status="approved", body__contains="?")
                 .exclude(user=message.user).select_related("user"))
    from .templatetags.community_extras import display_name
    who = display_name(message.user)
    for question in questions:
        notify(question.user, f"{who} posted in Island Chat after your question “{short(question.body, 50)}”",
               f"{reverse('chat')}#m{message.pk}", "bi-chat-dots", key=f"chat-answer-{question.pk}")
