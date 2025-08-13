from decouple import config
from nanoid import generate


class IDGenerator:
    """Centralized ID generator using Nanoid"""
    ALPHABET = config('PASSWORD_ALPHABET', default="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    ID_LENGTH = config('PASSWORD_ID_LENGTH', default=8, cast=int)
    
    @staticmethod
    def hospital_id():
        return f"HOSP-{generate(IDGenerator.ALPHABET, IDGenerator.ID_LENGTH)}"
    
    @staticmethod
    def doctor_id():
        return f"DOC-{generate(IDGenerator.ALPHABET, IDGenerator.ID_LENGTH)}"
    
    @staticmethod
    def patient_id():
        return f"PAT-{generate(IDGenerator.ALPHABET, IDGenerator.ID_LENGTH)}"