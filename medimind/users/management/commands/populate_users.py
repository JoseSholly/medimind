import random

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker
from users.field_choices import SPECIALIZATION_CHOICES

fake = Faker()
User = get_user_model()
Doctor  = apps.get_model(model_name="Doctor", app_label="users")
Patient = apps.get_model(model_name="Patient", app_label="users")
Hospital = apps.get_model(model_name="Hospital", app_label="hospitals")


class Command(BaseCommand):
    help = "Seed the database with 5 hospitals, 3 doctors each, and 3 patients per doctor."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Seeding hospitals, doctors, and patients..."))

        # Clear old data (optional - be careful in production)
        # Hospital.objects.all().delete()
        # User.objects.all().delete()
        # Doctor.objects.all().delete()
        # Patient.objects.all().delete()

        specialization_keys = [spec[0] for spec in SPECIALIZATION_CHOICES]

        for _ in range(5):  # Create 5 hospitals
            hospital = Hospital.objects.create(
                name=fake.unique.company() + " Hospital",
                description=fake.text(max_nb_chars=200),
                address=fake.address(),
                contact_email=fake.unique.email(),
                website_link=fake.url()
            )
            self.stdout.write(self.style.SUCCESS(f"Created hospital: {hospital.name} ({hospital.hospital_id})"))

            for _ in range(3):  # 3 doctors per hospital
                first_name = fake.first_name()
                last_name = fake.last_name()
                email = f"{first_name}{last_name}@gmail.com"

                doctor_user = User.objects.create(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    hospital=hospital,
                    is_active=True
                )
                doctor_user.set_password("password123")
                doctor_user.save()

                # Pick at least 2 random specializations
                specializations = random.sample(specialization_keys, k=random.randint(2, 4))

                doctor = Doctor.objects.create(
                    user=doctor_user,
                    specialization=specializations,
                    license_number=fake.unique.bothify(text="LIC-#######")
                )
                self.stdout.write(
                    self.style.NOTICE(f"  Added doctor: {doctor.user.get_full_name()} - {specializations}")
                )

                for _ in range(3):  # 3 patients per doctor
                    first_name = fake.first_name()
                    last_name = fake.last_name()
                    email = f"{first_name}{last_name}@gmail.com"
                    patient_user = User.objects.create(
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        hospital=hospital,
                        is_active=True
                    )
                    patient_user.set_password("password123")
                    patient_user.save()

                    patient = Patient.objects.create(
                        user=patient_user,
                        assigned_doctor=doctor,
                        medical_history=fake.text(max_nb_chars=200)
                    )
                    self.stdout.write(
                        self.style.NOTICE(f"    Added patient: {patient.user.get_full_name()}")
                    )

        self.stdout.write(self.style.SUCCESS("✅ Seeding complete!"))
