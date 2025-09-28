from django.utils import timezone
from notifications.utils import send_missed_logs_notification_via_mail

from .models import PrescriptionLog


def check_missed_logs():
    """
    Find all missed prescription logs for today and send email reminders
    if more than 1 hour has passed since the scheduled time.
    Returns a list of logs that were successfully notified.
    """
    now = timezone.localtime()
    today = now.date()

    missed_logs = (
        PrescriptionLog.objects.filter(
            taken=False,
            notified=False,
            date=today,
        )
        .select_related("prescription_drug__prescription__patient__user")
    )

    notified_logs = []
    for log in missed_logs:
        scheduled_dt = timezone.make_aware(
            timezone.datetime.combine(log.date, log.scheduled_time)
        )

        # Only notify if >1 hour grace period has passed
        if now <= scheduled_dt + timezone.timedelta(hours=1):
            continue

        user = log.prescription_drug.prescription.patient.user
        context = {
            "user_email": user.email,
            "user_full_name": user.get_full_name(),
            "drug_name": log.prescription_drug.drug_name,
            "scheduled_time_12h": log.scheduled_time.strftime("%I:%M %p"),
        }

        if send_missed_logs_notification_via_mail(**context):
            log.notified = True
            log.save(update_fields=["notified"])
            notified_logs.append(log)

    return notified_logs