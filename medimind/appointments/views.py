from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from users.permissions import IsActivated, IsDoctor, IsHospital, IsPatient

from .models import Appointment
from .serializers import (
    AppointmentBookingSerializer,
    AppointmentRescheduleSerializer,
    AppointmentSerializer,
    AppointmentStatusUpdateSerializer,
)


class PatientAppointmentListCreateAPIView(APIView):
    """
    Patients can:
    - GET: List their appointments
    - POST: Book a new appointment
    """

    permission_classes = [permissions.IsAuthenticated, IsActivated, IsPatient]

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method in ["POST"]:
            return AppointmentBookingSerializer(*args, **kwargs)
        return AppointmentSerializer(*args, **kwargs)

    @swagger_auto_schema(
        tags=["Appointments"],
        responses={200: AppointmentSerializer(many=True)},
        operation_summary="List Patient Appointments",
    )
    def get(self, request):
        queryset = Appointment.objects.filter(patient=request.user.patient)

        # filter by status if provided
        status_param = request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param.lower())

        appointments = queryset.order_by("-date", "-time")

        serializer = self.get_serializer_class(appointments, many=True)
        data = serializer.data
        return Response(
            {
                "status": "success",
                "appointment": data,
            },
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["Appointments"],
        request_body=AppointmentBookingSerializer,
        operation_summary="Book a New Appointment with Doctor assigned to same hospital as patient",
    )
    def post(self, request):
        serializer = AppointmentBookingSerializer(
            data=request.data, context={"request": request}
        )
        # Check if the serializer is valid before attempting to save
        if serializer.is_valid():
            try:
                appointment = serializer.save()
                data = self.get_serializer_class(appointment).data
                return Response(
                    {
                        "status": "success",
                        "appointment": data,
                    },
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                # Handle unexpected exceptions during the save process
                return Response(
                    {
                        "status": "error",
                        "detail": str(e),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            # Return validation errors if the data is invalid
            return Response(
                {
                    "status": "error",
                    "detail": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


# Doctor Side


class DoctorAppointmentListAPIView(APIView):
    """
    Doctors can:
    - GET: View all their appointments (any status)
    """

    permission_classes = [permissions.IsAuthenticated, IsActivated, IsDoctor]

    @swagger_auto_schema(
        tags=["Appointments"],
        responses={200: AppointmentSerializer(many=True)},
        operation_summary="List Doctor Appointments",
    )
    def get(self, request):
        queryset = Appointment.objects.filter(doctor=request.user.doctor)

        # filter by status if provided
        status_param = request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param.lower())

        appointments = queryset.order_by("-date", "-time")
        serializer = AppointmentSerializer(appointments, many=True)
        data = serializer.data
        return Response(
            {
                "status": "success",
                "appointment": data,
            },
            status=status.HTTP_200_OK,
        )


class DoctorAppointmentStatusUpdateAPIView(APIView):
    """
    Doctors can:
    - PATCH: Update status of an appointment (approve/decline/cancel/complete)
    """

    permission_classes = [permissions.IsAuthenticated, IsActivated, IsDoctor]

    @swagger_auto_schema(
        tags=["Appointments"],
        request_body=AppointmentStatusUpdateSerializer,
        operation_description="Update appointment status (approve/decline/cancel/complete)",
    )
    def patch(self, request, appointment_id):
        try:
            appointment = Appointment.objects.get(
                appointment_id=appointment_id, doctor=request.user.doctor
            )
        except Appointment.DoesNotExist:
            return Response(
                {"error": "Appointment not found or not assigned to you"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AppointmentStatusUpdateSerializer(
            appointment, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"status": "success", "message": "Appointment status updated"},
            status=status.HTTP_200_OK,
        )


class HospitalAppointmentListAPIView(APIView):
    """
    Hospitals can:
    - GET: View all appointments across their hospital
    """

    permission_classes = [permissions.IsAuthenticated, IsActivated, IsHospital]

    @swagger_auto_schema(
        tags=["Appointments"],
        responses={200: AppointmentSerializer(many=True)},
        operation_summary="List Hospital Appointments",
    )
    def get(self, request):
        hospital = (
            request.user.hospital
        )  # assuming User with type "hospital" has a OneToOne with Hospital

        queryset = Appointment.objects.filter(hospital=hospital)

        # optional filter by status
        status_param = request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param.lower())

        appointments = queryset.order_by("-date", "-time")
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(
            {"status": "success", "appointment": serializer.data},
            status=status.HTTP_200_OK,
        )
    

class PatientAppointmentRescheduleAPIView(APIView):
    """
    Doctor and Patient can:
    - PATCH: Reschedule their appointment (if doctor is available)
    """

    permission_classes = [permissions.IsAuthenticated, IsActivated, (IsDoctor or IsPatient)]

    @swagger_auto_schema(
        tags=["Appointments"],
        request_body=AppointmentRescheduleSerializer,
        operation_summary="Reschedule Appointment (Doctor/Patient)",
    )
    def patch(self, request, appointment_id):
        try:
            appointment = Appointment.objects.get(
                appointment_id=appointment_id
            )
        except Appointment.DoesNotExist:
            return Response(
                {"error": "Appointment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AppointmentRescheduleSerializer(
            appointment, data=request.data, partial=False, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"status": "success", "message": "Appointment rescheduled successfully"},
            status=status.HTTP_200_OK,
        )
