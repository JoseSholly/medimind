from django.utils import timezone
from rest_framework import serializers
from users.models import Doctor

from .models import Appointment, AppointmentStatus


class AppointmentSerializer(serializers.ModelSerializer):
    """
    Used for listing + retrieving appointments.
    Shows doctor & patient details in a readable way.
    """

    doctor_name = serializers.CharField(
        source="doctor.user.get_full_name", read_only=True
    )
    doctor_id = serializers.CharField(source="doctor.doctor_id", read_only=True)
    
    patient_name = serializers.CharField(
        source="patient.user.get_full_name", read_only=True
    )
    patient_id = serializers.CharField(source="patient.patient_id", read_only=True)
    hospital_name = serializers.CharField(source="hospital.name", read_only=True)
    hospital_id = serializers.CharField(source="hospital.hospital_id", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "appointment_id",
            "hospital_id",
            "hospital_name",
            "doctor_id",
            "doctor_name",
            "patient_id",
            "patient_name",
            "date",
            "time",
            "reason",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["appointment_id", "status", "created_at", "updated_at"]


class AppointmentBookingSerializer(serializers.ModelSerializer):
    doctor_id = serializers.CharField(write_only=True)  # accept doctor_id in request
    doctor = serializers.StringRelatedField(read_only=True)  # show doctor info in response

    class Meta:
        model = Appointment
        fields = ["doctor_id", "doctor", "date", "time", "reason"]

    def validate_doctor_id(self, doctor_id):
        """
        Ensure the doctor exists and belongs to the same hospital as the patient.
        """
        request = self.context.get("request")
        if not request or not hasattr(request.user, "patient"):
            raise serializers.ValidationError("Patient information not available.")

        try:
            doctor = Doctor.objects.get(doctor_id=doctor_id)
        except Doctor.DoesNotExist:
            raise serializers.ValidationError("Invalid doctor_id. Doctor not found.")

        patient = request.user.patient

        if doctor.hospital != patient.hospital:
            raise serializers.ValidationError("Doctor is not associated with your hospital.")

        return doctor  # we’ll replace doctor_id with doctor object

    def create(self, validated_data):
        doctor = validated_data.pop("doctor_id")  # this is the actual Doctor object now
        request = self.context["request"]
        patient = request.user.patient
        hospital = patient.hospital

        return Appointment.objects.create(
            patient=patient,
            hospital=hospital,
            doctor=doctor,
            status=AppointmentStatus.PENDING,
            **validated_data,
        )


class AppointmentStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ["status"]

    def validate_status(self, value):
        if value not in [
            AppointmentStatus.APPROVED,
            AppointmentStatus.DECLINED,
            AppointmentStatus.CANCELLED,
            AppointmentStatus.COMPLETED,
        ]:
            raise serializers.ValidationError("Invalid status update.")
        return value


class AppointmentRescheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ["date", "time"]

    def validate(self, data):
        appointment = self.instance
        doctor = appointment.doctor

        # Ensure both fields are provided
        if "date" not in data or "time" not in data:
            raise serializers.ValidationError(
                {"error": "Both 'date' and 'time' fields are required to reschedule."}
            )


        # Check if doctor has another appointment at that time (only approved or pending)
        conflict_exists = Appointment.objects.filter(
            doctor=doctor,
            date=data["date"],
            time=data["time"],
            status__in=[AppointmentStatus.PENDING, AppointmentStatus.APPROVED],
        ).exclude(id=appointment.id).exists()

        if conflict_exists:
            raise serializers.ValidationError(
                {"error": f"Doctor is not available on {data['date']} at {data['time']}. Request a new appointment time."}
            )

        return data

    def update(self, instance, validated_data):
        instance.date = validated_data["date"]
        instance.time = validated_data["time"]
        instance.status = AppointmentStatus.PENDING  # needs re-approval
        instance.rescheduled_count += 1
        instance.last_rescheduled_at = timezone.now()
        instance.save()
        return instance
