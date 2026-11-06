from django.core.mail import get_connection, EmailMessage
from django.urls import reverse

from .models import Profile


def notify_subscribers(request, category, title, path, poster):
    """Email everyone who turned on alerts for this category. Returns how many emails were queued."""
    recipients = [
        profile for profile in Profile.objects.select_related("user").exclude(user=poster)
        if category in (profile.alert_categories or []) and profile.email_verified and profile.user.email and profile.user.is_active
    ]
    if not recipients:
        return 0

    post_url = request.build_absolute_uri(path)
    settings_url = request.build_absolute_uri(reverse("dashboard") + "#email-alerts")
    emails = []
    for profile in recipients:
        stop_url = request.build_absolute_uri(reverse("alerts_off", args=[profile.alerts_token]))
        emails.append(EmailMessage(
            f"New on SCI Connect ({category}): {title}",
            f"Something new was just posted in {category}:\n\n{title}\n{post_url}\n\n"
            f"You're getting this because you turned on {category} alerts.\n"
            f"Change your alerts: {settings_url}\n"
            f"Turn off all alerts: {stop_url}",
            None,
            [profile.user.email],
        ))
    get_connection(fail_silently=True).send_messages(emails)
    return len(emails)
