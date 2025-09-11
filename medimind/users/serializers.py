import re

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import EmailValidator
from django.db import IntegrityError
from hospitals.models import Hospital
from medications.models import PrescriptionDrug, PrescriptionLog
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .exceptions import ExistingHospitalError, ExistingLicenseError, ExistingUserError
from .field_choices import GENDER, SPECIALIZATION_CHOICES
from .models import OTP, Doctor, Patient, SessionToken
from .validators import validate_email_address

User = get_user_model()


class BaseRegistrationSerializer(serializers.ModelSerializer):
    """
    Base serializer for user registration.
    Subclasses must define `user_type`.
    """

    email = serializers.CharField(max_length=254, required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        min_length=8,
        max_length=70,
    )

    class Meta:
        model = User
        fields = ["email", "password"]

    # Each child serializer should set this
    user_type = None

    def validate_email(self, value):
        """Check if email address is valid."""
        try:
            validate_email_address(value)
        except serializers.ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate(self, data):
        """Perform additional object-level validation if needed."""
        return data

    def create(self, validated_data):
        """Create and return a new user instance with the correct user_type."""
        if not self.user_type:
            raise ValueError("user_type must be set in the subclass.")

        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            user_type=self.user_type,
            is_activated=False,
        )
        return user

    def to_internal_value(self, data):
        """Process incoming data without custom error formatting."""
        return super().to_internal_value(data)

    def to_representation(self, instance):
        """Format successful responses without interfering with errors."""
        return super().to_representation(instance)


# --- Specialized Serializers ---


class PatientRegistrationSerializer(BaseRegistrationSerializer):
    user_type = "patient"


class DoctorRegistrationSerializer(BaseRegistrationSerializer):
    user_type = "doctor"


class HospitalRegistrationSerializer(BaseRegistrationSerializer):
    user_type = "hospital"


class EmailLoginSerializer(TokenObtainPairSerializer):
    # override fields: use email instead of username
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        errors = {}
        if not email:
            errors["email"] = ["This field is required."]
        if not password:
            errors["password"] = ["This field is required."]
        if errors:
            raise serializers.ValidationError(errors)

        # normalize email
        email = email.lower()

        # validate email format
        try:
            validate_email_address(email)
        except DjangoValidationError:
            raise serializers.ValidationError(
                {"email": ["Enter a valid email address."]}
            )

        # check user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"non_field_errors": ["Invalid credentials."]}
            )

        # check password
        if not user.check_password(password):
            raise serializers.ValidationError(
                {"non_field_errors": ["Invalid credentials."]}
            )

        # generate tokens
        refresh = self.get_token(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
            },
        }


class LogOutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class OTPVerificationSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, allow_null=False)
    session_token = serializers.CharField(max_length=64, allow_null=False)

    def validate(self, attrs):
        """
        Validate that otp and session_token are provided and valid.
        """
        otp = attrs.get("otp")
        session_token = attrs.get("session_token")

        if otp is None or session_token is None:
            raise serializers.ValidationError({"OTP and session token are required."})

        return attrs

    def to_internal_value(self, data):
        """
        Process incoming data without custom error formatting.
        """
        return super().to_internal_value(data)

    def to_representation(self, instance):
        """
        Format successful responses without interfering with errors.
        """
        return super().to_representation(instance)


class BaseOTPResendSerializer(serializers.Serializer):
    session_token = serializers.CharField(
        max_length=64,
        required=True,
        help_text="A valid session token is required to proceed.",
    )
    purpose = None

    def validate_session_token(self, value):
        # Validate session token
        token = SessionToken.objects.filter(
            token=value, purpose=self.purpose, is_used=False
        ).first()
        if not token or token.is_expired():
            raise serializers.ValidationError("Invalid or expired session token.")

        return value

    def validate(self, attrs):
        """
        Validate that session_token is provided and valid.
        """
        session_token = attrs.get("session_token")

        if session_token is None:
            raise serializers.ValidationError("Session token is required.")

        return attrs

    def to_internal_value(self, data):
        """
        Process incoming data without custom error formatting.
        """
        return super().to_internal_value(data)

    def to_representation(self, instance):
        """
        Format successful responses without interfering with errors.
        """
        return super().to_representation(instance)


