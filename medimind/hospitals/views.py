from rest_framework import generics, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsHospital

from .models import Hospital
from .serializers import (
    HospitalDetailSerializer,
    HospitalListSerializer,
    HospitalProfileDetailSerializer,
    HospitalUpdateSerializer,
)


class HospitalListViewSet(viewsets.ModelViewSet):
    queryset = Hospital.objects.all()
    serializer_class = HospitalListSerializer
    lookup_field = 'hospital_id'
    http_method_names = ['get']


    def get_serializer_class(self):
        if self.action == 'list':
            return HospitalListSerializer
        return HospitalDetailSerializer
    


class HospitalProfileUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsHospital]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return HospitalUpdateSerializer
        return HospitalProfileDetailSerializer

    def get_object(self):
        if not hasattr(self.request.user, "hospital"):
            raise ValidationError({"detail": "No hospital profile associated with this user."})
        return self.request.user.hospital