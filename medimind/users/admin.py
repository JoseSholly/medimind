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


# class TenantAwareAdmin(admin.ModelAdmin):
#     """Restricts queryset to current user's hospital unless superuser/staff."""
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         if request.user.is_superuser or request.user.is_staff:
#             return qs
#         return qs.filter(user__hospital=request.user.hospital)





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


    list_display = ('email', 'first_name', 'last_name', 'user_type',)
    list_filter = ('is_staff', 'is_active', 'user_type', )
    ordering = ('email',)
    search_fields = ('email', 'first_name', 'last_name', )
    inlines = (DoctorInline, PatientInline)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'age', 'gender',)}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_activated', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
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

class DoctorPatientInlineForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = '__all__'

    def __init__(self, *args, doctor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if doctor:
            self.fields['user'].queryset = Patient.objects.filter(
                assigned_doctor=doctor,
            )
        else:
            self.fields['user'].queryset = Patient.objects.none()
class DoctorPatientInline(admin.StackedInline):
    model = Patient
    # form = DoctorPatientInlineForm
    
    can_delete = True
    verbose_name_plural = 'patients'
    extra = 0
    fields = ('user', "user_email","user_first_name", "user_last_name", 'medical_history', 'assigned_doctor')
    readonly_fields = ("user",'medical_history', 'assigned_doctor',"user_email", "user_first_name", "user_last_name", )
    
    # def get_formset(self, request, obj=None, **kwargs):
    #     FormSet = super().get_formset(request, obj, **kwargs)
    #     class FormSetWrapper(FormSet):
    #         def __init__(self, *args, **kwargs):
    #             kwargs['form_kwargs'] = {'doctor': obj}
    #             super().__init__(*args, **kwargs)
    #     return FormSetWrapper
    

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Email"

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Email"

    def user_first_name(self, obj):
        return obj.user.first_name
    user_first_name.short_description = "First Name"

    def user_last_name(self, obj):
        return obj.user.last_name
    user_last_name.short_description = "Last Name"

    
@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("doctor_id", "doctor_email", "doctor_first_name","doctor_last_name","list_specializations", "license_number", "hospital_name", "created_at")
    search_fields = ("doctor_id", "user__email", "user__first_name","user__last_name","license_number", "specialization")
    ordering = ("-created_at",)
    list_filter = (SpecializationFilter, "hospital", "created_at",)
    form = DoctorForm
    readonly_fields =('user','hospital_name',)

    fieldsets = (
        ('Personal Info', {'fields': ('user', 'hospital_name','license_number', 'specialization',)}),
    )
    inlines = [DoctorPatientInline]

    def hospital_name(self, obj):
        return obj.hospital.name if obj.hospital else "-"
    hospital_name.short_description = "Hospital"

    def doctor_email(self, obj):
        return obj.user.email
    doctor_email.short_description = "Email"

    def doctor_first_name(self, obj):
        return obj.user.first_name
    doctor_first_name.short_description = "First Name"

    def doctor_last_name(self, obj):
        return obj.user.last_name
    doctor_last_name.short_description = "Last Name"


    
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
    list_display = ("patient_id", "user_email", "assigned_doctor", "hospital_name", "created_at")
    search_fields = ("patient_id", "user__email", "assigned_doctor__user__email")
    list_filter = ('assigned_doctor', 'hospital', 'created_at')
    readonly_fields = ("patient_id", "user")

    fieldsets = (
        ('Personal Info', {'fields': ('patient_id', "medical_history",'user',"hospital", "assigned_doctor", )}),
    )

    def hospital_name(self, obj):
        return obj.hospital.name if obj.hospital else "-"
    hospital_name.short_description = "Hospital"


    def user_email(self, obj):
        return obj.user.email if obj.user.email else None
    user_email.short_description = "Email"

    def get_queryset(self, request):
        # Bypass tenant filtering for superusers/staff
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_staff:
            return Patient._base_manager.all()  # use base manager to avoid tenant filter
        return qs.filter(hospital=request.user.hospital)
    


class HospitalDoctorInlineForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = '__all__'

    def __init__(self, *args, hospital=None, **kwargs):
        super().__init__(*args, **kwargs)
        if hospital:
            self.fields['user'].queryset = Doctor.objects.filter(
                hospital=hospital,
            )
        else:
            self.fields['user'].queryset = Doctor.objects.none()



class HospitalPatientInlineForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = '__all__'

    def __init__(self, *args, hospital=None, **kwargs):
        super().__init__(*args, **kwargs)
        if hospital:
            self.fields['user'].queryset = Patient.objects.filter(
                hospital=hospital,
            )
            self.fields['assigned_doctor'].queryset = Doctor.objects.filter(
                hospital=hospital,
            )
        else:
            self.fields['user'].queryset = Patient.objects.none()
            self.fields['assigned_doctor'].queryset = Doctor.objects.none()

class HospitalPatientInline(admin.TabularInline):
    model = Patient
    form = HospitalPatientInlineForm
    extra = 0
    fields = ('user', 'assigned_doctor', 'medical_history')
    readonly_fields = ('medical_history',)


    def get_formset(self, request, obj=None, **kwargs):
        FormSet = super().get_formset(request, obj, **kwargs)
        class FormSetWrapper(FormSet):
            def __init__(self, *args, **kwargs):
                kwargs['form_kwargs'] = {'hospital': obj}
                super().__init__(*args, **kwargs)
        return FormSetWrapper




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
    list_display = ['hospital_id','user__email', 'name', 'contact_email', 'website_link']
    readonly_fields = ("user",)
    search_fields = ['name']
    inlines = [HospitalDoctorInline, HospitalPatientInline]

    def get_inline_instances(self, request, obj=None):
        inlines = super().get_inline_instances(request, obj)
        for inline in inlines:
            if isinstance(inline, HospitalPatientInline):
                inline.parent_object = obj
        return inlines
    