class SignUpOTPResendSerializer(BaseOTPResendSerializer):
    purpose = "email_verification"


class PasswordResetOTPResendSerializer(BaseOTPResendSerializer):
    purpose = "password_reset"


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(
        validators=[EmailValidator(message="Invalid email format.")]
    )


class PasswordResetConfirmSerializer(serializers.Serializer):
    session_token = serializers.CharField(
        max_length=64,
        required=True,
        help_text="A valid session token is required to proceed.",
    )
    otp = serializers.CharField(required=True, max_length=6, min_length=6)
    new_password = serializers.CharField(required=True, min_length=8)

    def validate_session_token(self, value):
        try:
            session = SessionToken.objects.get(token=value, purpose="password_reset")
            if not session.is_valid():
                raise serializers.ValidationError("Invalid or expored session token")
        except SessionToken.DoesNotExist:
            raise serializers.ValidationError("Invalid session token")
        return value

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")
        return value

    def validate_new_password(self, value):
        if not re.search(r"[A-Z]", value):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter."
            )
        if not re.search(r"[a-z]", value):
            raise serializers.ValidationError(
                "Password must contain at least one lowercase letter."
            )
        if not re.search(r"[0-9]", value):
            raise serializers.ValidationError(
                "Password must contain at least one digit."
            )
        # if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
        #     raise serializers.ValidationError("Password must contain at least one special character.")
        return value

    def validate(self, attrs):
        session_token_value = attrs.get("session_token")
        otp_value = attrs.get("otp")

        try:
            session = SessionToken.objects.get(
                token=session_token_value, purpose="password_reset"
            )
        except SessionToken.DoesNotExist:
            raise serializers.ValidationError(
                {"session_token": "Invalid session token."}
            )

        if not session.is_valid():
            raise serializers.ValidationError(
                {"session_token": "Session token is invalid or expired."}
            )

        # Find OTP
        otp_obj = (
            OTP.objects.filter(user=session.user, purpose=session.purpose)
            .order_by("-created_at")
            .first()
        )
        if not otp_obj:
            raise serializers.ValidationError({"otp": "No OTP found for this session."})

        if otp_obj.is_expired():
            raise serializers.ValidationError({"otp": "OTP has expired."})

        if not otp_obj.verify_otp(otp_value):
            raise serializers.ValidationError({"otp": "Invalid OTP."})

        # attach for view use
        attrs["session"] = session
        attrs["otp"] = otp_obj

        return attrs


class DoctorOnboardingSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True, required=True)
    first_name = serializers.CharField(write_only=True, required=True)
    last_name = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    specialization = serializers.ListField(
        child=serializers.ChoiceField(choices=SPECIALIZATION_CHOICES)
    )
    license_number = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Doctor
        fields = [
            "email",
            "first_name",
            "last_name",
            "password",
            "specialization",
            "license_number",
        ]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            # Raise your custom exception instead of a generic ValidationError
            raise ExistingUserError()
        return value

    def validate(self, attrs):
        license_number = attrs.get("license_number")
        if Doctor.objects.filter(license_number=license_number).exists():
            raise ExistingLicenseError()
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        hospital = getattr(request.user, "hospital", None)

        email = validated_data.pop("email")
        first_name = validated_data.pop("first_name")
        last_name = validated_data.pop("last_name")
        password = validated_data.pop("password", None)

        # create the User account for the doctor

        user = User.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password or User.objects.make_random_password(),
            user_type="doctor",  # if you have a role field
            is_activated=True,
        )

        # create the Doctor profile
        doctor = Doctor.objects.create(
            user=user,
            hospital=hospital,
            **validated_data,
        )

        # store credentials for email later
        doctor._raw_password = password  # attach to object, can be used in view
        return doctor

    def to_internal_value(self, data):
        """
        Process incoming data without custom error formatting.
        """
        return super().to_internal_value(data)

    def to_representation(self, instance):
        """
        Format successful responses without interfering with errors.
        """
        return super().to_representation(instance)


