import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PrescriptionDrug

logger = logging.getLogger(__name__)

@receiver(post_save, sender=PrescriptionDrug)
def generate_logs_on_drug_create(sender, instance, created, **kwargs):
    if created:  # Only run when doctor first creates the drug
        logger.info(f"Generating schedule for  {instance.drug_id}")
        instance.generate_schedule()