from django.urls import path

from .views import (
    DoctorAppointmentListAPIView,
    DoctorAppointmentStatusUpdateAPIView,
    HospitalAppointmentListAPIView,
    PatientAppointmentListCreateAPIView,
    PatientAppointmentRescheduleAPIView,
)

urlpatterns = [
    # Patient endpoints
    path(
        "v1/patient/appointments/",
        PatientAppointmentListCreateAPIView.as_view(),
        name="patient-appointments",
    ),
    # Doctor endpoints
    path(
        "v1/doctor/appointments/",
        DoctorAppointmentListAPIView.as_view(),
        name="doctor-appointments",
    ),
    path(
        "v1/doctor/appointments/<str:appointment_id>/update-status/",
        DoctorAppointmentStatusUpdateAPIView.as_view(),
        name="doctor-appointment-update-status",
    ),
    path(
        "v1/patient/appointments/<str:appointment_id>/reschedule/",
        PatientAppointmentRescheduleAPIView.as_view(),
        name="appointment-reschedule",
    ),
    # Hospital endpoints
    path(
        "v1/hospital/appointments/",
        HospitalAppointmentListAPIView.as_view(),
        name="hospital-appointments",
    ),
]
