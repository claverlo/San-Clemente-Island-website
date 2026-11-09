def notification_bell(request):
    """The bell in the top menu: the latest few notifications and how many are waiting to be cleared."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}
    notes = user.notifications.all()
    return {
        "bell_count": notes.count(),  # stays until the member clears them
        "bell_items": list(notes[:8]),
    }
