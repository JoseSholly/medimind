from django.contrib.auth.models import Group, Permission, AbstractUser

from django.db import models
from hospitals.models import Hospital

class User(AbstractUser):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    is_doctor = models.BooleanField(default=False)
    is_patient = models.BooleanField(default=False)


    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_set',  # unique related name to avoid clashes
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_set',  # unique related name to avoid clashes
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)
    license_number = models.CharField(max_length=100)

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10)
    medical_history = models.TextField(blank=True)
    assigned_doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, related_name='patients')
