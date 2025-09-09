from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PrescriptionDrug


@receiver(post_save, sender=PrescriptionDrug)
def generate_logs_on_drug_create(sender, instance, created, **kwargs):
    if created:  # Only run when doctor first creates the drug
        instance.generate_schedule()
