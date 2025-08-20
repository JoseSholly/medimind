from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .validators import validate_email_address

User = get_user_model()

class BaseRegistrationSerializer(serializers.ModelSerializer):
    """
    Base serializer for user registration.
    Subclasses must define `user_type`.
    """
    email = serializers.CharField(
        max_length=254,
        required=True
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        min_length=8,
        max_length=70,
    )

    class Meta:
        model = User
        fields = ["email", "password"]

    # Each child serializer should set this
    user_type = None  

    def validate_email(self, value):
        """Check if email address is valid."""
        try:
            validate_email_address(value)
        except serializers.ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate(self, data):
        """Perform additional object-level validation if needed."""
        return data

    def create(self, validated_data):
        """Create and return a new user instance with the correct user_type."""
        if not self.user_type:
            raise ValueError("user_type must be set in the subclass.")
        
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            user_type=self.user_type,
            is_activated=False,
        )
        return user

    def to_internal_value(self, data):
        """Process incoming data without custom error formatting."""
        return super().to_internal_value(data)

    def to_representation(self, instance):
        """Format successful responses without interfering with errors."""
        return super().to_representation(instance)


# --- Specialized Serializers ---

class PatientRegistrationSerializer(BaseRegistrationSerializer):
    user_type = "patient"


class DoctorRegistrationSerializer(BaseRegistrationSerializer):
    user_type = "doctor"


class HospitalRegistrationSerializer(BaseRegistrationSerializer):
    user_type = "hospital"

class EmailLoginSerializer(TokenObtainPairSerializer):
    # override fields: use email instead of username
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")


        errors = {}
        if not email:
            errors["email"] = ["This field is required."]
        if not password:
            errors["password"] = ["This field is required."]
        if errors:
            raise serializers.ValidationError(errors)

        # normalize email
        email = email.lower()

        # validate email format
        try:
            validate_email_address(email)
        except DjangoValidationError:
            raise serializers.ValidationError({"email": ["Enter a valid email address."]})

        # check user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"non_field_errors": ["Invalid credentials."]})

        # check password
        if not user.check_password(password):
            raise serializers.ValidationError({"non_field_errors": ["Invalid credentials."]})


        # generate tokens
        refresh = self.get_token(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
            },
        }