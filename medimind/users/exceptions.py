from rest_framework.exceptions import APIException


class ExistingUserError(APIException):
    status_code = 409
    default_detail = "User with this email already exists."
    default_code = "conflict"
    default_code = "conflict"

class ExistingLicenseError(APIException):
    status_code = 409
    default_detail = "Existing licence number."
    default_code = "conflict"
    default_code = "conflict"