class PatientOnboardingSerializer(serializers.ModelSerializer):
    # User-related fields
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    age = serializers.IntegerField(write_only=True)
    gender = serializers.ChoiceField(
        choices=[("male", "Male"), ("female", "Female")], write_only=True
    )

    # Patient-related fields
    hospital_id = serializers.CharField(
        write_only=True, required=False, allow_null=True, allow_blank=True
    )
    medical_history = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )

    class Meta:
        model = Patient
        fields = [
            "first_name",
            "last_name",
            "age",
            "gender",
            "hospital_id",
            "medical_history",
        ]

    def create(self, validated_data):
        user = self.context["request"].user
        hospital_id = validated_data.pop("hospital_id", None)

        # Update the user's fields
        user.first_name = validated_data.get("first_name")
        user.last_name = validated_data.get("last_name")
        user.age = validated_data.get("age")
        user.gender = validated_data.get("gender")
        user.save()

        # Find hospital if hospital_id is provided
        hospital = None
        if hospital_id:
            hospital = Hospital.objects.filter(hospital_id=hospital_id).first()
            if not hospital:
                raise serializers.ValidationError(
                    {"hospital_id": "Invalid hospital ID."}
                )
        else:
            # If no hospital_id provided, randomly assign a hospital
            hospital = Hospital.objects.order_by("?").first()
            if not hospital:
                raise serializers.ValidationError(
                    {"hospital_id": "No hospitals available to assign."}
                )

        # Create patient profile
        try:
            patient = Patient.objects.create(
                user=user,
                hospital=hospital if hospital else None,
                medical_history=validated_data.get("medical_history", ""),
                assigned_doctor=None,  # assigned later by hospital
            )
        except IntegrityError:
            raise IntegrityError("User already has a patient profile.")

        return patient


class HospitalOnboardingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = [
            "hospital_id",
            "name",
            "description",
            "address",
            "contact_email",
            "website_link",
        ]
        read_only_fields = ["hospital_id"]

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user

        if not user.is_activated:  # Assuming you set this after OTP verification
            raise serializers.ValidationError(
                {"detail": "You must verify your account before creating a hospital."}
            )

        # Ensure a user doesn’t create more than one hospital
        if hasattr(user, "hospital"):
            raise ExistingHospitalError()
        hospital = Hospital.objects.create(user=user, **validated_data)
        return hospital


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "age", "gender"]


class AssignedDoctorSerializer(serializers.ModelSerializer):
    user = UserInfoSerializer(read_only=True)

    class Meta:
        model = Doctor
        fields = ["doctor_id", "user", "specialization", "license_number"]


class HospitalDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ["hospital_id", "name", "description", "address"]
        ref_name = "Hospitals.HospitalDetailSerializer"


class PatientProfileUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name", required=False)
    last_name = serializers.CharField(source="user.last_name", required=False)
    age = serializers.IntegerField(source="user.age", required=False)
    gender = serializers.CharField(source="user.gender", required=False)

    class Meta:
        model = Patient
        fields = ["first_name", "last_name", "age", "gender", "medical_history"]

    def update(self, instance, validated_data):
        # Handle nested user fields
        user_data = validated_data.pop("user", {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        instance.user.save()

        # Update patient fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class PatientProfileDetailSerializer(serializers.ModelSerializer):
    patient_id = serializers.ReadOnlyField()
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    age = serializers.IntegerField(source="user.age", read_only=True)
    gender = serializers.CharField(source="user.gender", read_only=True)
    hospital = HospitalDetailSerializer(read_only=True)
    assigned_doctor = AssignedDoctorSerializer(read_only=True)

    class Meta:
        model = Patient
        fields = [
            "email",
            "patient_id",
            "first_name",
            "last_name",
            "age",
            "gender",
            "medical_history",
            "hospital",
            "assigned_doctor",
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        assigned_doctor = rep.get("assigned_doctor")
        if assigned_doctor and "user" in assigned_doctor:
            user_data = assigned_doctor.pop("user", {})
            assigned_doctor.update(user_data)
            rep["assigned_doctor"] = assigned_doctor

        return rep


class DoctorPatientListSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    patient_id = serializers.CharField(read_only=True)

    class Meta:
        model = Patient
        fields = ["patient_id", "email", "first_name", "last_name"]


class DoctorProfileDetailSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", required=False)
    last_name = serializers.CharField(source="user.last_name", required=False)
    age = serializers.IntegerField(source="user.age", required=False)
    gender = serializers.CharField(source="user.gender", required=False)
    specialization = serializers.ListField(
        child=serializers.ChoiceField(choices=SPECIALIZATION_CHOICES), required=False
    )
    license_number = serializers.CharField(required=False)
    hospital = HospitalDetailSerializer(read_only=True)
    # patients = DoctorPatientListSerializer(many=True, read_only=True)

    class Meta:
        model = Doctor
        fields = [
            "email",
            "doctor_id",
            "first_name",
            "last_name",
            "age",
            "gender",
            "specialization",
            "hospital",
            "license_number",
        ]


class DoctorProfileUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name", required=False)
    last_name = serializers.CharField(source="user.last_name", required=False)
    age = serializers.IntegerField(source="user.age", required=False)
    gender = serializers.ChoiceField(
        source="user.gender", required=False, choices=GENDER
    )
    specialization = serializers.ListField(
        child=serializers.ChoiceField(choices=SPECIALIZATION_CHOICES), required=False
    )
    license_number = serializers.CharField(required=False)

    class Meta:
        model = Doctor
        fields = [
            "first_name",
            "last_name",
            "age",
            "gender",
            "specialization",
            "license_number",
        ]

    def update(self, instance, validated_data):
        # pop nested user data
        user_data = validated_data.pop("user", {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        instance.user.save()

        # update doctor fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class DoctorListSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source="user.get_full_name", read_only=True)
    specialization = serializers.CharField(read_only=True)

    class Meta:
        model = Doctor
        fields = ["doctor_id", "doctor_name", "specialization"]


class PatientListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="user.get_full_name", read_only=True)
    assigned_doctor_id = serializers.CharField(
        source="assigned_doctor.doctor_id", read_only=True
    )
    assigned_doctor_name = serializers.CharField(
        source="assigned_doctor.user.get_full_name", read_only=True
    )

    class Meta:
        model = Patient
        fields = [
            "patient_id",
            "patient_name",
            "assigned_doctor_id",
            "assigned_doctor_name",
        ]


class PatientScheduleLogSerializer(serializers.ModelSerializer):
    prescription_id = serializers.CharField(
        source="prescription_drug.prescription.prescription_id", read_only=True
    )
    drug_name = serializers.CharField(
        source="prescription_drug.drug_name", read_only=True
    )
    dosage = serializers.CharField(
        source="prescription_drug.dosage_instruction", read_only=True
    )
    status = serializers.SerializerMethodField()
    next = serializers.BooleanField(default=False)

    class Meta:
        model = PrescriptionLog
        fields = [
            "prescription_id",
            "log_id",
            "drug_name",
            "dosage",
            "date",
            "scheduled_time",
            "status",
            "taken",
            "taken_at",
            "next",
        ]

    def get_status(self, obj):
        return obj.get_status()


class PatientActivePrescriptionSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()
    start_date = serializers.DateField(source="prescription.start_date")
    status = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()

    class Meta:
        model = PrescriptionDrug
        fields = [
            "drug_id",
            "drug_name",
            "start_date",
            "end_date",
            "frequency_per_day",
            "duration_days",
            "status",
            "progress",
            "stats",
        ]

    def get_status(self, obj):
        return obj.get_status

    def get_end_date(self, obj):
        return obj.get_end_date()

    def get_progress(self, obj):
        logs = PrescriptionLog.objects.filter(prescription_drug=obj)
        total = logs.count()
        if total == 0:
            return 0
        taken = logs.filter(taken=True).count()
        return round((taken / total) * 100, 2)

    def get_stats(self, obj):
        logs = PrescriptionLog.objects.filter(prescription_drug=obj)
        taken = logs.filter(taken=True).count()
        missed = sum(1 for log in logs if log.get_status() == "missed")
        pending = sum(1 for log in logs if log.get_status() == "pending")
        return {
            "taken": taken,
            "missed": missed,
            "pending": pending,
        }


class DoctorActivePrescriptionSerializer(serializers.ModelSerializer):
    prescription_id = serializers.CharField(source="prescription.prescription_id")
    patient_id = serializers.CharField(source="prescription.patient.patient_id")
    doctor_name = serializers.CharField(source="prescription.doctor.user.get_full_name")
    patient_name = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()
    start_date = serializers.DateField(source="prescription.start_date")
    status = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    daily_times = serializers.SerializerMethodField()

    class Meta:
        model = PrescriptionDrug
        fields = [
            "prescription_id",
            "patient_id",
            "patient_name",
            "doctor_name",
            "drug_id",
            "drug_name",
            "dosage_instruction",
            "start_date",
            "end_date",
            "frequency_per_day",
            "daily_times",
            "duration_days",
            "status",
            "progress",
            "stats",
        ]

    def get_patient_name(self, obj):
        user = obj.prescription.patient.user
        if user:
            return user.get_full_name()
        return None

    def get_daily_times(self, obj):
        return obj.get_daily_times()

    def get_status(self, obj):
        return obj.get_status

    def get_end_date(self, obj):
        return obj.get_end_date()

    def get_progress(self, obj):
        logs = PrescriptionLog.objects.filter(prescription_drug=obj)
        total = logs.count()
        if total == 0:
            return 0
        taken = logs.filter(taken=True).count()
        return round((taken / total) * 100, 2)

    def get_stats(self, obj):
        logs = PrescriptionLog.objects.filter(prescription_drug=obj)
        taken = logs.filter(taken=True).count()
        missed = sum(1 for log in logs if log.get_status() == "missed")
        pending = sum(1 for log in logs if log.get_status() == "pending")
        return {
            "taken": taken,
            "missed": missed,
            "pending": pending,
        }


class AdminPatientListSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    gender = serializers.CharField(source="user.gender")
    age = serializers.CharField(source="user.age")
    adherence_percentage = serializers.SerializerMethodField()
    assigned_doctor_name = serializers.CharField(
        source="assigned_doctor.user.get_full_name"
    )

    class Meta:
        model = Patient
        fields = [
            "patient_id",
            "patient_name",
            "gender",
            "age",
            "assigned_doctor_name",
            "medical_history",
            "adherence_percentage",
        ]

    def get_patient_name(self, obj):
        if obj.user:
            return obj.user.get_full_name()
        return None

    def get_adherence_percentage(self, obj):
        if obj.user:
            result = obj.user.patient.adherence_summary()
            adherence_percentage = result.get("adherence_percentage", None)
            return adherence_percentage
        return None


class AdminDoctorListSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source="user.get_full_name")
    gender = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    num_patients = serializers.SerializerMethodField()
    patients = serializers.SerializerMethodField()
    patients_adherence_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = [
            "doctor_id",
            "doctor_name",
            "specialization",
            "gender",
            "age",
            "num_patients",
            "patients",
            "patients_adherence_percentage",
        ]

    def get_gender(self, obj):
        gender = obj.user.gender
        if gender and not gender == "":
            return obj.user.gender
        return None

    def get_age(self, obj):
        if obj.user.age:
            return obj.user.age
        return None

    def get_patients_adherence_percentage(self, obj):
        if obj.user:
            result = obj.user.doctor.adherence_summary()
            adherence_percentage = result.get("adherence_percentage", None)
            return adherence_percentage
        return None

    def get_num_patients(self, obj):
        if obj.user:
            return obj.patients.count()
        return 0

    def get_patients(self, obj):
        if obj.patients.exists():
            return [patient.user.get_full_name() for patient in obj.patients.all()]
        return None


class PrescriptionLogSerializer(serializers.ModelSerializer):
    prescription_id = serializers.CharField(
        source="prescription_drug.prescription.prescription_id", read_only=True
    )
    drug_name = serializers.CharField(
        source="prescription_drug.drug_name", read_only=True
    )

    class Meta:
        model = PrescriptionLog
        fields = [
            "prescription_id",
            "drug_name",
            "date",
            "scheduled_time",
            "taken",
            "taken_at",
        ]
