from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Doctor, Patient

User = get_user_model()


@receiver(pre_save, sender=Doctor)
def set_doctor_hospital(sender, instance, **kwargs):
    """
    Ensure doctor is always tied to a hospital
    and user_type is enforced as 'doctor'.
    """
    if not instance.user_id:
        raise ValidationError("Doctor must be linked to a user.")

    # Enforce correct user type
    instance.user.user_type = "doctor"

    # If hospital not set explicitly, try to infer from user's hospital profile
    if not instance.hospital_id and hasattr(instance.user, "hospital_profile"):
        instance.hospital = instance.user.hospital_profile


@receiver(pre_save, sender=Patient)
def set_patient_hospital(sender, instance, **kwargs):
    """
    Ensure patient is always tied to a hospital
    and user_type is enforced as 'patient'.
    """
    if not instance.user_id:
        raise ValidationError("Patient must be linked to a user.")

    # Enforce correct user type
    instance.user.user_type = "patient"

    # If hospital not set explicitly, try to infer from user's hospital profile
    if not instance.hospital_id and hasattr(instance.user, "hospital_profile"):
        instance.hospital = instance.user.hospital_profile

    # Ensure assigned doctor is from the same hospital
    if instance.assigned_doctor_id and instance.assigned_doctor.hospital_id != instance.hospital_id:
        raise ValidationError("Assigned doctor must belong to the same hospital as the patient.")
