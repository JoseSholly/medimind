# appointments/models.py
import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from hospitals.models import Hospital
from users.models import Doctor, Patient


class AppointmentStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    APPROVED = "approved", _("Approved")
    DECLINED = "declined", _("Declined")
    CANCELLED = "cancelled", _("Cancelled")
    COMPLETED = "completed", _("Completed")


class Appointment(models.Model):
    appointment_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
        help_text=_("Unique appointment identifier"),
    )

    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.CASCADE,
        related_name="appointments",
        help_text=_("Hospital where this appointment is booked."),
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="appointments",
        help_text=_("Doctor requested for this appointment."),
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="appointments",
        help_text=_("Patient who booked this appointment."),
    )

    date = models.DateField(help_text=_("Requested appointment date"))
    time = models.TimeField(help_text=_("Requested appointment time"))

    reason = models.TextField(
        blank=True,
        help_text=_("Optional reason or note for the appointment."),
    )

    status = models.CharField(
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.PENDING,
        help_text=_("Status of the appointment."),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "time"]

    def __str__(self):
        return f"{self.patient.user.get_full_name()} → {self.doctor.user.get_full_name()} on {self.date} at {self.time}"
