from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "appointment_id",
        "patient_name",
        "doctor_name",
        "hospital_name",
        "date",
        "time",
        "status",
        "rescheduled_count",
        "last_rescheduled_at",
        "created_at",
    )
    list_filter = ("status", "hospital", "doctor", "date")
    search_fields = (
        "appointment_id",
        "patient__user__first_name",
        "patient__user__last_name",
        "doctor__user__first_name",
        "doctor__user__last_name",
        "hospital__name",
    )
    list_editable = ("status",)
    date_hierarchy = "date"
    readonly_fields = ("appointment_id", "created_at", "updated_at", "rescheduled_count", "last_rescheduled_at")
    fieldsets = (
        (None, {
            "fields": ("appointment_id", "status")
        }),
        ("Appointment Details", {
            "fields": ("hospital", "doctor", "patient", "date", "time")
        }),
        ("Additional Information", {
            "fields": ("reason", "rescheduled_count", "last_rescheduled_at", "created_at", "updated_at")
        }),
    )

    def patient_name(self, obj):
        return obj.patient.user.get_full_name()
    patient_name.short_description = "Patient"

    def doctor_name(self, obj):
        return obj.doctor.user.get_full_name()
    doctor_name.short_description = "Doctor"

    def hospital_name(self, obj):
        return obj.hospital.name
    hospital_name.short_description = "Hospital"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("patient__user", "doctor__user", "hospital")