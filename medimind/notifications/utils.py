import os

from twilio.rest import Client


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

    return client.messages.create(
        body=message_body,
        from_=os.getenv("TWILIO_WHATSAPP_FROM"),
        to=f"whatsapp:{phone_number}",
    )
