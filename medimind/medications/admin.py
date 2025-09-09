from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Prescription, PrescriptionDrug, PrescriptionLog


# Inline for PrescriptionDrug to show drugs within Prescription admin
class PrescriptionDrugInline(admin.TabularInline):
    model = PrescriptionDrug
    extra = 1
    fields = ('drug_id', 'drug_name', 'dosage_instruction', 'frequency_per_day', 'duration_days')
    readonly_fields = ('drug_id', 'created_at', 'updated_at')

# Inline for PrescriptionLog to show logs within PrescriptionDrug admin
class PrescriptionLogInline(admin.TabularInline):
    model = PrescriptionLog
    extra = 0
    fields = ('log_id', 'date', 'scheduled_time', 'taken', 'taken_at', 'get_status')
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
        'prescription_id',
        'patient_name',
        'frequency_per_day',
        'duration_days',
        'created_at'
    )
    list_filter = ('prescription__doctor', 'frequency_per_day')
    search_fields = (
        'drug_id',
        'drug_name',
        'prescription__prescription_id',
        'prescription__patient__user__first_name',
        'prescription__patient__user__last_name'
    )
    inlines = [PrescriptionLogInline]
    readonly_fields = ('drug_id', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    def prescription_id(self, obj):
        return obj.prescription.prescription_id
    prescription_id.short_description = _('Prescription ID')

    def patient_name(self, obj):
        return obj.prescription.patient.user.get_full_name()
    patient_name.short_description = _('Patient')

@admin.register(PrescriptionLog)
class PrescriptionLogAdmin(admin.ModelAdmin):
    list_display = ('log_id', 'prescription_drug', 'date', 'scheduled_time', 'taken', 'get_status', 'taken_at')
    list_filter = ('taken', 'date', 'prescription_drug__prescription__doctor')
    search_fields = (
        'log_id',
        'prescription_drug__drug_name',
        'prescription_drug__prescription__prescription_id'
    )
    readonly_fields = ('log_id', 'get_status', 'created_at', 'updated_at')
    date_hierarchy = 'date'
    ordering = ('-date', '-scheduled_time')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'prescription_drug__prescription__patient',
            'prescription_drug__prescription__doctor'
        )