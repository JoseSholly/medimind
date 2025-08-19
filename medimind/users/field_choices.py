from django.utils.translation import gettext as _

GENDER = [
    ("male", _("Male")),
    ("female", _("Female"))
]

SPECIALIZATION_CHOICES = (
    # Primary Care & General Medicine
    ('family_medicine', _('Family Medicine')),
    ('internal_medicine', _('Internal Medicine')),
    ('pediatrics', _('Pediatrics')),
    ('geriatrics', _('Geriatrics')),

    # Surgical Specialties
    ('general_surgery', _('General Surgery')),
    ('orthopedic_surgery', _('Orthopedic Surgery')),
    ('neurosurgery', _('Neurosurgery')),
    ('cardiothoracic_surgery', _('Cardiothoracic Surgery')),
    ('plastic_surgery', _('Plastic Surgery')),
    ('urology', _('Urology')),
    ('otolaryngology_ent', _('Otolaryngology (ENT)')),
    ('ophthalmology', _('Ophthalmology')),
    ('colon_rectal_surgery', _('Colon and Rectal Surgery')),

    # Internal Medicine Subspecialties
    ('cardiology', _('Cardiology')),
    ('dermatology', _('Dermatology')),
    ('endocrinology', _('Endocrinology')),
    ('gastroenterology', _('Gastroenterology')),
    ('infectious_disease', _('Infectious Disease')),
    ('nephrology', _('Nephrology')),
    ('pulmonology', _('Pulmonology')),
    ('rheumatology', _('Rheumatology')),
    ('hematology', _('Hematology')),
    ('oncology', _('Oncology')),

    # Diagnostic & Support Specialties
    ('anesthesiology', _('Anesthesiology')),
    ('pathology', _('Pathology')),
    ('radiology', _('Radiology')),
    ('emergency_medicine', _('Emergency Medicine')),
    ('physical_medicine_rehabilitation', _('Physical Medicine and Rehabilitation')),

    # Other Specialties
    ('allergy_immunology', _('Allergy and Immunology')),
    ('neurology', _('Neurology')),
    ('obstetrics_gynecology', _('Obstetrics and Gynecology')),
    ('psychiatry', _('Psychiatry')),
)