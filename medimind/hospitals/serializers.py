from rest_framework import serializers

from .models import Hospital


class HospitalListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ['hospital_id', 'name', 'address']

class HospitalDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        exclude = ['id', 'created_at', 'updated_at']