from django.urls import path

from .views import (  # DoctorSignUpView,
    DoctorOnboardingAPIView,
    EmailLoginView,
    HospitalOnboardingAPIView,
    HospitalSignUpView,
    LogoutAPIView,
    PasswordResetConfirmView,
    PasswordResetOTPResendView,
    PasswordResetRequestView,
    PatientOnboardingView,
    PatientProfileUpdateView,
    PatientSignUpView,
    SignUpOTPResendView,
    SignUpOTPverificationView,
)

urlpatterns = [
    path('v1/patient/signup/', PatientSignUpView.as_view(), name='patient-signup'),
    path('v1/patient/onboarding/', PatientOnboardingView.as_view(), name='patient-onboarding'),
    path("v1/patient/profile/", PatientProfileUpdateView.as_view(), name="patient-profile-update"),
    # path('v1/doctor/signup/', DoctorSignUpView.as_view(), name='doctor-signup'),
    path('v1/doctor/onboarding/', DoctorOnboardingAPIView.as_view(), name='doctor-onboarding'),
    path('v1/hospital/signup/', HospitalSignUpView.as_view(), name='hospital-signup'),
    path('v1/hospital/onboarding/', HospitalOnboardingAPIView.as_view(), name='hospital-onboarding'),
    path('v1/user/otp/verify/', SignUpOTPverificationView.as_view(), name='user-otp-verify'),
    path('v1/user/login/', EmailLoginView.as_view(), name='signin'),
    path('v1/user/logout/', LogoutAPIView.as_view(), name='logout'),
    path("v1/signup/otp/resend/", SignUpOTPResendView.as_view(), name='signup-otp-resend'),
    path("v1/auth/password-reset/request/", PasswordResetRequestView.as_view(), name='password-reset-request'),
    path("v1/auth/password-reset/resend-otp/", PasswordResetOTPResendView.as_view(), name='password-reset-resend-otp'),
    path("v1/auth/password-reset/confirm/", PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]