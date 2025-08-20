from django.urls import path

from .views import (
    DoctorSignUpView,
    EmailLoginView,
    HospitalSignUpView,
    PatientSignUpView,
)

urlpatterns = [
    path('v1/patient/signup/', PatientSignUpView.as_view(), name='patient-signup'),
    path('v1/doctor/signup/', DoctorSignUpView.as_view(), name='doctor-signup'),
    path('v1/hospital/signup/', HospitalSignUpView.as_view(), name='hospital-signup'),
    path('v1/user/login/', EmailLoginView.as_view(), name='signin'),
]