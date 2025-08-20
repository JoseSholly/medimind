from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_email_verification_otp(email, otp):
    subject = "Email OTP Verification"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email] 

    try:
        # Load the HTML template and pass the OTP dynamically
        html_message = render_to_string(
            "user/email_verification.html", {"otp": otp}
        )
        plain_message = strip_tags(
            html_message
        )  # Strip HTML tags for a fallback plain text version

        # Create email message
        email_message = EmailMultiAlternatives(
            subject, plain_message, from_email, recipient_list
        )
        email_message.attach_alternative(
            html_message, "text/html"
        )  # Attach HTML version

        # Send email
        email_message.send()
    except Exception as e:
        return ValidationError(f"Failed to send email: {e}")