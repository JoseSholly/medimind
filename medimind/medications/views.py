import logging

from drf_yasg.utils import swagger_auto_schema
from notifications.utils import send_prescription_notification
from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from medications.serializers import (
    PrescriptionCreateSerializer,
    PrescriptionDetailSerializer,
    PrescriptionDrugTimelineSerializer,
)

from datetime import datetime

from .models import Prescription

logger = logging.getLogger(__name__)


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
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            prescription = serializer.save()

            # Notify patient via WhatsApp
            patient_name = prescription.patient.user.get_full_name()
            doctor_name = request.user.get_full_name()
            start_date = prescription.start_date
            drugs_data = []
            for drug in prescription.drugs.all():
                daily_times_24h = drug.get_daily_times()
                daily_times_12h = []
                for time_str in daily_times_24h:
                    # Parse the 24-hour time string
                    time_obj = datetime.strptime(time_str, "%H:%M")
                    # Format to 12-hour string with AM/PM
                    daily_times_12h.append(time_obj.strftime("%I:%M %p"))

                drugs_data.append(
                    {
                        "drug_name": drug.drug_name,
                        "dosage_instruction": drug.dosage_instruction,
                        "frequency_per_day": drug.frequency_per_day,
                        "duration_days": drug.duration_days,
                        "daily_times": daily_times_12h,
                        # Convert date objects to a string format for readability
                        "start_date": start_date.strftime("%B %d, %Y"),
                        "end_date": drug.get_end_date().strftime("%B %d, %Y"),
                    }
                )

            try:
                send_prescription_notification(
                    phone_number="+2348177249074",
                    patient_name=patient_name,
                    doctor_name=doctor_name,
                    drugs=drugs_data,
                )
            except Exception as e:
                logger.warning(f"WhatsApp notification failed: {e}")

            data = PrescriptionCreateSerializer(prescription).data
            return Response(
                {
                    "status": "sucesss",
                    "message": "Prescription created sucessfully",
                    "data": data,
                },
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
