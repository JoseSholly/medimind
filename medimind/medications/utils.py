def calculate_adherence(logs):
    """
    Shared adherence calculation.
    Takes a queryset (or iterable) of PrescriptionLog instances.
    Returns dict with taken/missed/pending and adherence_percentage.
    """
    taken = missed = pending = 0

    for log in logs.only("id", "date", "scheduled_time", "taken", "taken_at"):
        status = log.get_status()
        if status == "taken":
            taken += 1
        elif status == "missed":
            missed += 1
        elif status in ("pending", "due"):
            pending += 1

    total = taken + missed + pending
    adherence_percentage = round((taken / total) * 100, 2) if total else 0

    return {
        "taken": taken,
        "missed": missed,
        "pending": pending,
        "adherence_percentage": adherence_percentage,
    }
