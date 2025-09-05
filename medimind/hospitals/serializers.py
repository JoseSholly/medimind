from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import Hospital

User = get_user_model()
class HospitalListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ['hospital_id', 'name', 'address']

class HospitalDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        exclude = ['id', 'created_at', 'updated_at']


class HospitalOwnerInfoSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(read_only=True)  # prevent editing

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "age", "gender"]


class HospitalUpdateSerializer(serializers.ModelSerializer):
    owner_info = HospitalOwnerInfoSerializer(source="user", required=False)

    class Meta:
        model = Hospital
        fields = [
            "name", "description", "address",
            "contact_email", "website_link", "owner_info"
        ]

    @transaction.atomic
    def update(self, instance, validated_data):
        # Pop nested user data
        user_data = validated_data.pop("user", {})
        if user_data:
            for attr, value in user_data.items():
                setattr(instance.user, attr, value)
            instance.user.save()

        # Update hospital fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class HospitalProfileDetailSerializer(serializers.ModelSerializer):
    owner_info = HospitalOwnerInfoSerializer(source="user", read_only=True)

    class Meta:
        model = Hospital
        fields = [
            "hospital_id", "name", "description", "address",
            "contact_email", "website_link", "owner_info"
        ]
        read_only_fields = ["hospital_id"]     