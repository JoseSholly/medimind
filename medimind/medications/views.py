from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from medications.serializers import PrescriptionCreateSerializer


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
