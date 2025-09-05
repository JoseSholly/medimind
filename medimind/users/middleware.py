import threading

from django.core.exceptions import ObjectDoesNotExist

_thread_locals = threading.local()

def get_current_hospital():
    """Return the hospital linked to the current user in this thread, if any."""
    return getattr(_thread_locals, "hospital", None)

def get_current_user():
    """Return the current authenticated user in this thread, if any."""
    return getattr(_thread_locals, "user", None)

class HospitalTenantMiddleware:
    """
    Attach current user + hospital to thread-local storage for multi-tenancy.
    Ensures each request is scoped to the right hospital.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            _thread_locals.user = request.user

            try:
                if hasattr(request.user, "doctor") and request.user.doctor.hospital:
                    _thread_locals.hospital = request.user.doctor.hospital
                elif hasattr(request.user, "patient") and request.user.patient.hospital:
                    _thread_locals.hospital = request.user.patient.hospital
                else:
                    _thread_locals.hospital = None
            except ObjectDoesNotExist:
                _thread_locals.hospital = None
        else:
            _thread_locals.user = None
            _thread_locals.hospital = None

        response = self.get_response(request)

        # clean up after request
        _thread_locals.user = None
        _thread_locals.hospital = None

        return response
