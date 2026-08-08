import base64
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from django.conf import settings


def send_phone_verification_text(phone_number, code):
    account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
    auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
    from_number = getattr(settings, "TWILIO_FROM_NUMBER", "")

    if not (account_sid and auth_token and from_number):
        return False, "SMS provider is not configured yet."

    message = f"Your SCI List verification code is {code}. It expires in 10 minutes."
    body = urlencode({"To": phone_number, "From": from_number, "Body": message}).encode("utf-8")
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

    credentials = f"{account_sid}:{auth_token}".encode("utf-8")
    auth_header = base64.b64encode(credentials).decode("utf-8")

    request = Request(url, data=body, method="POST")
    request.add_header("Authorization", f"Basic {auth_header}")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urlopen(request, timeout=15) as response:
            status_code = response.getcode()
            if 200 <= status_code < 300:
                return True, ""
            payload = json.loads(response.read().decode("utf-8") or "{}")
            return False, payload.get("message", "Failed to send verification text.")
    except HTTPError as error:
        try:
            payload = json.loads(error.read().decode("utf-8") or "{}")
            return False, payload.get("message", "Failed to send verification text.")
        except Exception:
            return False, "Failed to send verification text."
    except (URLError, TimeoutError):
        return False, "Unable to reach SMS provider."
