from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.translation import gettext_lazy as _

from .field_choices import SPECIALIZATION_CHOICES
from .models import Doctor
from .validators import validate_specialization

User = get_user_model()


class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required fields, plus repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on the user, but replaces the password field with admin's password hash display field."""
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password', 'is_active', 'is_staff', 'is_activated')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        return self.initial["password"]
    



class DoctorForm(forms.ModelForm):
    specialization = forms.MultipleChoiceField(
        choices=SPECIALIZATION_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text=_("Specializations associated with the doctor"),
    )

    class Meta:
        model = Doctor
        fields = [
            "user",
            "specialization",
            "license_number",
        ]

    def clean_specialization(self):
        specialization = self.cleaned_data.get("specialization", [])
        validate_specialization(specialization)
        return specialization