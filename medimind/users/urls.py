from django.urls import path

from .views import (  # DoctorSignUpView,
    DoctorDashboardAPIView,
    DoctorOnboardingAPIView,
    DoctorProfileUpdateView,
    EmailLoginView,
    HospitalDoctorListAPIView,
    HospitalOnboardingAPIView,
    HospitalSignUpView,
    LogoutAPIView,
    MarkLogTakenAPIView,
    PasswordResetConfirmView,
    PasswordResetOTPResendView,
    PasswordResetRequestView,
    PatientDashboardAPIView,
    PatientListAPIView,
    PatientOnboardingView,
    PatientProfileUpdateView,
    PatientSignUpView,
    SignUpOTPResendView,
    SignUpOTPverificationView,
    HospitalDashboardAPIView,
)

urlpatterns = [
    path("v1/patient/signup/", PatientSignUpView.as_view(), name="patient-signup"),
    path(
        "v1/patient/onboarding/",
        PatientOnboardingView.as_view(),
        name="patient-onboarding",
    ),
    path(
        "v1/patient/profile/",
        PatientProfileUpdateView.as_view(),
        name="patient-profile-update",
    ),
    path(
        "v1/patient/dashboard/",
        PatientDashboardAPIView.as_view(),
        name="patient-dashboard",
    ),
    path(
        "v1/doctor/profile/",
        DoctorProfileUpdateView.as_view(),
        name="patient-doctor-update",
    ),
    path(
        "v1/doctor/dashboard/",
        DoctorDashboardAPIView.as_view(),
        name="patient-dashboard",
    ),
    path("v1/list-doctors/", HospitalDoctorListAPIView.as_view(), name="doctor-list"),
    path("v1/list-patients/", PatientListAPIView.as_view(), name="patient-list"),
    path(
        "v1/doctor/onboarding/",
        DoctorOnboardingAPIView.as_view(),
        name="doctor-onboarding",
    ),
    path(
        "v1/hospital/dashboard/",
        HospitalDashboardAPIView.as_view(),
        name="hospital-dashboard",
    ),
    path("v1/hospital/signup/", HospitalSignUpView.as_view(), name="hospital-signup"),
    path(
        "v1/hospital/onboarding/",
        HospitalOnboardingAPIView.as_view(),
        name="hospital-onboarding",
    ),
    path(
        "v1/user/otp/verify/",
        SignUpOTPverificationView.as_view(),
        name="user-otp-verify",
    ),
    path("v1/user/login/", EmailLoginView.as_view(), name="signin"),
    path("v1/user/logout/", LogoutAPIView.as_view(), name="logout"),
    path(
        "v1/signup/otp/resend/", SignUpOTPResendView.as_view(), name="signup-otp-resend"
    ),
    path(
        "v1/auth/password-reset/request/",
        PasswordResetRequestView.as_view(),
        name="password-reset-request",
    ),
    path(
        "v1/auth/password-reset/resend-otp/",
        PasswordResetOTPResendView.as_view(),
        name="password-reset-resend-otp",
    ),
    path(
        "v1/auth/password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path(
        "v1/med/<str:log_id>/taken/",
        MarkLogTakenAPIView.as_view(),
        name="mark-log-taken",
    ),
]
