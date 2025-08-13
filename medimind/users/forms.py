from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User


class UserAdminCreationForm(UserCreationForm):
    """
    A custom form for creating new users in the admin.
    It extends the standard UserCreationForm to handle the custom User model.
    """
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We need to make sure the password fields aren't required when creating a superuser
        self.fields['password2'].required = False

class UserAdminChangeForm(UserChangeForm):
    """
    A custom form for updating existing users in the admin.
    It extends the standard UserChangeForm.
    """
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_superuser', 'is_activated')
