import uuid


def generate_prescription_id():
    return f"PRES-{uuid.uuid4().hex[:8].upper()}"


def generate_drug_id():
    return f"DRUG-{uuid.uuid4().hex[:8].upper()}"

def generate_log_id():
    return f"LOG-{uuid.uuid4().hex[:8].upper()}"