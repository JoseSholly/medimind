from django.db import IntegrityError, models, transaction
from django.utils.translation import gettext as _
from users.mixins import TimestampMixin
from users.password_generator import IDGenerator


class Hospital(TimestampMixin, models.Model):
    hospital_id = models.CharField(
        max_length=14,  # HOSP- (5) + ID_LENGTH (8) + buffer (1)
        unique=True,
        editable=False,
        null=True,
        blank=True,
        help_text=_("Unique hospital ID in format HOSP-XXXXXXXX")
    )

    name = models.CharField(max_length=255, unique=True, help_text=_("Name of the hospital."))
    description = models.TextField(max_length=2000, null=True, blank=True, help_text=_("Description of the hospital."))
    address = models.TextField(max_length=255, null=True, blank=True, help_text=_("Address of the hospital."))
    contact_email = models.EmailField(max_length=100, help_text=_("Contact email of the hospital."))
    website_link = models.URLField(max_length=200, null=True, blank=True, help_text=_("Website link of the hospital."))
    

    def __str__(self):
        return self.name
    
    @transaction.atomic
    def save(self, *args, **kwargs):
        if not self.hospital_id:
            max_attempts = 10
            for _ in range(max_attempts):
                self.hospital_id = IDGenerator.hospital_id()
                try:
                    # force_insert=True tells Django to always create a new record
                    super().save(*args, **kwargs)
                    return # Exit the function on success
                except IntegrityError:
                    # If ID already exists, the loop continues to try a new ID
                    continue
            # If the loop finishes without success, raise an error
            raise ValueError("Could not generate unique Hospital ID after maximum attempts")
        
        # If the ID already exists, proceed with a standard save (update)
        super().save(*args, **kwargs)       