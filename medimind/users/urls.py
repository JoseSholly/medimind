from django.urls import path

from .views import (
    DoctorOnboardingAPIView,
    # DoctorSignUpView,
    EmailLoginView,
    HospitalOnboardingAPIView,
    HospitalSignUpView,
    LogoutAPIView,
    PatientOnboardingView,
    PatientSignUpView,
    SignUpOTPResendView,
    SignUpOTPverificationView,
)

urlpatterns = [
    path('v1/patient/signup/', PatientSignUpView.as_view(), name='patient-signup'),
    path('v1/patient/onboarding/', PatientOnboardingView.as_view(), name='patient-onboarding'),
    # path('v1/doctor/signup/', DoctorSignUpView.as_view(), name='doctor-signup'),
    path('v1/doctor/onboarding/', DoctorOnboardingAPIView.as_view(), name='doctor-onboarding'),
    path('v1/hospital/signup/', HospitalSignUpView.as_view(), name='hospital-signup'),
    path('v1/hospital/onboarding/', HospitalOnboardingAPIView.as_view(), name='hospital-onboarding'),
    path('v1/user/otp/verify/', SignUpOTPverificationView.as_view(), name='user-otp-verify'),
    path('v1/user/login/', EmailLoginView.as_view(), name='signin'),
    path('v1/user/logout/', LogoutAPIView.as_view(), name='logout'),
    path("v1/signup/otp/resend/", SignUpOTPResendView.as_view(), name='signup-otp-resend'),
]