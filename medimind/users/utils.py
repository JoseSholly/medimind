from datetime import datetime

from decouple import config
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_email(subject, template_name, recipient_list, context=None):
    """
    Generic email sender utility (HTML + plain fallback).
    
    Args:
        subject (str): Email subject.
        template_name (str): Path to the HTML template (e.g., "user/email_verification.html").
        recipient_list (list): List of recipient emails.
        context (dict, optional): Extra context to pass into the template.
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    context = context or {}

    try:
        # Render HTML template with context
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)  # Fallback plain text

        # Build and send message
        email_message = EmailMultiAlternatives(
            subject, plain_message, from_email, recipient_list
        )
        email_message.attach_alternative(html_message, "text/html")
        email_message.send()

    except Exception as e:
        raise ValidationError(f"Failed to send email: {e}")


# --- Specific wrappers (DRY) ---

def send_email_verification_otp(email, otp):
    return send_email(
        subject="Email OTP Verification",
        template_name="user/email_verification.html",
        recipient_list=[email],
        context={"otp": otp},
    )


def send_onboarding_welcome(email):
    domain_name = config("DOMAIN_NAME", cast=str)
    context = {
        "signin_url": f"{domain_name}/sign-in/",
        "current_year": datetime.now().year,
    }
    return send_email(
        subject="Welcome to NuwellAI!",
        template_name="onboarding/onboarding_welcome.html",
        recipient_list=[email],
        context=context,
    )

def send_doctor_onboarding_welcome(
        doctor_id, 
        hospital_name, 
        hospital_id, 
        user_email, 
        user_password, 
        hospital_contact_email, 
        hospital_address,
    ):
    """
    Sends onboarding welcome email to a new doctor.
    """
    domain_name = config("DOMAIN_NAME", cast=str)
    subject = f"Welcome to {hospital_name} - Your Onboarding Details"
    template_name = "onboarding/doctor_onboarding_welcome.html"  

    context = {
        "doctor_id": doctor_id,
        "hospital_name": hospital_name,
        "hospital_id": hospital_id,
        "user_email": user_email,
        "user_password": user_password,
        "hospital_contact_email": hospital_contact_email,
        "hospital_address": hospital_address,
        "signin_url": f"{domain_name}/sign-in/"
    }

    recipient_list = [user_email]

    send_email(
        subject=subject,
        template_name=template_name,
        recipient_list=recipient_list,
        context=context,
    )