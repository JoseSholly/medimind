from django.db import models
from users.models import Doctor, Patient

class Medication(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    dosage = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

class Prescription(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class PrescriptionSchedule(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='schedules')
    time_of_day = models.TimeField()
