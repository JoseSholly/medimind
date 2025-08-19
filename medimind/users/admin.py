from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.forms import ModelForm
from hospitals.models import Hospital

from .field_choices import SPECIALIZATION_CHOICES
from .forms import DoctorForm, UserChangeForm, UserCreationForm
from .models import Doctor, Patient

User = get_user_model()


class TenantAwareAdmin(admin.ModelAdmin):
    """Restricts queryset to current user's hospital unless superuser/staff."""
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_staff:
            return qs
        return qs.filter(user__hospital=request.user.hospital)





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
    

class PatientInlineForm(ModelForm):
    class Meta:
        model = Patient
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Check if the parent object (Doctor) is available
        if 'instance' in kwargs and kwargs['instance'].assigned_doctor:
            doctor = kwargs['instance'].assigned_doctor
            # Filter the user queryset to include only users from the doctor's hospital
            self.fields['user'].queryset = User.objects.filter(hospital=doctor.user.hospital)
        elif 'request' in kwargs:
            # Fallback for new inline forms
            request = kwargs['request']
            doctor = Doctor.objects.get(user=request.user)
            self.fields['user'].queryset = User.objects.filter(hospital=doctor.user.hospital)


class DoctorPatientInline(admin.StackedInline):
    model = Patient
    can_delete = True
    verbose_name_plural = 'patients'
    extra = 0
    fields = ('user', 'medical_history', 'assigned_doctor')
    readonly_fields = ('medical_history', 'assigned_doctor')
    
    form = PatientInlineForm

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

class SpecializationFilter(admin.SimpleListFilter):
    title = 'Specialization'
    parameter_name = 'specialization'

    def lookups(self, request, model_admin):
        return SPECIALIZATION_CHOICES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(specialization__contains=[self.value()])
        return queryset
        

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("doctor_id", "user", "list_specializations", "license_number", "hospital_name", "created_at")
    search_fields = ("doctor_id", "user__email", "license_number", "specialization")
    ordering = ("-created_at",)
    list_filter = (SpecializationFilter, "user__hospital", "created_at",)
    form = DoctorForm
    readonly_fields =('user','hospital_name',)

    fieldsets = (
        ('Medical info', {'fields': ('user', 'hospital_name','license_number', 'specialization',)}),
    )
    inlines = [DoctorPatientInline]

    def hospital_name(self, obj):
        return obj.user.hospital.name if obj.user.hospital else "-"
    hospital_name.short_description = "Hospital"

    def get_queryset(self, request):
        # Bypass tenant filtering for superusers/staff
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_staff:
            return Doctor._base_manager.all()  # use base manager to avoid tenant filter
        return qs.filter(user__hospital=request.user.hospital)
    
    def list_specializations(self, obj):
        choices_dict = dict(SPECIALIZATION_CHOICES)
        # We'll use a list comprehension to get the human-readable names for each specialization
        specialization_names = [choices_dict.get(spec, spec) for spec in obj.specialization]
        
        # Finally, we join them into a clean string, e.g., "Geriatrics, General Surgery"
        return ", ".join(specialization_names)

    # This sets the column header name for the method we created
    list_specializations.short_description = 'Specialization'
    


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("patient_id", "user", "assigned_doctor", "hospital_name", "created_at")
    search_fields = ("patient_id", "user__email", "assigned_doctor__user__email")
    list_filter = ('assigned_doctor', 'user__hospital', 'created_at')

    def hospital_name(self, obj):
        return obj.user.hospital.name if obj.user.hospital else "-"
    hospital_name.short_description = "Hospital"

    def get_queryset(self, request):
        # Bypass tenant filtering for superusers/staff
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_staff:
            return Patient._base_manager.all()  # use base manager to avoid tenant filter
        return qs.filter(user__hospital=request.user.hospital)
    


class HospitalDoctorInlineForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = '__all__'

    def __init__(self, *args, hospital=None, **kwargs):
        super().__init__(*args, **kwargs)
        if hospital:
            self.fields['user'].queryset = User.objects.filter(
                hospital=hospital,
                doctor__isnull=False
            )
        else:
            self.fields['user'].queryset = User.objects.none()

class HospitalPatientInline(admin.TabularInline):
    model = Patient
    extra = 0
    fields = ('user', 'assigned_doctor', 'medical_history')
    readonly_fields = ('medical_history',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Filter patients whose assigned doctor belongs to the current hospital
        if hasattr(self, 'parent_object') and self.parent_object is not None:
            return qs.filter(assigned_doctor__hospital=self.parent_object)
        return qs




class HospitalDoctorInline(admin.StackedInline):
    model = Doctor
    form = HospitalDoctorInlineForm
    extra = 0
    fields = ('user', 'list_specializations', 'license_number')
    readonly_fields = ('license_number', 'specialization', 'list_specializations')

    def list_specializations(self, obj):
        choices_dict = dict(SPECIALIZATION_CHOICES)
        specialization_names = [choices_dict.get(spec, spec) for spec in obj.specialization]
        return ", ".join(specialization_names)
    list_specializations.short_description = 'Specialization'

    def get_formset(self, request, obj=None, **kwargs):
        FormSet = super().get_formset(request, obj, **kwargs)
        class FormSetWrapper(FormSet):
            def __init__(self, *args, **kwargs):
                kwargs['form_kwargs'] = {'hospital': obj}
                super().__init__(*args, **kwargs)
        return FormSetWrapper

    # formset = HospitalDoctorInlineFormSet  # (include your formset filter if used)


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ['hospital_id', 'name', 'contact_email', 'website_link']
    search_fields = ['name']
    inlines = [HospitalDoctorInline, HospitalPatientInline]

    def get_inline_instances(self, request, obj=None):
        inlines = super().get_inline_instances(request, obj)
        for inline in inlines:
            if isinstance(inline, HospitalPatientInline):
                inline.parent_object = obj
        return inlines
    