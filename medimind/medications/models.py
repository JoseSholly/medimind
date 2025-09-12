from datetime import time, timedelta

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from users.mixins import TimestampMixin
from users.models import Doctor, Patient

from .id_generator import generate_drug_id, generate_log_id, generate_prescription_id


class Prescription(TimestampMixin, models.Model):
    prescription_id = models.CharField(
        max_length=15,
        unique=True,
        editable=False,
        blank=True,
        null=True,
        db_index=True,
        default=generate_prescription_id,
        help_text=_("Unique prescription ID in format PRE-XXXXXXXX"),
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="prescriptions",
        help_text=_("The doctor who issued this prescription."),
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="prescriptions",
        help_text=_("The patient who receives this prescription."),
    )
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Prescription"
        verbose_name_plural = "Prescriptions"
        indexes = [
            models.Index(fields=["prescription_id"]),
            models.Index(fields=["doctor", "patient"]),
        ]

    def __str__(self):
        return f"Prescription for {self.patient.user.get_full_name()} by Dr. {self.doctor.user.get_full_name()}"


class PrescriptionDrug(TimestampMixin, models.Model):
    drug_id = models.CharField(
        max_length=15,
        unique=True,
        editable=False,
        blank=True,
        null=True,
        db_index=True,
        default=generate_drug_id,
        help_text=_("Unique drug ID in format DRG-XXXXXXXX"),
    )
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name="drugs",
        help_text=_("The prescription this drug belongs to."),
    )
    drug_name = models.CharField(
        max_length=255, help_text=_("Free text drug name written by doctor.")
    )
    dosage_instruction = models.TextField(
        help_text=_("Dosage instructions, e.g., '2 tablets after meal'.")
    )
    frequency_per_day = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text=_("How many times a day this drug should be taken.")
    )
    duration_days = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text=_("How many days the drug should be taken.")
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Prescription Drug"
        verbose_name_plural = "Prescription Drugs"
        indexes = [
            models.Index(fields=["prescription", "drug_name"]),
        ]

    def __str__(self):
        return f"{self.drug_name} ({self.prescription.patient.user.get_full_name()})"

    def get_end_date(self):
        """
        Calculate the end date of this drug’s prescription based on
        the prescription start_date and duration_days.
        End date is inclusive (last day patient should take the drug).
        """
        if not self.prescription.start_date:
            return None
        return self.prescription.start_date + timedelta(days=self.duration_days - 1)

    @property
    def get_status(self):
        """
        Determine if this prescription drug is pending, active, or done
        based on start_date (from Prescription) and duration_days.
        """
        if not self.prescription.start_date:
            return "invalid"  # No start date → cannot determine
        

        if not isinstance(self.duration_days, int) or self.duration_days <= 0:
            return "invalid"  # Invalid duration_days

        today = timezone.localdate()
        start_date = self.prescription.start_date
        end_date = start_date + timedelta(days=self.duration_days)

        if today < start_date:
            return "pending"
        elif start_date <= today < end_date:
            return "active"
        else:
            return "done"

    def generate_schedule(self, strict=False):
        """
        Generate prescription logs automatically based on frequency and duration.

        Modes:
        - Default: start at 8 AM baseline, spread across waking hours.
        - Strict: spread evenly across 24 hours (e.g. every 8h for 3x/day).
        """
        logs = []
        if not self.prescription.start_date:
            raise ValueError("Prescription start_date cannot be None")
        if self.frequency_per_day <= 0:
            raise ValueError("Frequency per day must be positive")

        start_date = self.prescription.start_date

        # Determine base interval
        if strict:
            interval_hours = 24 / self.frequency_per_day
            first_dose_time = time(0, 0)  # midnight start
        else:
            # Default: baseline 8 AM
            first_dose_time = time(8, 0)
            if self.frequency_per_day == 1:
                interval_hours = 0  # single dose, always at 8 AM
            else:
                # Spread doses until bedtime (~8 PM latest)
                interval_hours = 12 / (self.frequency_per_day - 1)

        for day in range(self.duration_days):
            current_date = start_date + timedelta(days=day)

            for i in range(self.frequency_per_day):
                # Scheduled time = baseline + interval
                scheduled_dt = timezone.datetime.combine(
                    current_date, first_dose_time
                ) + timedelta(hours=i * interval_hours)
                logs.append(
                    PrescriptionLog(
                        prescription_drug=self,
                        date=current_date,
                        scheduled_time=scheduled_dt.time(),
                    )
                )

        PrescriptionLog.objects.bulk_create(logs)

    def get_daily_times(self, strict=False):
        """
        Return a list of times (as strings HH:MM) representing
        when this drug is scheduled to be taken each day.

        Modes:
        - Default: start at 8 AM baseline, spread across waking hours.
        - Strict: spread evenly across 24 hours (e.g., every 8h for 3x/day).
        """
        if self.frequency_per_day <= 0:
            return []

        # Strict mode → evenly across 24h starting at midnight
        if strict:
            interval_hours = 24 / self.frequency_per_day
            first_dose_time = time(0, 0)
        else:
            # Default → start at 8 AM
            first_dose_time = time(8, 0)
            if self.frequency_per_day == 1:
                interval_hours = 0
            else:
                interval_hours = 12 / (self.frequency_per_day - 1)

        times = []
        for i in range(self.frequency_per_day):
            scheduled_dt = timezone.datetime.combine(
                timezone.localdate(), first_dose_time
            ) + timedelta(hours=i * interval_hours)
            times.append(scheduled_dt.time().strftime("%H:%M"))

        return times


class PrescriptionLog(TimestampMixin, models.Model):
    
    log_id = models.CharField(
        max_length=15,
        unique=True,
        editable=False,
        blank=True,
        null=True,
        db_index=True,
        default=generate_log_id,
        help_text=_("Unique log ID in format LOG-XXXXXXXX"),
    )
    prescription_drug = models.ForeignKey(
        PrescriptionDrug,
        on_delete=models.CASCADE,
        related_name="logs",
        help_text=_("The drug schedule this log belongs to."),
    )
    date = models.DateField(help_text=_("The date this dose was scheduled."))
    scheduled_time = models.TimeField(help_text=_("Expected time for this dose."))
    taken = models.BooleanField(
        default=False, help_text=_("Whether patient took this dose.")
    )
    taken_at = models.DateTimeField(
        null=True, blank=True, help_text=_("Timestamp when patient marked as taken.")
    )

    def __str__(self):
        status = "taken" if self.taken else "Not Taken"
        return f"{self.prescription_drug.drug_name} - {self.date} ({status})"

    def get_status(self):
        if not self.date or not self.scheduled_time:
            raise ValueError("Invalid log: date and scheduled_time required.")

        # Current timezone-aware datetime
        now = timezone.localtime(timezone.now())
        scheduled_dt = timezone.make_aware(
            timezone.datetime.combine(self.date, self.scheduled_time)
        )

        if self.taken:
            return "taken"

        # Too early (before scheduled time)
        if now < scheduled_dt:
            return "pending"

        # Within 1-hour grace period → "ready"
        if scheduled_dt <= now <= scheduled_dt + timezone.timedelta(hours=2):
            return "due"

        # Beyond 1-hour grace → missed
        return "missed"
