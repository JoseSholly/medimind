from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from users.validators import validate_email_address

User = get_user_model()

class HospitalSignUpEmailPasswordSerializer(serializers.Serializer):
    """
    Serializer for the initial hospital signup step: email and password.
    """
    email = serializers.EmailField(
        max_length=100,
        help_text=_("Contact email of the hospital."),
        required=True
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        help_text=_("Password for the hospital account.")
    )

    def validate(self, data):
        """
        Check that the two password fields match.
        """
        return data

    def validate_email(self, value):
        """
        Check if a user with this email already exists.
        """
        try:
            validate_email_address(value)
        except serializers.ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value