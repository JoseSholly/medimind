import random

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker
from users.field_choices import SPECIALIZATION_CHOICES

fake = Faker()

User = get_user_model()
Doctor = apps.get_model(app_label="users", model_name="Doctor")
Patient = apps.get_model(app_label="users", model_name="Patient")
Hospital = apps.get_model(app_label="hospitals", model_name="Hospital")


class Command(BaseCommand):
    help = "Seed the database with 5 hospitals, 3 doctors each, and 3 patients per doctor."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Seeding hospitals, doctors, and patients..."))

        specialization_keys = [spec[0] for spec in SPECIALIZATION_CHOICES]

        for _ in range(5):  # Create 5 hospitals
            # 1. Create hospital user
            hospital_user = User.objects.create_user(
                email=fake.unique.email(),
                password="password123",
                user_type="hospital",
                is_active=True,
                is_activated=True,
            )

            # 2. Create Hospital profile
            hospital = Hospital.objects.create(
                hospital_id=None,  # auto-generated
                name=fake.unique.company() + " Hospital",
                description=fake.text(max_nb_chars=200),
                address=fake.address(),
                contact_email=hospital_user.email,
                website_link=fake.url(),
                user=hospital_user,   # <--- FK to User
            )

            self.stdout.write(self.style.SUCCESS(f"🏥 Created hospital: {hospital.name} ({hospital.hospital_id})"))

            # 3. Add doctors to hospital
            for _ in range(3):
                first_name = fake.first_name()
                last_name = fake.last_name()
                email = f"{first_name.lower()}.{last_name.lower()}@gmail.com"

                doctor_user = User.objects.create_user(
                    email=email,
                    password="password123",
                    first_name=first_name,
                    last_name=last_name,
                    user_type="doctor",
                    is_active=True,
                    is_activated=True,
                )

                # Pick random specializations (at least 2)
                specializations = random.sample(specialization_keys, k=random.randint(2, 4))

                doctor = Doctor.objects.create(
                    user=doctor_user,
                    hospital=hospital,
                    specialization=specializations,
                    license_number=fake.unique.bothify(text="LIC-#######"),
                )

                self.stdout.write(
                    self.style.NOTICE(f"  ➕ Doctor: {doctor.user.get_full_name()} ({', '.join(specializations)})")
                )

                # 4. Add patients for doctor
                for _ in range(3):
                    first_name = fake.first_name()
                    last_name = fake.last_name()
                    email = f"{first_name.lower()}.{last_name.lower()}@gmail.com"

                    patient_user = User.objects.create_user(
                        email=email,
                        password="password123",
                        first_name=first_name,
                        last_name=last_name,
                        user_type="patient",
                        is_active=True,
                        is_activated=True,
                    )

                    patient = Patient.objects.create(
                        user=patient_user,
                        hospital=hospital,
                        assigned_doctor=doctor,
                        medical_history=fake.text(max_nb_chars=200),
                    )

                    self.stdout.write(
                        self.style.NOTICE(f"    👤 Patient: {patient.user.get_full_name()}")
                    )

        self.stdout.write(self.style.SUCCESS("✅ Seeding complete!"))
