from rest_framework.permissions import BasePermission


class IsHospital(BasePermission):
    """
    Allows access only to authenticated users who are hospital accounts.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.user_type == "hospital" and request.user.is_hospital)
    
class IsActivated(BasePermission):
    """
    Custom permission to only allow activated users to access the view.
    """

    message = "Your account is inactive. Please activate your account to access this resource."

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False  # Deny access to anonymous users

        # Check if the user is activated
        return request.user.is_activated