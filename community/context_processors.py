def notification_bell(request):
    """The bell in the top menu: the latest few notifications and how many are unread."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}
    notes = user.notifications.all()
    return {
        "bell_unread": notes.filter(read=False).count(),
        "bell_items": list(notes[:8]),
    }
