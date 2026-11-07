"""Face ID / fingerprint / Windows Hello sign-in using passkeys (WebAuthn).

The phone or laptop keeps a private key that only unlocks with the owner's face, finger or device PIN.
The website stores just the matching public key, so there is no password to steal.
"""
import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from .models import Passkey, Profile

RP_NAME = "SCI Connect"
SIGNED_IN_FOR = timedelta(days=30)  # a passkey only works on the owner's own device, so treat it as trusted
LOCAL_HOSTS = {"localhost", "127.0.0.1"}


def site_ids(request):
    """The website name the passkey is tied to (e.g. www.sciconnect.net) and the exact origin browsers report."""
    host = request.get_host()
    domain = host.split(":")[0]
    scheme = "http" if domain in LOCAL_HOSTS else "https"
    return domain, f"{scheme}://{host}"


def device_name(request):
    agent = request.META.get("HTTP_USER_AGENT", "")
    for needle, name in (("iPhone", "iPhone"), ("iPad", "iPad"), ("Android", "Android phone"),
                         ("Macintosh", "Mac"), ("Windows", "Windows computer"), ("CrOS", "Chromebook")):
        if needle in agent:
            return name
    return "This device"


def body_json(request):
    try:
        return json.loads(request.body or b"{}")
    except ValueError:
        return {}


@login_required
@require_POST
def register_options(request):
    rp_id, _ = site_ids(request)
    user = request.user
    options = generate_registration_options(
        rp_id=rp_id,
        rp_name=RP_NAME,
        user_id=str(user.pk).encode(),
        user_name=user.email or user.username,
        user_display_name=user.get_full_name() or user.email or user.username,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(key.credential_id)) for key in user.passkeys.all()
        ],
    )
    request.session["passkey_register_challenge"] = bytes_to_base64url(options.challenge)
    return JsonResponse(json.loads(options_to_json(options)))


@login_required
@require_POST
def register_verify(request):
    challenge = request.session.pop("passkey_register_challenge", None)
    rp_id, origin = site_ids(request)
    if not challenge:
        return JsonResponse({"error": "That took too long. Please try again."}, status=400)
    try:
        verified = verify_registration_response(
            credential=body_json(request),
            expected_challenge=base64url_to_bytes(challenge),
            expected_rp_id=rp_id,
            expected_origin=origin,
            require_user_verification=True,
        )
    except Exception:
        return JsonResponse({"error": "Your device didn't confirm it. Please try again."}, status=400)
    credential_id = bytes_to_base64url(verified.credential_id)
    if Passkey.objects.filter(credential_id=credential_id).exists():
        return JsonResponse({"error": "This device is already set up."}, status=400)
    Passkey.objects.create(
        user=request.user,
        credential_id=credential_id,
        public_key=bytes_to_base64url(verified.credential_public_key),
        sign_count=verified.sign_count,
        name=device_name(request),
    )
    messages.success(request, "Face ID / fingerprint sign-in is on for this device.")
    return JsonResponse({"ok": True, "redirect": reverse("dashboard") + "#passkeys"})


@require_POST
def login_options(request):
    rp_id, _ = site_ids(request)
    options = generate_authentication_options(rp_id=rp_id, user_verification=UserVerificationRequirement.REQUIRED)
    request.session["passkey_login_challenge"] = bytes_to_base64url(options.challenge)
    return JsonResponse(json.loads(options_to_json(options)))


@require_POST
def login_verify(request):
    challenge = request.session.pop("passkey_login_challenge", None)
    rp_id, origin = site_ids(request)
    data = body_json(request)
    passkey = Passkey.objects.select_related("user").filter(credential_id=data.get("id", "")).first()
    if not challenge or not passkey:
        return JsonResponse({"error": "We don't recognize that Face ID / fingerprint. Sign in with your email and password, then turn it on from your dashboard."}, status=400)
    try:
        verified = verify_authentication_response(
            credential=data,
            expected_challenge=base64url_to_bytes(challenge),
            expected_rp_id=rp_id,
            expected_origin=origin,
            credential_public_key=base64url_to_bytes(passkey.public_key),
            credential_current_sign_count=passkey.sign_count,
            require_user_verification=True,
        )
    except Exception:
        return JsonResponse({"error": "Your device didn't confirm it. Please try again."}, status=400)
    user = passkey.user
    if not user.is_active:
        return JsonResponse({"error": "This account is turned off."}, status=403)
    passkey.sign_count = verified.new_sign_count
    passkey.last_used_at = timezone.now()
    passkey.save(update_fields=["sign_count", "last_used_at"])
    # The owner just proved it's them on their own device, so clear any wrong-password lock.
    Profile.objects.filter(user=user).update(failed_logins=0, login_locked=False)
    login(request, user, backend="community.backends.EmailOrUsernameBackend")
    request.session.set_expiry(int(SIGNED_IN_FOR.total_seconds()))
    next_url = data.get("next") or ""
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = reverse("dashboard")
    return JsonResponse({"ok": True, "redirect": next_url})


@login_required
@require_POST
def delete(request, pk):
    passkey = get_object_or_404(Passkey, pk=pk, user=request.user)
    passkey.delete()
    messages.success(request, f"Face ID / fingerprint sign-in was turned off for {passkey.name}.")
    return redirect(reverse("dashboard") + "#passkeys")
