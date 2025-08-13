from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _
from hospitals.models import Hospital

from .field_choices import GENDER
from .managers import CustomUserManager, TenantAwareManager


class User(AbstractBaseUser, PermissionsMixin):
    username = None  # remove the username field
    email = models.EmailField(unique=True)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, null=True, blank=True, related_name='hospital_users')

    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_activated = models.BooleanField(default=False, help_text=_("Indicates whether the user has activated their account."))

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name or self.email.split('@')[0]
    
    @property
    def is_doctor(self):
        return hasattr(self, 'doctor')

    @property
    def is_patient(self):
        return hasattr(self, 'patient')


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor')
    specialization = models.CharField(max_length=100, help_text=_("Specialization of the doctor."))
    license_number = models.CharField(max_length=100, unique=True, help_text=_("Unique license number of the doctor."))
    age = models.PositiveIntegerField(null=True, blank=True) 
    gender = models.CharField(max_length=10, blank=True, choices=GENDER) 

    objects = TenantAwareManager()

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.specialization}"
    
    

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient')
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER, blank=True)
    medical_history = models.TextField(blank=True)
    assigned_doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, related_name='patients', help_text=_("Doctor assigned to this patient."))

    objects = TenantAwareManager()
