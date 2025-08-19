import threading
from django.core.exceptions import ObjectDoesNotExist

_thread_locals = threading.local()

def get_current_hospital():
    """Return the hospital linked to the current user in this thread, if any."""
    return getattr(_thread_locals, 'hospital', None)

def get_current_user():
    """Return the current authenticated user in this thread, if any."""
    return getattr(_thread_locals, 'user', None)

class HospitalTenantMiddleware:
    """
    Middleware to attach current user and hospital (if exists) to thread-local storage.
    Useful for multi-tenant access without always passing hospital in queries.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            _thread_locals.user = request.user

            # safely fetch hospital if it exists
            try:
                _thread_locals.hospital = request.user.hospital
            except ObjectDoesNotExist:
                _thread_locals.hospital = None
        else:
            _thread_locals.user = None
            _thread_locals.hospital = None

        response = self.get_response(request)

        # clear after request to prevent leakage across threads
        _thread_locals.user = None
        _thread_locals.hospital = None

        return response
