import base64
import json
import mimetypes
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


BLOCKED_PATTERNS = [
    r"\bnude\b",
    r"\bsex\b",
    r"\bporn\b",
    r"\bdrugs?\b",
    r"\bcocaine\b",
    r"\bmeth\b",
    r"\bweapon\b",
    r"\bgun\b",
    r"\bhate\b",
    r"\bkill\b",
]


def moderate_text_fields(*values):
    combined = " ".join((value or "") for value in values).lower()
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, combined, flags=re.IGNORECASE):
            return "pending", "Sent to admin review after automatic text moderation."
    return "approved", "Approved by automatic text review."


def moderate_uploaded_images(files):
    image_files = [file for file in files if file]
    if not image_files:
        return "approved", "Approved with no uploaded images."

    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key:
        return "approved", "Approved (AI image moderation not configured)."

    for image_file in image_files:
        result, reason = _moderate_single_image(image_file, api_key)
        if result != "approved":
            return "pending", reason

    return "approved", "Approved by automatic image review."


def _moderate_single_image(image_file, api_key):
    model = getattr(settings, "OPENAI_IMAGE_MODERATION_MODEL", "gpt-4o-mini")
    raw_bytes = image_file.read()
    if hasattr(image_file, "seek"):
        image_file.seek(0)

    content_type = getattr(image_file, "content_type", None)
    if not content_type:
        content_type = mimetypes.guess_type(getattr(image_file, "name", "image.jpg"))[0] or "image/jpeg"

    encoded = base64.b64encode(raw_bytes).decode("utf-8")
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Review this user-uploaded community listing image. "
                            "If it contains nudity, explicit sexual content, graphic violence, hate imagery, illegal drugs, "
                            "or dangerous weapon promotion, return result=review. Otherwise return result=approved."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{content_type};base64,{encoded}"},
                    },
                ],
            }
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "image_review",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "result": {"type": "string", "enum": ["approved", "review"]},
                        "reason": {"type": "string"},
                    },
                    "required": ["result", "reason"],
                    "additionalProperties": False,
                },
            },
        },
    }

    request = Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return "review", "Awaiting admin review because AI image moderation could not complete."

    try:
        message = body["choices"][0]["message"]["content"]
        review = json.loads(message)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return "review", "Awaiting admin review because AI image moderation returned an invalid response."

    if review.get("result") == "approved":
        return "approved", review.get("reason", "Approved by automatic image review.")
    return "review", review.get("reason", "Awaiting admin review after AI image scan.")
