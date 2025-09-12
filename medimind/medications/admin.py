from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Prescription, PrescriptionDrug, PrescriptionLog


# Inline for PrescriptionDrug to show drugs within Prescription admin
class PrescriptionDrugInline(admin.TabularInline):
    model = PrescriptionDrug
    extra = 1
    fields = ('drug_id', 'drug_name', 'dosage_instruction', 'frequency_per_day', 'duration_days', 'get_status', 'get_end_date')
    readonly_fields = ('drug_id', 'get_status', 'get_end_date', 'created_at', 'updated_at')
    show_change_link = True

# Inline for PrescriptionLog to show logs within PrescriptionDrug admin
class PrescriptionLogInline(admin.TabularInline):
    model = PrescriptionLog
    extra = 0
    fields = ('log_id', 'date', 'scheduled_time', 'taken', 'notified', 'taken_at', 'get_status')
    readonly_fields = ('log_id', 'get_status', 'created_at', 'updated_at')
    can_delete = False

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('prescription_id', 'patient_name', 'doctor_name', 'start_date', 'end_date', 'created_at')
    list_filter = ('start_date', 'end_date', 'doctor')
    search_fields = (
        'prescription_id',
        'patient__user__first_name',
        'patient__user__last_name',
        'doctor__user__first_name',
        'doctor__user__last_name'
    )
    inlines = [PrescriptionDrugInline]
    readonly_fields = ('prescription_id', 'created_at', 'updated_at')
    date_hierarchy = 'start_date'
    ordering = ('-created_at',)

    def patient_name(self, obj):
        return obj.patient.user.get_full_name()
    patient_name.short_description = _('Patient')

    def doctor_name(self, obj):
        return obj.doctor.user.get_full_name()
    doctor_name.short_description = _('Doctor')

@admin.register(PrescriptionDrug)
class PrescriptionDrugAdmin(admin.ModelAdmin):
    list_display = (
        'drug_id',
        'drug_name',
        'prescription_link',
        'patient_name',
        'frequency_per_day',
        'duration_days',
        'get_status',
        'get_end_date',
        'daily_times_strict',
        'daily_times_default',
        'created_at'
    )
    list_filter = ('prescription__doctor', 'frequency_per_day', 'prescription__start_date')
    search_fields = (
        'drug_id',
        'drug_name',
        'prescription__prescription_id',
        'prescription__patient__user__first_name',
        'prescription__patient__user__last_name'
    )
    inlines = [PrescriptionLogInline]
    readonly_fields = ('drug_id', 'get_status', 'get_end_date', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    actions = ['generate_schedule_strict', 'generate_schedule_default']

    def prescription_link(self, obj):
        url = reverse('admin:medications_prescription_change', args=[obj.prescription.id])
        return format_html('<a href="{}">{}</a>', url, obj.prescription.prescription_id)
    prescription_link.short_description = _('Prescription')

    def patient_name(self, obj):
        return obj.prescription.patient.user.get_full_name()
    patient_name.short_description = _('Patient')

    def daily_times_strict(self, obj):
        return ", ".join(obj.get_daily_times(strict=True))
    daily_times_strict.short_description = _('Daily Times (Strict)')

    def daily_times_default(self, obj):
        return ", ".join(obj.get_daily_times(strict=False))
    daily_times_default.short_description = _('Daily Times (Default)')

    def generate_schedule_strict(self, request, queryset):
        for drug in queryset:
            drug.generate_schedule(strict=True)
        self.message_user(request, _("Successfully generated strict schedules for selected drugs."))
    generate_schedule_strict.short_description = _("Generate strict schedule (24-hour spread)")

    def generate_schedule_default(self, request, queryset):
        for drug in queryset:
            drug.generate_schedule(strict=False)
        self.message_user(request, _("Successfully generated default schedules for selected drugs."))
    generate_schedule_default.short_description = _("Generate default schedule (8 AM start)")

@admin.register(PrescriptionLog)
class PrescriptionLogAdmin(admin.ModelAdmin):
    list_display = (
        'log_id',
        'prescription_drug_name',
        'date',
        'scheduled_time',
        'taken',
        'notified',
        'get_status',
        'taken_at'
    )
    list_filter = ('taken', 'notified', 'date', 'prescription_drug__prescription__doctor')
    search_fields = (
        'log_id',
        'prescription_drug__drug_name',
        'prescription_drug__prescription__prescription_id'
    )
    readonly_fields = ('log_id', 'get_status', 'created_at', 'updated_at')
    date_hierarchy = 'date'
    ordering = ('-date', '-scheduled_time')

    def prescription_drug_name(self, obj):
        return obj.prescription_drug.drug_name
    prescription_drug_name.short_description = _('Drug Name')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'prescription_drug__prescription__patient',
            'prescription_drug__prescription__doctor'
        )