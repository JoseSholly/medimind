from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from .field_choices import GENDER, SPECIALIZATION_CHOICES


def validate_choices(valid_choices, choices):
    choices = [choice[0] for choice in choices]
    for choice in valid_choices:
        if choice not in choices:
            raise ValidationError(
                _(f"{choice} is not a valid choice. Valid choices: {choices}"),
            )


def validate_specialization(choices):
    valid_choices = [choice for choice in choices]
    validate_choices(valid_choices=valid_choices, choices=SPECIALIZATION_CHOICES)

def validate_gender(value):
    choices = [choice[0] for choice in GENDER]
    if value not in choices:
        raise ValidationError(
                _(f"{value} is not a valid choice."),
            )
    return value
    