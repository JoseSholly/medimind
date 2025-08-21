import random
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models, IntegrityError
from django.utils import timezone

from .middleware import get_current_hospital, get_current_user


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
        except IntegrityError as e:
            raise IntegrityError(str(e))
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

        if not user:
            return qs.none()

        # Superusers and staff always see all data
        if user.is_superuser or user.is_staff:
            return qs

        # If no hospital in context but user has one, use that
        if not hospital and hasattr(user, 'hospital') and user.hospital:
            hospital = user.hospital

        # Still no hospital? deny access
        if not hospital:
            return qs.none()

        return qs.filter(user__hospital=hospital)
    

class OTPManager(models.Manager):
    def create_otp(self, user, purpose, user_type, length=6,):
        """
        Creates and stores a hashed OTP for the given user and purpose.
        """
        raw_code = "".join([str(random.randint(0, 9)) for _ in range(length)])  # numeric OTP
        hashed_code = make_password(raw_code)

        otp = self.create(
            user=user,
            code=hashed_code,
            purpose=purpose,
            user_type=user_type,
        )
        return otp, raw_code
    

class SessionTokenManager(models.Manager):
    def create_token(self, user, purpose, expiry_hours=12):
        """
        Creates a new session token for the given user and purpose.
        Defaults to 12 hours expiry.
        """
        # Invalidate old tokens for this user & purpose (optional, depending on business rules)
        self.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)

        expires_at = timezone.now() + timedelta(hours=expiry_hours)

        token = self.create(
            user=user,
            purpose=purpose,
            expires_at=expires_at,
        )
        return token