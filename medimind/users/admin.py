from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UserAdminChangeForm, UserAdminCreationForm
from .models import Doctor, Patient, User


# Register the custom User model with a custom UserAdmin class
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom Admin for the User model.
    Inherits from BaseUserAdmin to get default user permissions functionality.
    """
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm

    list_display = (
        'email', 
        'first_name', 
        'last_name', 
        'is_staff', 
        'is_active', 
        'is_activated'
    )
    list_filter = (
        'is_staff', 
        'is_active', 
        'is_superuser', 
        'is_activated'
    )
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'hospital')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_activated', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password', 'password2')}
        ),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    """
    Admin for the Doctor model.
    """
    list_display = ('user', 'specialization', 'license_number', 'age', 'gender')
    list_filter = ('specialization', 'gender')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'license_number')
    readonly_fields = ('user',)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """
    Admin for the Patient model.
    """
    list_display = ('user', 'age', 'gender', 'assigned_doctor')
    list_filter = ('gender', 'assigned_doctor')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('user',)
