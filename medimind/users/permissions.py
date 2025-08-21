from rest_framework.permissions import BasePermission


class IsHospital(BasePermission):
    """
    Allows access only to authenticated users who are hospital accounts.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.user_type == "hospital" and request.user.is_hospital)