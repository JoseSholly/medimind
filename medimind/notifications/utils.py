import os

from twilio.rest import Client
from users.utils import send_email

RECIPIENT_NUMBERS = os.getenv("RECIPIENT_NUMBERS").split(",")


def send_prescription_notification(
    phone_number: str,
    patient_name: str,
    doctor_name: str,
    drugs: list
):
    """
    Send a WhatsApp notification to the patient with multiple prescription drugs.
    `drugs` is a list of dicts with:
        - drug_name
        - dosage_instruction
        - frequency_per_day
        - duration_days
        - daily_times
        - start_date
        - end_date
    """
    client = Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    )

    # Build drug details section
    drug_lines = []
    for d in drugs:
        daily_times_text = ", ".join(d["daily_times"]) if d["daily_times"] else "—"
        drug_lines.append(
            f"💊 {d['drug_name']}\n"
            f"📖 {d['dosage_instruction']}\n"
            f"⏰ {d['frequency_per_day']}x/day ({daily_times_text})\n"
            f"📆 {d['duration_days']} days\n"
            f"🗓 {d['start_date']} → {d['end_date']}\n"
        )

    drugs_text = "\n".join(drug_lines)

    message_body = (
        f"Hello {patient_name},\n\n"
        f"Dr. {doctor_name} has prescribed the following medications:\n\n"
        f"{drugs_text}\n"
        f"✅ Please follow these instructions carefully.\n"
        f"Stay healthy, Medimind cares for you ❤️"
    )
    for phone in RECIPIENT_NUMBERS:
        client.messages.create(
            body=message_body,
            from_=os.getenv("TWILIO_WHATSAPP_FROM"),
            to=phone,
        )


def send_missed_logs_notification(phone_number, user_full_name, drug_name, scheduled_time_12h):
    """
    Send WhatsApp reminder for a missed medication log.
    """
    if not phone_number:
        return False

    # Twilio setup
    client = Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    )
    sender=os.getenv("TWILIO_WHATSAPP_FROM"),

    

    message_body = (
        f"Hello {user_full_name},\n\n"
        f"You missed your medication: *{drug_name}* scheduled at {scheduled_time_12h}.\n\n"
        "Please take your dose as soon as possible or mark it in the app."
    )

    try:
        client.messages.create(
            body=message_body,
            from_=sender,
            to=phone_number,
        )
        return True
    except Exception as e:
        print(f"WhatsApp reminder failed for {user_full_name}: {e}")
        return False
    

def send_prescription_notice_via_mail(doctor_name, patient_email, patient_name, drugs_data):
    """
    Send an email notification to the patient about a new prescription."""
    send_email(
                    subject=f"Your Prescription from Dr. {doctor_name}",
                    template_name="notification/prescription_notice.html",
                    recipient_list=[patient_email],
                    context={
                        "patient_name": patient_name,
                        "doctor_name": doctor_name,
                        "drugs": drugs_data,
                    },
                )


def send_missed_logs_notification_via_mail(user_email, user_full_name, drug_name, scheduled_time_12h):
    """
    Sends a missed dosage notification email to the user.
    Returns True if successful, False otherwise.
    """
    subject = f"Missed Dosage Notice for {drug_name}"
    template_name = "notification/missed_dosage.html"
    recipient_list = [user_email]

    context = {
        "patient_name": user_full_name,
        "medication_name": drug_name,
        "scheduled_time": scheduled_time_12h,
    }

    try:
        send_email(subject, template_name, recipient_list, context)
        return True
    except Exception as e:
        print(f"Failed to send missed log email to {user_email}: {e}")
        return False
