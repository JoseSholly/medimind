import uuid

from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from .field_choices import GENDER, SPECIALIZATION_CHOICES
from .managers import CustomUserManager, OTPManager, TenantAwareManager, SessionTokenManager
from .mixins import TimestampMixin
from .password_generator import IDGenerator
from .validators import validate_gender, validate_specialization

USER_TYPES = (
        ("patient", _("Patient")),
        ("doctor", _("Doctor")),
        ("hospital", _("Hospital")),
        ("admin", _("Admin")),
    )

PURPOSE_CHOICES = (
        ("email_verification", "Email Verification"),
        ("password_reset", "Password Reset"),
        ("2fa", "Two-Factor Authentication"),
    )
class User(AbstractBaseUser, PermissionsMixin):
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPES,
        default="patient",
        help_text=_("Defines whether this user is a patient, doctor, or hospital."),
    )
    username = None
    email = models.EmailField(unique=True)
    user_id = models.UUIDField(
        default = uuid.uuid4,
        editable = False)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True, choices=GENDER, validators=[validate_gender])
    
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

    class Meta:
        indexes = [
            models.Index(fields=['user_id']),
        ]

    def __str__(self):
        return f"{self.email.split('@')[0]}"

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
    hospital = models.ForeignKey(
        "hospitals.Hospital",
        on_delete=models.CASCADE,
        related_name='doctors',
        null=True,
        blank=True,
        verbose_name=_("Hospital"),
        help_text=_("The hospital this doctor belongs to.")
    )
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
    specialization = ArrayField(
        models.CharField(max_length=100,choices=SPECIALIZATION_CHOICES, ),
        blank=True, default=list,
        help_text=_("List of specializations for the doctor. Use field choices from field_choices.py."), 
        validators=[validate_specialization]
    )
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
        return f"Dr. {self.user.get_full_name()} -- {self.hospital}"

    def clean(self):
        super().clean()

        if not self.user_id:
            raise ValidationError(_("Doctor must be linked to a user."))

        if not self.hospital_id:
            raise ValidationError(_("Doctor must belong to a hospital."))

    
    def save(self, *args, **kwargs):

        self.user.user_type = "doctor"
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
    hospital = models.ForeignKey(
        "hospitals.Hospital",
        on_delete=models.CASCADE,
        related_name='hosiptal_patient',
        null=True,
        blank=True,
        verbose_name=_("Hospital"),
        help_text=_("The hospital this doctor belongs to.")
    )
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
        return f"Patient: {self.user.get_full_name()}--{self.hospital or '—'})"
    
    def get_full_name(self):
        return self.user.get_full_name()
    
    def clean(self):
        super().clean()

        if not self.user_id:
            raise ValidationError(_("Patient must be linked to a user."))

        if not self.hospital_id:
            raise ValidationError(_("Patient must belong to a hospital."))

        # If assigned doctor exists, enforce same hospital
        if self.assigned_doctor_id and self.assigned_doctor.hospital_id != self.hospital_id:
            raise ValidationError(_("Assigned doctor must belong to the same hospital as the patient."))

    def save(self, *args, **kwargs):
        self.user.user_type = "patient"
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



class OTP(models.Model):
    

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPES,
        default="patient",
        help_text=_("Defines whether this user is a patient, doctor, or hospital."),
    )
    code = models.CharField(max_length=128)  # store hashed OTP
    purpose = models.CharField(max_length=50, choices=PURPOSE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = OTPManager()

    class Meta:
        indexes = [
            models.Index(fields=["user", "purpose"]),
        ]
        verbose_name = "OTP"

    def is_expired(self, validity_minutes=10):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=validity_minutes)

    def verify_otp(self, raw_code):
        """
        Verify OTP by checking hashed code.
        """
        return check_password(raw_code, self.code)

    def __str__(self):
        return f"OTP for {self.user.email} ({self.purpose})"


class SessionToken(TimestampMixin, models.Model):
    """
    Stores a temporary session token that authorizes user.
    This token is single-use and time-limited.
    """
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    token = models.UUIDField(
        default = uuid.uuid1,
        editable = False,
        unique=True)
    purpose = models.CharField(max_length=50, choices=PURPOSE_CHOICES)
    expires_at = models.DateTimeField(default=None)
    is_used = models.BooleanField(default=False)

    objects = SessionTokenManager()

    def is_valid(self):
        """Checks if the session token is still valid (not expired and not yet used)."""
        return not self.is_used and self.expires_at > timezone.now()
    
    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Session for {self.user.email} - {str(self.token)[:10]}..."