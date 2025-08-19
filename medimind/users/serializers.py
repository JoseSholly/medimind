from django.contrib.auth import get_user_model
from rest_framework import serializers
from .validators import validate_email_address

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):

    """
    Serializer for user registration with password validation.
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


    def validate_email(self, value):
        """
        Check if email address is valid.
        """
        try:
            validate_email_address(value)
        except serializers.ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value
    
    def validate(self, data):
        """
        Perform additional object-level validation if needed.
        """
        return data
    
    def create(self, validated_data):
        """
        Create and return a new user instance.
        """
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            is_activated=False,
        )
        return user

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

