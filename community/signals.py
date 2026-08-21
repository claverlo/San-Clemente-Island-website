from django.conf import settings
from django.contrib.auth.signals import user_logged_in
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
