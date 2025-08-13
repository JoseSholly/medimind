from rest_framework import status
from rest_framework.exceptions import (
    MethodNotAllowed,
    NotAuthenticated,
    PermissionDenied,
    Throttled,
)
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, NotAuthenticated):
            response.data = {
                "status": "error",
                "message": "Authentication credentials were not provided or are invalid.",
                
            }
            response.status_code = status.HTTP_401_UNAUTHORIZED

        elif isinstance(exc, PermissionDenied):
            response.data = {
                "status": "error",
                "message": "You do not have permission to access this resource.",
                
            }
            response.status_code = status.HTTP_403_FORBIDDEN

        elif isinstance(exc, Throttled):
            wait_time = exc.wait
            response.data = {
                "status": "error",
                "message": f"Rate limit exceeded. Please try again in {wait_time} seconds.",
                "data": {
                    "wait_time": wait_time,
                },
            }
            response.status_code = status.HTTP_429_TOO_MANY_REQUESTS

        elif isinstance(exc, MethodNotAllowed):
            response.data = {
                "status": "error",
                "message": f"'{exc.detail}' not allowed for this resource.",
                
            }
            response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED

        return response
