from rest_framework import serializers
from users.models import Patient

from medications.models import Prescription, PrescriptionDrug


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
