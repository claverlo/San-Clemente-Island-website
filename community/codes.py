"""One-time codes emailed to members (verify email at sign-up, reset a forgotten password)."""
import secrets

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


def seconds_until_resend(user, purpose):
    """How long the member must wait before another code can be sent (0 means send now)."""
    latest = EmailCode.objects.filter(user=user, purpose=purpose).first()
    if not latest:
        return 0
    wait = (latest.created_at + EmailCode.RESEND_WAIT) - timezone.now()
    return max(0, int(wait.total_seconds()) + 1) if wait.total_seconds() > 0 else 0


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
