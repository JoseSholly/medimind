from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from hospitals.models import Hospital
from users.models import Doctor, Patient


class Medication(models.Model):
    hospital = models.ForeignKey(
        Hospital, on_delete=models.CASCADE, related_name="medications"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    dosage = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("hospital", "name")  # Medication name unique per hospital

    def __str__(self):
        return self.name


class Prescription(models.Model):
    hospital = models.ForeignKey(
        Hospital, on_delete=models.CASCADE, related_name="prescriptions"
    )
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="prescriptions")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="prescriptions")
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name="prescriptions")

    start_date = models.DateField()
    end_date = models.DateField()
    instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_date"]

    def clean(self):
        # Hospital consistency enforcement
        if self.doctor.user.hospital_id != self.hospital_id:
            raise ValidationError("Doctor's hospital must match prescription hospital.")
        if self.patient.user.hospital_id != self.hospital_id:
            raise ValidationError("Patient's hospital must match prescription hospital.")
        if self.medication.hospital_id != self.hospital_id:
            raise ValidationError("Medication's hospital must match prescription hospital.")

    def __str__(self):
        return f"{self.medication.name} for {self.patient.user.get_full_name()}"

    def get_next_dose_datetime(self):
        """
        Returns the next scheduled dose datetime for this prescription from now.
        """
        now = timezone.localtime()
        today = now.date()

        if self.end_date and today > self.end_date:
            return None

        # Check today's remaining schedules
        schedules_today = self.schedules.all().order_by("time_of_day")
        for schedule in schedules_today:
            dose_dt = timezone.make_aware(datetime.combine(today, schedule.time_of_day))
            if dose_dt > now:
                return dose_dt

        # Move to next day if no more doses today
        next_day = today + timedelta(days=1)
        if not self.end_date or next_day <= self.end_date:
            first_time = schedules_today.first()
            if first_time:
                return timezone.make_aware(datetime.combine(next_day, first_time.time_of_day))

        return None


class PrescriptionSchedule(models.Model):
    prescription = models.ForeignKey(
        Prescription, on_delete=models.CASCADE, related_name="schedules"
    )
    time_of_day = models.TimeField()

    class Meta:
        ordering = ["time_of_day"]

    def __str__(self):
        return f"{self.prescription} at {self.time_of_day.strftime('%H:%M')}"
