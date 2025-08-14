from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from hospitals.models import Hospital

from .forms import UserChangeForm, UserCreationForm
from .models import Doctor, Patient

User = get_user_model()


class TenantAwareAdmin(admin.ModelAdmin):
    """Restricts queryset to current user's hospital unless superuser/staff."""
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_staff:
            return qs
        return qs.filter(user__hospital=request.user.hospital)


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ['name', 'hospital_id', 'contact_email', 'created_at', 'website_link']
    search_fields = ['name']


class DoctorInline(admin.StackedInline):
    model = Doctor
    can_delete = False
    verbose_name_plural = 'doctor profile'
    fk_name = 'user'
    extra = 0

    def has_add_permission(self, request, obj=None):
        # Disallow adding if Doctor profile exists for this User
        if obj and hasattr(obj, 'doctor'):
            return False
        return super().has_add_permission(request, obj)

class PatientInline(admin.StackedInline):
    model = Patient
    can_delete = False
    verbose_name_plural = 'patient profile'
    fk_name = 'user'
    extra = 0
    

    def has_add_permission(self, request, obj=None):
        if obj and hasattr(obj, 'patient'):
            return False
        return super().has_add_permission(request, obj)

class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm


    list_display = ('email', 'first_name', 'last_name', 'hospital', 'is_doctor','is_patient','is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'hospital',)
    ordering = ('email',)
    search_fields = ('email', 'first_name', 'last_name', )
    inlines = (DoctorInline, PatientInline)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'hospital', 'age', 'gender',)}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_activated', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'hospital', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

admin.site.register(User, UserAdmin)



@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("doctor_id", "user", "specialization", "license_number", "hospital_name", "created_at")
    search_fields = ("doctor_id", "user__email", "license_number", "specialization")
    ordering = ("-created_at",)
    list_filter = ("specialization", "user__hospital", "created_at",)

    def hospital_name(self, obj):
        return obj.user.hospital.name if obj.user.hospital else "-"
    hospital_name.short_description = "Hospital"

    def get_queryset(self, request):
        # Bypass tenant filtering for superusers/staff
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_staff:
            return Doctor._base_manager.all()  # use base manager to avoid tenant filter
        return qs.filter(user__hospital=request.user.hospital)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("patient_id", "user", "assigned_doctor", "hospital_name", "created_at")
    search_fields = ("patient_id", "user__email", "assigned_doctor__user__email")

    def hospital_name(self, obj):
        return obj.user.hospital.name if obj.user.hospital else "-"
    hospital_name.short_description = "Hospital"

    def get_queryset(self, request):
        # Bypass tenant filtering for superusers/staff
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_staff:
            return Patient._base_manager.all()  # use base manager to avoid tenant filter
        return qs.filter(user__hospital=request.user.hospital)