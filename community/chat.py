import base64
import json
import re
from datetime import timedelta
from io import BytesIO
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Q
from django.utils import timezone
from PIL import Image, ImageOps

from .templatetags.community_extras import display_name

MAX_PHOTO_SIDE = 1600
STOP_WORDS = {
    "a", "an", "and", "any", "anybody", "anyone", "are", "at", "be", "can", "could", "do", "does", "for",
    "hey", "how", "i", "if", "in", "is", "it", "know", "me", "of", "on", "or", "please", "so", "someone",
    "somebody", "tell", "that", "the", "there", "this", "to", "today", "tonight", "was", "what", "whats",
    "when", "where", "which", "who", "why", "will", "with", "you", "yall",
}


def shrink_photo(uploaded):
    """Re-encode an uploaded photo as a JPEG no larger than MAX_PHOTO_SIDE on its longest side."""
    image = ImageOps.exif_transpose(Image.open(uploaded))
    image.thumbnail((MAX_PHOTO_SIDE, MAX_PHOTO_SIDE))
    if image.mode != "RGB":
        image = image.convert("RGB")
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=80, optimize=True)
    name = re.sub(r"\.[^.]+$", "", uploaded.name.rsplit("/", 1)[-1]) or "photo"
    return ContentFile(buffer.getvalue(), name=f"{name}.jpg")


def search_terms(question):
    words = re.findall(r"[a-z0-9']+", question.lower())
    terms = [word.strip("'") for word in words if word.strip("'") not in STOP_WORDS and len(word) > 1]
    return terms or words


def matching_messages(queryset, question):
    terms = search_terms(question)
    if not terms:
        return queryset.none()
    match = Q()
    for term in terms:
        match |= Q(body__icontains=term)
        # Also match the plain singular, so "hours" finds "hour" and "stores" finds "store".
        if len(term) > 3 and term.endswith("s"):
            match |= Q(body__icontains=term[:-1])
    return queryset.filter(match)


def with_replies(queryset, matches, window=timedelta(hours=6), per_match=5):
    """Add the messages posted shortly after each match, since answers often don't repeat the question's words."""
    found = {message.pk: message for message in matches}
    for message in matches:
        later = queryset.filter(created_at__gt=message.created_at, created_at__lte=message.created_at + window).order_by("created_at")[:per_match]
        for reply in later:
            found.setdefault(reply.pk, reply)
    return sorted(found.values(), key=lambda m: m.created_at, reverse=True)


def ai_answer(question, text_messages, photo_messages):
    """Ask the AI to answer from chat messages only. Returns (answer, cited message ids) or (None, [])."""
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key or not (text_messages or photo_messages):
        return None, []

    now = timezone.localtime()
    lines = [f"Current date and time: {now:%A, %B %d %Y, %I:%M %p}.", "Chat messages:"]
    for message in text_messages:
        lines.append(f"[id {message.pk}] {display_name(message.user)} at {timezone.localtime(message.created_at):%a %b %d, %I:%M %p}: {message.body}")
    content = [{"type": "text", "text": "\n".join(lines)}]
    for message in photo_messages:
        try:
            with message.image.open("rb") as photo:
                encoded = base64.b64encode(photo.read()).decode("utf-8")
        except (OSError, ValueError):
            continue
        content.append({"type": "text", "text": f"[id {message.pk}] Photo posted by {display_name(message.user)} at {timezone.localtime(message.created_at):%a %b %d, %I:%M %p}. Caption: {message.body or '(none)'}"})
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}", "detail": "low"}})

    payload = {
        "model": getattr(settings, "OPENAI_CHAT_SEARCH_MODEL", "gpt-4o-mini"),
        "messages": [
            {
                "role": "system",
                "content": (
                    "You answer questions for a small island community chat board. Use ONLY the chat messages and photos given. "
                    "Credit who said it and when, e.g. 'According to sailor (today, 2:10 PM), the store is open 8 AM to 3 PM.' "
                    "Prefer the newest information and say so if older messages disagree. If the messages do not answer the question, "
                    "say nobody in the chat has answered that yet. Keep it to 1-3 short sentences. "
                    "Return the ids of the messages you relied on."
                ),
            },
            {"role": "user", "content": content + [{"type": "text", "text": f"Question: {question}"}]},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "chat_answer",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "answer": {"type": "string"},
                        "message_ids": {"type": "array", "items": {"type": "integer"}},
                    },
                    "required": ["answer", "message_ids"],
                    "additionalProperties": False,
                },
            },
        },
    }
    request = Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
        result = json.loads(body["choices"][0]["message"]["content"])
    except (HTTPError, URLError, TimeoutError, KeyError, IndexError, TypeError, json.JSONDecodeError):
        return None, []
    return result.get("answer") or None, [i for i in result.get("message_ids", []) if isinstance(i, int)]
