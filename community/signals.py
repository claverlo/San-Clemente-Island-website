from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.core.mail import send_mail
from django.dispatch import receiver
from django.utils import timezone


@receiver(user_logged_in)
def notify_admin_of_staff_login(sender, request, user, **kwargs):
    if not user.is_staff:
        return

    ip = request.META.get("REMOTE_ADDR", "unknown IP") if request else "unknown IP"
    send_mail(
        f"SCI List: staff login - {user.username}",
        f"{user.username} logged in at {timezone.now():%Y-%m-%d %H:%M %Z} from {ip}.\n\n"
        "If this wasn't you, change your password immediately.",
        None,
        [settings.REPORT_ADMIN_EMAIL],
        fail_silently=True,
    )


@receiver(user_login_failed)
def count_failed_login(sender, credentials, request=None, **kwargs):
    """Every wrong password, on any login page (site, admin, map), counts toward the limit."""
    from .limits import client_ip, record
    from .backends import login_key
    record("login-fail-account", login_key(credentials.get("username")))
    record("login-fail-ip", client_ip(request))


# --- Notification bell -----------------------------------------------------------------------------
from django.db.models.signals import post_save, pre_save  # noqa: E402
from django.urls import reverse  # noqa: E402

from . import bell  # noqa: E402
from .models import Announcement, ChatMessage, ContactMessage, ContentReport, Event, Listing, LostFound  # noqa: E402

MODERATED = (Listing, LostFound, ChatMessage)


def _owner(item):
    return getattr(item, "seller", None) or getattr(item, "user", None)


def _describe(item):
    if isinstance(item, Listing):
        return f"post \u201c{bell.short(item.title, 50)}\u201d", item.get_absolute_url(), "community_listing"
    if isinstance(item, LostFound):
        return f"Lost & Found post \u201c{bell.short(item.item, 50)}\u201d", reverse("lost_found"), "community_lostfound"
    return f"chat message \u201c{bell.short(item.body or 'photo', 50)}\u201d", f"{reverse('chat')}#m{item.pk}", "community_chatmessage"


@receiver(pre_save)
def remember_old_status(sender, instance, **kwargs):
    if sender in MODERATED and instance.pk:
        instance._old_status = sender._base_manager.filter(pk=instance.pk).values_list("moderation_status", flat=True).first()


@receiver(post_save)
def moderation_notifications(sender, instance, created, **kwargs):
    if sender not in MODERATED or kwargs.get("raw"):
        return
    status = instance.moderation_status
    old = None if created else getattr(instance, "_old_status", None)
    what, url, admin_model = _describe(instance)
    owner = _owner(instance)
    if status == "pending" and old != "pending":
        bell.notify_admins(f"Needs your approval: {what}", bell.admin_url(admin_model), "bi-hourglass-split")
    if old == "pending" and status == "approved":
        bell.notify(owner, f"Your {what} was approved and is now live.", url, "bi-check-circle")
    if old != "rejected" and status == "rejected" and not created:
        reason = f" Reason: {instance.moderation_notes}" if instance.moderation_notes else ""
        bell.notify(owner, f"Your {what} wasn't approved.{reason}", reverse("dashboard"), "bi-x-circle")
    if sender is ChatMessage and status == "approved" and (created or old == "pending"):
        bell.chat_answered(instance)


@receiver(post_save, sender=ContentReport)
def report_notification(sender, instance, created, **kwargs):
    if not created or kwargs.get("raw"):
        return
    item = instance.listing or instance.lost_found or instance.chat_message
    what = _describe(item)[0] if item else "an item"
    reason = f" \u2013 \u201c{bell.short(instance.reason, 60)}\u201d" if instance.reason else ""
    bell.notify_admins(f"Someone reported a {what}{reason}", bell.admin_url("community_contentreport"), "bi-flag")


@receiver(post_save, sender=ContactMessage)
def contact_notification(sender, instance, created, **kwargs):
    if created and not kwargs.get("raw"):
        bell.notify_admins(f"New Contact us message from {bell.short(instance.name, 40)}",
                           bell.admin_url("community_contactmessage"), "bi-envelope")


@receiver(post_save, sender=Announcement)
def announcement_notification(sender, instance, created, **kwargs):
    if created and not kwargs.get("raw"):
        icon = "bi-megaphone-fill" if instance.priority in ("Important", "Urgent") else "bi-megaphone"
        label = f"{instance.priority} announcement" if instance.priority != "Routine" else "New announcement"
        bell.notify_many(bell.everyone_except(), f"{label}: {bell.short(instance.title, 80)}", reverse("announcements"), icon)


@receiver(post_save, sender=Event)
def event_notification(sender, instance, created, **kwargs):
    if created and not kwargs.get("raw"):
        day = timezone.localtime(instance.date)
        when = f"{day:%a %b} {day.day}"
        bell.notify_many(bell.everyone_except(), f"New event: {bell.short(instance.title, 70)} ({when})", reverse("events"), "bi-calendar-event")
