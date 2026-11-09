import re

from django.core.mail import get_connection, EmailMessage
from django.urls import reverse

from .models import Profile


def keyword_pattern(word):
    """Match the word on its own, with or without a plural ending (shoe, shoes; slipper, slippers)."""
    word = word.lower()
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        word = word[:-1]
    return re.compile(r"\b" + re.escape(word) + r"(e?s)?\b", re.IGNORECASE)


def matching_keyword(profile, text):
    for word in profile.alert_keyword_list:
        if keyword_pattern(word).search(text):
            return word
    return None


def notify_subscribers(request, category, title, path, poster, text=""):
    """Email everyone who turned on alerts for this category or for a word in the post. One email per person."""
    text = f"{title} {text}"
    recipients = []
    for profile in Profile.objects.select_related("user").exclude(user=poster):
        if not (profile.email_verified and profile.user.email and profile.user.is_active):
            continue
        if category in (profile.alert_categories or []):
            recipients.append((profile, None))
        else:
            word = matching_keyword(profile, text)
            if word:
                recipients.append((profile, word))
    if not recipients:
        return 0

    from .bell import notify, short
    for profile, word in recipients:
        why = f'mentions “{word}”' if word else f"in {category}"
        notify(profile.user, f"New post {why}: {short(title, 70)}", path, "bi-bell-fill")

    post_url = request.build_absolute_uri(path)
    settings_url = request.build_absolute_uri(reverse("dashboard") + "#email-alerts")
    emails = []
    for profile, word in recipients:
        stop_url = request.build_absolute_uri(reverse("alerts_off", args=[profile.alerts_token]))
        if word:
            subject = f'New on SCI Connect (mentions "{word}"): {title}'
            intro = f'Something new was just posted that mentions "{word}":'
            reason = f'You\'re getting this because you asked to hear about "{word}".'
        else:
            subject = f"New on SCI Connect ({category}): {title}"
            intro = f"Something new was just posted in {category}:"
            reason = f"You're getting this because you turned on {category} alerts."
        emails.append(EmailMessage(
            subject,
            f"{intro}\n\n{title}\n{post_url}\n\n{reason}\n"
            f"Change your alerts: {settings_url}\n"
            f"Turn off all alerts: {stop_url}",
            None,
            [profile.user.email],
        ))
    get_connection(fail_silently=True).send_messages(emails)
    return len(emails)
