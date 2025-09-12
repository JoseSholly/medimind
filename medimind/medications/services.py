import os

from django.utils import timezone
from notifications.utils import send_missed_logs_notification

from .models import PrescriptionLog
RECIPIENT_NUMBERS = os.getenv("RECIPIENT_NUMBERS").split(",")

def check_missed_logs():
    """
    Query all logs, find missed ones, and send WhatsApp reminders.
    """
    now = timezone.localtime(timezone.now())
    today_date = now.date()
    missed_logs = PrescriptionLog.objects.filter(
        taken=False,
        notified=False,
        date=today_date,
    ).select_related("prescription_drug__prescription__patient__user")

    notified_logs = []
    if missed_logs.count() > 0:
        for log in missed_logs:
            scheduled_dt = timezone.make_aware(
                timezone.datetime.combine(log.date, log.scheduled_time)
            )

            # Only notify if >1 hour grace has passed
            if now > scheduled_dt + timezone.timedelta(hours=1):
                patient = log.prescription_drug.prescription.patient
                user = patient.user
                user_full_name = user.get_full_name()
                drug_name = log.prescription_drug.drug_name
                scheduled_time_12h = log.scheduled_time.strftime("%I:%M %p")
                for recipient in RECIPIENT_NUMBERS:
                    sent = send_missed_logs_notification(
                        phone_number=recipient, user_full_name=user_full_name, drug_name=drug_name, scheduled_time_12h=scheduled_time_12h
                    )

                if sent:
                    log.notified = True
                    log.save(update_fields=["notified"])
                    notified_logs.append(log)

        return notified_logs
    else: 
        return []