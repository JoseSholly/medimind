from rest_framework import viewsets

from .models import Hospital
from .serializers import HospitalDetailSerializer, HospitalListSerializer


class HospitalListViewSet(viewsets.ModelViewSet):
    queryset = Hospital.objects.all()
    serializer_class = HospitalListSerializer
    lookup_field = 'hospital_id'
    http_method_names = ['get']


    def get_serializer_class(self):
        if self.action == 'list':
            return HospitalListSerializer
        return HospitalDetailSerializer