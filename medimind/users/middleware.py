import threading

_thread_locals = threading.local()

def get_current_hospital():
    return getattr(_thread_locals, 'hospital', None)

def get_current_user():
    return getattr(_thread_locals, 'user', None)

class HospitalTenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            _thread_locals.hospital = request.user.hospital
            _thread_locals.user = request.user
        else:
            _thread_locals.hospital = None
            _thread_locals.user = None

        response = self.get_response(request)

        # clear after request
        _thread_locals.hospital = None
        _thread_locals.user = None

        return response
