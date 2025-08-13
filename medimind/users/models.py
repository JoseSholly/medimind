from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.utils import timezone
from django.utils.translation import gettext as _
from hospitals.models import Hospital

from .field_choices import GENDER
from .managers import CustomUserManager, TenantAwareManager
from .mixins import TimestampMixin
from .password_generator import IDGenerator


class User(AbstractBaseUser, PermissionsMixin):
    username = None
    email = models.EmailField(unique=True)
    hospital = models.ForeignKey(
        Hospital, on_delete=models.CASCADE, null=True, blank=True,
        related_name='hospital_users'
    )
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True, choices=GENDER)
    
    date_joined = models.DateTimeField(default=timezone.now)
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    is_activated = models.BooleanField(
        default=False,
        help_text=_("Indicates whether the user has activated their account.")
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name or (self.email.split('@')[0] if self.email else "")

    @property
    def is_doctor(self):
        return hasattr(self, 'doctor')

    @property
    def is_patient(self):
        return hasattr(self, 'patient')

class Doctor(TimestampMixin, models.Model):
    doctor_id = models.CharField(
        max_length=13,  # e.g. DOC-XXXXXXXX
        unique=True,
        editable=False,
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Unique doctor ID in format DOC-XXXXXXXX")
    )
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='doctor'
    )
    specialization = models.CharField(max_length=100, help_text=_("Specialization of the doctor."))
    license_number = models.CharField(
        max_length=100, unique=True,
        help_text=_("Unique license number of the doctor.")
    )

    objects = TenantAwareManager()

    class Meta:
        indexes = [
            models.Index(fields=['license_number']),
            models.Index(fields=['doctor_id']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.specialization}"

    def clean(self):
        super().clean()

        if not self.user_id:
            raise ValidationError(_("Doctor must be linked to a user."))

        # Enforce that a doctor’s user has a hospital (for strict multi-tenancy)
        if not self.user.hospital_id:
            raise ValidationError(_("Doctor's user must belong to a hospital."))

    
    def save(self, *args, **kwargs):
        # Run model validation first (also runs field validators)
        self.full_clean()

        # If we're just updating (PK exists), normal atomic save is enough.
        if self.pk and self.doctor_id:
            with transaction.atomic():
                return super().save(*args, **kwargs)

        # New object or object missing doctor_id -> generate with retry
        MAX_ATTEMPTS = 10
        for attempt in range(1, MAX_ATTEMPTS + 1):
            if not self.doctor_id:
                self.doctor_id = IDGenerator.doctor_id()

            try:
                with transaction.atomic():
                    return super().save(*args, **kwargs)
            except IntegrityError as e:
                # If collision is on doctor_id, retry with a new one; otherwise re-raise
                # (DB error messages vary; check both field names)
                msg = str(e).lower()
                collided_id = 'doctor_id' in msg
                collided_license = 'license' in msg and 'unique' in msg
                if collided_id and attempt < MAX_ATTEMPTS:
                    # regenerate and retry
                    self.doctor_id = None
                    continue
                # If license_number collided, surface clearly
                if collided_license:
                    raise ValidationError(_("License number already exists.")) from e
                # Unknown integrity issue
                raise



class Patient(TimestampMixin, models.Model):
    patient_id = models.CharField(
        max_length=13,  # e.g. PAT-XXXXXXXX
        unique=True,
        editable=False,
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Unique patient ID in format PAT-XXXXXXXX")
    )
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='patient'
    )
    medical_history = models.TextField(blank=True)
    assigned_doctor = models.ForeignKey(
        Doctor, on_delete=models.SET_NULL, null=True, blank=False,
        related_name='patients',
        help_text=_("Doctor assigned to this patient.")
    )

    objects = TenantAwareManager()

    class Meta:
        indexes = [
            models.Index(fields=['patient_id']),
        ]

    def __str__(self):
        
        return f"Patient: {self.user.get_full_name()} (ID: {self.patient_id or '—'})"

    
    def clean(self):
        super().clean()

        if not self.user_id:
            raise ValidationError(_("Patient must be linked to a user."))

        # Enforce that a patient's user has a hospital (for strict multi-tenancy)
        if not self.user.hospital_id:
            raise ValidationError(_("Patient's user must belong to a hospital."))

        # If assigned_doctor present, they must be from same hospital
        if self.assigned_doctor_id:
            doc_hospital_id = self.assigned_doctor.user.hospital_id
            if doc_hospital_id != self.user.hospital_id:
                raise ValidationError(
                    _("Assigned doctor must belong to the same hospital as the patient.")
                )

    def save(self, *args, **kwargs):
        # Run validations first
        self.full_clean()

        # Updates with existing patient_id: simple atomic save
        if self.pk and self.patient_id:
            with transaction.atomic():
                return super().save(*args, **kwargs)

        # New object or missing patient_id -> generate with retry
        MAX_ATTEMPTS = 10
        for attempt in range(1, MAX_ATTEMPTS + 1):
            if not self.patient_id:
                self.patient_id = IDGenerator.patient_id()

            try:
                with transaction.atomic():
                    return super().save(*args, **kwargs)
            except IntegrityError as e:
                msg = str(e).lower()
                collided_id = 'patient_id' in msg
                if collided_id and attempt < MAX_ATTEMPTS:
                    # regenerate and retry
                    self.patient_id = None
                    continue
                # Unknown integrity issue
                raise
