from django.db import models
from medications.models import Prescription


class MedicationLog(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE)
    taken_at = models.DateTimeField(null=True, blank=True)
    missed = models.BooleanField(default=False)
    notified_doctor = models.BooleanField(default=False)
