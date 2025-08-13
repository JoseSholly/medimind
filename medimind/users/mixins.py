from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _


class TimestampMixin(models.Model):
    created_at = models.DateTimeField(
        default=now,
        editable=False,
        help_text=_("Time created"),
    )
    updated_at = models.DateTimeField(auto_now=True, help_text=_("Last time updated"))

    class Meta:
        abstract = True        