from datetime import timedelta

from medications.models import Prescription, PrescriptionDrug
from rest_framework import serializers
from users.models import Patient


class PrescriptionDrugSerializer(serializers.ModelSerializer):

    class Meta:
        model = PrescriptionDrug
        fields = [
            "drug_id",
            "drug_name",
            "dosage_instruction",
            "frequency_per_day",
            "duration_days",
        ]
        read_only_fields = ["drug_id"]


class PrescriptionCreateSerializer(serializers.ModelSerializer):
    drugs = PrescriptionDrugSerializer(many=True)
    patient_id = serializers.CharField(write_only=True)

    class Meta:
        model = Prescription
        fields = [
            "prescription_id",
            "patient_id",
            "start_date",
            "end_date",
            "drugs",
        ]
        read_only_fields = ["prescription_id"]


    def validate_patient_id(self, patient_id):
        """
        Ensure the patient exists and belongs to the same hospital as the doctor.
        """
        request = self.context.get("request")

        try:
            patient = Patient.objects.get(patient_id=patient_id)
        except Patient.DoesNotExist:
            raise serializers.ValidationError("Invalid patient_id. Pa not found.")

        doctor = request.user.doctor

        if doctor.hospital != patient.hospital:
            raise serializers.ValidationError("Patient is not associated with your hospital.")

        return patient  # we’ll replace doctor_id with doctor object

    def create(self, validated_data):
        # Pop out nested drugs
        drugs_data = validated_data.pop("drugs", [])
        request = self.context["request"]  # inject doctor from view
        doctor = request.user.doctor
        patient = validated_data.pop("patient_id")


        # Create prescription with doctor + patient
        prescription = Prescription.objects.create(doctor=doctor, patient=patient, **validated_data)

        # Create nested drugs
        for drug_data in drugs_data:
            PrescriptionDrug.objects.create(prescription=prescription, **drug_data)
            

        return prescription


class PrescriptionDrugTimelineSerializer(serializers.ModelSerializer):
    timeline = serializers.SerializerMethodField()
    daily_times = serializers.SerializerMethodField()

    class Meta:
        model = PrescriptionDrug
        fields = [
            "drug_id",
            "drug_name",
            "dosage_instruction",
            "frequency_per_day",
            "duration_days",
            "daily_times",
            "timeline", 
        ]

    def get_daily_times(self, obj):
        return obj.get_daily_times()

    def get_timeline(self, obj):
        timeline = []
        start_date = obj.prescription.start_date
        logs = { (log.date.strftime("%Y-%m-%d"), log.scheduled_time.strftime("%H:%M")): log
                 for log in obj.logs.all() }  # map logs by date+time

        for day in range(obj.duration_days):
            current_date = start_date + timedelta(days=day)
            current_date_str = current_date.strftime("%Y-%m-%d")
            doses = []

            for t in obj.get_daily_times():
                log = logs.get((current_date_str, t))
                doses.append({
                    "time": t,
                    "taken": log.taken if log else False,
                    "status": log.get_status() if log else "pending",
                })

            timeline.append({
                "day": f"Day {day + 1}",
                "date": current_date_str,
                "doses": doses
            })

        return timeline

class PrescriptionDetailSerializer(serializers.ModelSerializer):
    doctor = serializers.CharField(source="doctor.user.get_full_name")
    patient = serializers.CharField(source="patient.user.get_full_name")
    drugs = PrescriptionDrugTimelineSerializer(many=True, read_only=True)

    class Meta:
        model = Prescription
        fields = [
            "prescription_id",
            "doctor",
            "patient",
            "start_date",
            "end_date",
            "drugs",
        ]
