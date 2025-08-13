from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from .middleware import get_current_hospital, get_current_user
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        try:
            email = self.normalize_email(email)
            user = self.model(email=email, **extra_fields)
            user.full_clean(exclude=["password"])
            user.set_password(password)
            user.save(using=self._db)
            return user
        except ValidationError as e:
            raise ValidationError(str(e))

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)



class TenantAwareManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        user = get_current_user()
        hospital = get_current_hospital()

        if not user or not hospital:
            # No user or tenant context, return empty queryset
            return qs.none()

        if user.is_superuser or user.is_staff:
            # Admins see all data
            return qs

        # Normal users see only their tenant's data
        return qs.filter(user__hospital=hospital)