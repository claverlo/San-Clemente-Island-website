from rest_framework.permissions import BasePermission


class IsAdminSession(BasePermission):
    message = "Admin access required. Log in at /admin/login/?next=/admin/ with a staff account."

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.is_staff)
