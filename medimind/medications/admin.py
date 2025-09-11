from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Prescription, PrescriptionDrug, PrescriptionLog


# Inline for PrescriptionDrug to show drugs within Prescription admin
class PrescriptionDrugInline(admin.TabularInline):
    model = PrescriptionDrug
    extra = 1
    fields = (
        "drug_id",
        "drug_name",
        "dosage_instruction",
        "frequency_per_day",
        "duration_days",
        "get_status",
    )
    readonly_fields = ("drug_id", "created_at", "updated_at", "get_status")
    show_change_link = True


# Inline for PrescriptionLog to show logs within PrescriptionDrug admin
class PrescriptionLogInline(admin.TabularInline):
    model = PrescriptionLog
    extra = 0
    fields = ("log_id", "date", "scheduled_time", "taken", "taken_at", "get_status")
    readonly_fields = ("log_id", "get_status", "created_at", "updated_at")
    can_delete = False


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = (
        "prescription_id",
        "patient_name",
        "doctor_name",
        "start_date",
        "end_date",
        "created_at",
        "updated_at",
    )
    list_filter = ("start_date", "end_date", "doctor", "patient")
    search_fields = (
        "prescription_id",
        "patient__user__first_name",
        "patient__user__last_name",
        "doctor__user__first_name",
        "doctor__user__last_name",
    )
    inlines = [PrescriptionDrugInline]
    readonly_fields = ("prescription_id", "created_at", "updated_at")
    date_hierarchy = "start_date"
    ordering = ("-created_at",)
    list_per_page = 25

    def patient_name(self, obj):
        return obj.patient.user.get_full_name()

    patient_name.short_description = _("Patient")

    def doctor_name(self, obj):
        return obj.doctor.user.get_full_name()

    doctor_name.short_description = _("Doctor")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("patient__user", "doctor__user")
        )


@admin.register(PrescriptionDrug)
class PrescriptionDrugAdmin(admin.ModelAdmin):
    list_display = (
        "drug_id",
        "drug_name",
        "prescription_id",
        "patient_name",
        "doctor_name",
        "frequency_per_day",
        "duration_days",
        "get_status",
        "created_at",
    )
    list_filter = ("prescription__doctor", "frequency_per_day", "prescription__patient")
    search_fields = (
        "drug_id",
        "drug_name",
        "prescription__prescription_id",
        "prescription__patient__user__first_name",
        "prescription__patient__user__last_name",
        "prescription__doctor__user__first_name",
        "prescription__doctor__user__last_name",
    )
    inlines = [PrescriptionLogInline]
    readonly_fields = ("drug_id", "created_at", "updated_at", "get_status")
    ordering = ("-created_at",)
    list_per_page = 25
    actions = ["generate_schedule_default", "generate_schedule_strict"]

    def prescription_id(self, obj):
        return obj.prescription.prescription_id

    prescription_id.short_description = _("Prescription ID")

    def patient_name(self, obj):
        return obj.prescription.patient.user.get_full_name()

    patient_name.short_description = _("Patient")

    def doctor_name(self, obj):
        return obj.prescription.doctor.user.get_full_name()

    doctor_name.short_description = _("Doctor")

    def generate_schedule_default(self, request, queryset):
        for drug in queryset:
            drug.generate_schedule(strict=False)
        self.message_user(
            request,
            _(
                "Successfully generated default schedules for selected prescription drugs."
            ),
        )

    generate_schedule_default.short_description = _(
        "Generate default schedule (8 AM baseline)"
    )

    def generate_schedule_strict(self, request, queryset):
        for drug in queryset:
            drug.generate_schedule(strict=True)
        self.message_user(
            request,
            _(
                "Successfully generated strict schedules for selected prescription drugs."
            ),
        )

    generate_schedule_strict.short_description = _(
        "Generate strict schedule (24-hour spread)"
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "prescription__patient__user",
                "prescription__doctor__user",
            )
        )


@admin.register(PrescriptionLog)
class PrescriptionLogAdmin(admin.ModelAdmin):
    list_display = (
        "log_id",
        "drug_name",
        "prescription_id",
        "date",
        "scheduled_time",
        "taken",
        "get_status",
        "taken_at",
    )
    list_filter = (
        "taken",
        "date",
        "prescription_drug__prescription__doctor",
        "prescription_drug__prescription__patient",
    )
    search_fields = (
        "log_id",
        "prescription_drug__drug_name",
        "prescription_drug__prescription__prescription_id",
        "prescription_drug__prescription__patient__user__first_name",
        "prescription_drug__prescription__patient__user__last_name",
    )
    readonly_fields = ("log_id", "get_status", "created_at", "updated_at")
    date_hierarchy = "date"
    ordering = ("-date", "-scheduled_time")
    list_per_page = 25
    actions = ["mark_as_taken"]

    def drug_name(self, obj):
        return obj.prescription_drug.drug_name

    drug_name.short_description = _("Drug Name")

    def prescription_id(self, obj):
        return obj.prescription_drug.prescription.prescription_id

    prescription_id.short_description = _("Prescription ID")

    def mark_as_taken(self, request, queryset):
        queryset.update(taken=True, taken_at=timezone.now())
        self.message_user(request, _("Selected prescription logs marked as taken."))

    mark_as_taken.short_description = _("Mark selected logs as taken")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "prescription_drug__prescription__patient__user",
                "prescription_drug__prescription__doctor__user",
            )
        )
