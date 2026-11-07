from django import template

register = template.Library()


def display_name(user):
    """The name other people see. Never shows an email address."""
    if not user:
        return ""
    full = user.get_full_name().strip()
    if full:
        return full
    return user.username.split("@")[0]


register.filter("display_name", display_name)
