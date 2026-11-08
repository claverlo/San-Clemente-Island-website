"""One-time codes emailed to members (verify email at sign-up, reset a forgotten password)."""
import secrets
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.utils import timezone

from .models import EmailCode

SUBJECTS = {
    EmailCode.VERIFY: "Your SCI Connect verification code",
    EmailCode.RESET: "Your SCI Connect password reset code",
}
REASONS = {
    EmailCode.VERIFY: "to verify your email",
    EmailCode.RESET: "to reset your password",
}


CODES_PER_DAY = 5  # with 5 tries per code, at most 25 guesses a day out of a million possible codes


def seconds_until_resend(user, purpose):
    """How long the member must wait before another code can be sent (0 means send now)."""
    now = timezone.now()
    recent = list(EmailCode.objects.filter(user=user, purpose=purpose, created_at__gte=now - timedelta(days=1))
                  .order_by("created_at").values_list("created_at", flat=True))
    if not recent:
        return 0
    waits = [(recent[-1] + EmailCode.RESEND_WAIT) - now]
    if len(recent) >= CODES_PER_DAY:
        waits.append((recent[-CODES_PER_DAY] + timedelta(days=1)) - now)
    wait = max(waits).total_seconds()
    return int(wait) + 1 if wait > 0 else 0


def wait_text(seconds):
    """'45 seconds', '12 minutes' or '3 hours' for messages."""
    if seconds < 120:
        return f"{seconds} seconds"
    if seconds < 2 * 3600:
        return f"{seconds // 60} minutes"
    return f"{seconds // 3600} hours"


def send_code(user, purpose, extra_text=""):
    """Make a fresh 6-digit code, email it, and cancel any older codes for the same purpose."""
    code = f"{secrets.randbelow(1_000_000):06d}"
    EmailCode.objects.filter(user=user, purpose=purpose, used=False).update(used=True)
    EmailCode.objects.create(
        user=user, purpose=purpose, code_hash=make_password(code),
        expires_at=timezone.now() + EmailCode.LIFETIME,
    )
    minutes = int(EmailCode.LIFETIME.total_seconds() // 60)
    send_mail(
        f"{SUBJECTS[purpose]}: {code}",
        f"Your SCI Connect code is:\n\n    {code}\n\n"
        f"Type it on the website {REASONS[purpose]}. It expires in {minutes} minutes.\n"
        f"{extra_text}"
        f"\nIf you didn't ask for this, you can ignore this email. Never share this code with anyone.",
        None,
        [user.email],
        fail_silently=False,
    )
    return code


def check_code(user, purpose, code):
    """True if the code is right. Each code works once, expires, and allows only a few tries."""
    code = "".join(ch for ch in (code or "") if ch.isdigit())
    if not user or len(code) != 6:
        return False
    entry = EmailCode.objects.filter(user=user, purpose=purpose, used=False).first()
    if not entry or entry.expires_at < timezone.now() or entry.tries >= EmailCode.MAX_TRIES:
        return False
    if check_password(code, entry.code_hash):
        entry.used = True
        entry.save(update_fields=["used"])
        return True
    entry.tries += 1
    entry.save(update_fields=["tries"])
    return False
