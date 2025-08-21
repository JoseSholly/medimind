from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from hospitals.models import Hospital
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Doctor, Patient
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


class OTPVerificationSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, allow_null=False)
    session_token = serializers.CharField(max_length=64, allow_null=False)

    def validate(self, attrs):
        """
        Validate that otp and session_token are provided and valid.
        """
        otp = attrs.get("otp")
        session_token = attrs.get("session_token")

        if otp is None or session_token is None:
            raise serializers.ValidationError({"OTP and session token are required."})

        return attrs

    def to_internal_value(self, data):
        """
        Process incoming data without custom error formatting.
        """
        return super().to_internal_value(data)

    def to_representation(self, instance):
        """
        Format successful responses without interfering with errors.
        """
        return super().to_representation(instance)


class DoctorOnboardingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ["specialization", "license_number", "years_of_experience", "hospital_affiliation"]

    def create(self, validated_data):
        user = self.context["request"].user
        return Doctor.objects.create(user=user, **validated_data)

class PatientOnboardingSerializer(serializers.ModelSerializer):
    # User-related fields
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    age = serializers.IntegerField(write_only=True)
    gender = serializers.ChoiceField(choices=[("male", "Male"), ("female", "Female")], write_only=True)

    # Patient-related fields
    hospital_id = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    medical_history = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Patient
        fields = [
            "first_name", "last_name", "age", "gender",
            "hospital_id", "medical_history"
        ]

    def create(self, validated_data):
        user = self.context['request'].user
        hospital_id = validated_data.pop("hospital_id", None)

        # Update the user's fields
        user.first_name = validated_data.get("first_name")
        user.last_name = validated_data.get("last_name")
        user.age = validated_data.get("age")
        user.gender = validated_data.get("gender")
        user.save()

        # Find hospital if hospital_id is provided
        hospital = None
        if hospital_id:
            hospital = Hospital.objects.filter(hospital_id=hospital_id).first()
            if not hospital:
                raise serializers.ValidationError({"hospital_id": "Invalid hospital ID."})

        # Create patient profile
        try:
            patient = Patient.objects.create(
                user=user,
                hospital=hospital,
                medical_history=validated_data.get("medical_history", ""),
                assigned_doctor=None,  # assigned later by hospital
            )
        except IntegrityError:
            raise IntegrityError("User already has a patient profile.")
        
        return patient


class HospitalOnboardingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ["hospital_name", "address", "registration_number"]

    def create(self, validated_data):
        user = self.context["request"].user
        return Hospital.objects.create(user=user, **validated_data)