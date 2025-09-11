from drf_yasg.utils import swagger_auto_schema
from medications.serializers import (
    PrescriptionCreateSerializer,
    PrescriptionDetailSerializer,
    PrescriptionDrugTimelineSerializer,
)
from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Prescription


class PrescriptionCreateAPIView(APIView):
    """
    Allow doctors to create prescriptions for patients.
    """

    permission_classes = [permissions.IsAuthenticated]


    @swagger_auto_schema(
        tags=["Prescription"],
        request_body=PrescriptionCreateSerializer,
        operation_summary="Doctor create prescription for patient",
    )
    def post(self, request, *args, **kwargs):
        # Ensure only doctors can create prescriptions
        if not hasattr(request.user, "doctor"):
            return Response(
                {"detail": "Only doctors can create prescriptions."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = PrescriptionCreateSerializer(
            data=request.data,
            context={"request": request}  
        )

        if serializer.is_valid():
            prescription = serializer.save()
            data = PrescriptionCreateSerializer(prescription).data
            return Response(
                {
                    "status": "sucesss",
                    "message": "Prescription created sucessfully",
                    "data": data
                }
                ,
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PrescriptionDetailView(generics.RetrieveAPIView):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "prescription_id"

    def retrieve(self, request, *args, **kwargs):
        prescription = self.get_object()
        drug_id = self.kwargs.get("drug_id")

        drug = prescription.drugs.filter(drug_id=drug_id).first()
        if not drug:
            raise NotFound("Drug not found for this prescription")

        serializer = self.get_serializer(prescription)
        data = dict(serializer.data)

        # Replace drugs array with single drug (with timeline & real logs)
        drug_serializer = PrescriptionDrugTimelineSerializer()
        data["drug"] = drug_serializer.to_representation(drug)
        if "drugs" in data:
            del data["drugs"]

        return Response(data)

