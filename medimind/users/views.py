import logging
from datetime import date, timedelta
from smtplib import SMTPException

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from hospitals.models import Hospital
from medications.models import Prescription, PrescriptionDrug, PrescriptionLog
from rest_framework import generics, serializers, status, views
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import OTP, Doctor, Patient, SessionToken
from .permissions import IsActivated, IsHospital
from .serializers import (
    ActivePrescriptionSerializer,
    DoctorListSerializer,
    DoctorOnboardingSerializer,
    DoctorProfileDetailSerializer,
    DoctorProfileUpdateSerializer,
    DoctorRegistrationSerializer,
    EmailLoginSerializer,
    HospitalOnboardingSerializer,
    HospitalRegistrationSerializer,
    LogOutSerializer,
    OTPVerificationSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetOTPResendSerializer,
    PasswordResetRequestSerializer,
    PatientListSerializer,
    PatientOnboardingSerializer,
    PatientProfileDetailSerializer,
    PatientProfileUpdateSerializer,
    PatientRegistrationSerializer,
    PatientScheduleLogSerializer,
    PrescriptionLogSerializer,
    SignUpOTPResendSerializer,
)
from .utils import (
    send_doctor_onboarding_welcome,
    send_email_verification_otp,
    send_onboarding_welcome,
    send_password_reset_otp,
)

logger = logging.getLogger(__name__)

User = get_user_model()


class PatientSignUpView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = PatientRegistrationSerializer
    http_method_names = ["post"]

    @swagger_auto_schema(
        request_body=PatientRegistrationSerializer, tags=["Patient SignUp"]
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]

            # Check for existing user at the view level
            if User.objects.filter(email=email).exists():
                return Response(
                    {
                        "status": "conflict",
                        "detail": "Existing user with this email address already exists.",
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            with transaction.atomic():
                user = serializer.save()

                # Clear all existing otp related email_verification associated with user
                OTP.objects.filter(
                    user=user, purpose="email_verification", user_type="patient"
                ).delete()

                # Create OTP for email verification
                _, raw_code = OTP.objects.create_otp(
                    user=user, purpose="email_verification", user_type="patient"
                )

                # Create session token
                session_token = SessionToken.objects.create_token(
                    user,
                    purpose="email_verification",
                )
            # Send OTP via email
            try:
                send_email_verification_otp(email=user.email, otp=raw_code)
            except SMTPException as e:
                logger.error(
                    f"Failed to send email verification OTP to {user.email} (user_id: {user.id}): {str(e)}"
                )
                return Response(
                    {
                        "status": "error",
                        "message": "Failed to send OTP",
                        "errors": {
                            "email": ["Unable to send OTP. Please try again later."]
                        },
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            return Response(
                {
                    "status": "success",
                    "data": {
                        "user_id": user.user_id,
                        "session_token": session_token.token,
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        # Return validation errors in the desired format
        return Response(
            {
                "status": "error",
                "detail": "Validation failed",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class DoctorSignUpView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = DoctorRegistrationSerializer
    http_method_names = ["post"]

    @swagger_auto_schema(
        request_body=DoctorRegistrationSerializer, tags=["Doctor SignUp"]
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]

            # Check for existing user at the view level
            if User.objects.filter(email=email).exists():
                return Response(
                    {
                        "status": "conflict",
                        "detail": "Existing user with this email address already exists.",
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            with transaction.atomic():
                user = serializer.save()

                # Clear all existing otp related email_verification associated with user
                OTP.objects.filter(
                    user=user, purpose="email_verification", user_type="doctor"
                ).delete()

                # Create OTP for email verification
                _, raw_code = OTP.objects.create_otp(
                    user=user, purpose="email_verification", user_type="doctor"
                )

                # Create session token
                session_token = SessionToken.objects.create_token(
                    user, purpose="email_verification"
                )
            # Send OTP via email
            try:
                send_email_verification_otp(email=user.email, otp=raw_code)
            except SMTPException as e:
                logger.error(
                    f"Failed to send email verification OTP to {user.email} (user_id: {user.id}): {str(e)}"
                )
                return Response(
                    {
                        "status": "error",
                        "message": "Failed to send OTP",
                        "errors": {
                            "email": ["Unable to send OTP. Please try again later."]
                        },
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            return Response(
                {
                    "status": "success",
                    "data": {
                        "user_id": user.user_id,
                        "session_token": session_token.token,
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        # Return validation errors in the desired format
        return Response(
            {
                "status": "error",
                "detail": "Validation failed",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class HospitalSignUpView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = HospitalRegistrationSerializer
    http_method_names = ["post"]

    @swagger_auto_schema(
        request_body=HospitalRegistrationSerializer, tags=["Hospital SignUp"]
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]

            # Check for existing user at the view level
            if User.objects.filter(email=email).exists():
                return Response(
                    {
                        "status": "conflict",
                        "detail": "Existing user with this email address already exists.",
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            with transaction.atomic():
                user = serializer.save()

                # Clear all existing otp related email_verification associated with user
                OTP.objects.filter(
                    user=user, purpose="email_verification", user_type="hospital"
                ).delete()

                # Create OTP for email verification
                _, raw_code = OTP.objects.create_otp(
                    user=user, purpose="email_verification", user_type="hospital"
                )

                # Create session token
                session_token = SessionToken.objects.create_token(
                    user, purpose="email_verification"
                )

            # Send OTP via email
            try:
                send_email_verification_otp(email=user.email, otp=raw_code)
            except SMTPException as e:
                logger.error(
                    f"Failed to send email verification OTP to {user.email} (user_id: {user.id}): {str(e)}"
                )
                return Response(
                    {
                        "status": "error",
                        "message": "Failed to send OTP",
                        "errors": {
                            "email": ["Unable to send OTP. Please try again later."]
                        },
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            return Response(
                {
                    "status": "success",
                    "data": {
                        "user_id": user.user_id,
                        "session_token": session_token.token,
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        # Return validation errors in the desired format
        return Response(
            {
                "status": "error",
                "detail": "Validation failed",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class EmailLoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = EmailLoginSerializer
    http_method_names = ["post"]

    @swagger_auto_schema(request_body=EmailLoginSerializer, tags=["Login"])
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data.get("user")
            user = User.objects.get(id=user.get("id"))

            # if user.is_activated is False:
            #     return Response({
            #         "status": "error",
            #         "detail": "User account is not activated. Please contact support"
            #     }, status=status.HTTP_403_FORBIDDEN)

            data = serializer.validated_data
            return Response(
                {
                    "status": "success",
                    "detail": "Login successful",
                    "user_data": {"user_id": user.user_id, "user_type": user.user_type},
                    "token": {
                        "refresh": data.get("refresh"),
                        "access": data.get("access"),
                    },
                },
                status=status.HTTP_200_OK,
            )

        except serializers.ValidationError as e:
            # Check if non_field_errors exist (invalid credentials)
            non_field_errors = e.detail.get("non_field_errors")
            if non_field_errors:
                return Response(
                    {
                        "status": "error",
                        "detail": non_field_errors[0],
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # Otherwise, field errors
            return Response(
                {
                    "status": "error",
                    "detail": "Validation error",
                    "errors": e.detail,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {
                    "status": "error",
                    "detail": f"An unexpected error occurred: {str(e)}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LogoutAPIView(views.APIView):
    permission_classes = [IsAuthenticated, IsActivated]
    serializer_class = LogOutSerializer

    @swagger_auto_schema(request_body=LogOutSerializer, tags=["Logout"])
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()  # Invalidate the refresh token
            return Response(
                {"status": "success", "message": "Logout successful", "data": None},
                status=status.HTTP_200_OK,
            )
        except Exception:
            return Response(
                {"status": "error", "message": "Logout failed", "data": None},
                status=status.HTTP_400_BAD_REQUEST,
            )


class SignUpOTPverificationView(views.APIView):
    serializer_class = OTPVerificationSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=OTPVerificationSerializer,
        tags=["SignUp OTP"],
        operation_description="Verify sign up OTP",
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            otp = serializer.validated_data["otp"]
            session_token = serializer.validated_data["session_token"]

            # Validate session token and associated user
            token = SessionToken.objects.filter(
                token=session_token, is_used=False
            ).first()
            if not token or token.is_expired():
                return Response(
                    {
                        "status": "error",
                        "message": "Validation failed",
                        "errors": "Invalid or expired session token.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = token.user
            user_user_type = user.user_type

            # Find and validate OTP
            otp_record = (
                OTP.objects.filter(user=user, purpose="email_verification")
                .order_by("-created_at")
                .first()
            )
            if not otp_record:
                return Response(
                    {
                        "status": "error",
                        "message": "Validation failed",
                        "errors": {"otp": ["No OTP record found."]},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if otp_record.is_expired():
                return Response(
                    {
                        "status": "error",
                        "message": "Validation failed",
                        "errors": {"otp": ["Invalid OTP."]},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not otp_record.verify_otp(otp):
                return Response(
                    {
                        "status": "error",
                        "message": "Validation failed",
                        "errors": {"otp": ["Invalid OTP."]},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with transaction.atomic():
                # Mark session token as used and delete
                token.is_used = True
                token.save()
                token.delete()

                # Delete OTP record after successful verification
                otp_record.delete()
                # Activate user account
                user.is_activated = True
                user.save()

            try:
                send_onboarding_welcome(email=user.email)
            except SMTPException as e:
                logger.error(f"Failed to onboarding {user.email}: {str(e)}")
                return Response(
                    {
                        "status": "error",
                        "message": "Failed to send onboarding mail",
                        "errors": {
                            "email": ["Unable to send mail. Please try again later."]
                        },
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "status": "success",
                    "message": "Account activated successfully.",
                    "user_data": {"role": user_user_type},
                    "data": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "status": "error",
                "message": "Validation failed",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class SignUpOTPResendView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = SignUpOTPResendSerializer

    @swagger_auto_schema(
        request_body=SignUpOTPResendSerializer,
        ags=["SignUp OTP"],
        operation_description="Request for new OTP",
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "detail": "Invalid input.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        session_token = serializer.validated_data["session_token"]

        # Get session token and associated user
        token = SessionToken.objects.filter(
            token=session_token, purpose="email_verification", is_used=False
        ).first()
        if not token or token.is_expired():
            logger.error(f"Invalid or expired session token: {session_token[:10]}...")
            return Response(
                {
                    "status": "error",
                    "message": "Session failed",
                    "errors": {"session_token": ["Invalid session token."]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Check if user is already activated
        user = token.user
        if user.is_activated:
            return Response(
                {
                    "detail": "Activated user account",
                    "errors": {"account": ["Account is already activated."]},
                },
                status=status.HTTP_409_CONFLICT,
            )

        # Validate if user exists and is not activated
        if not user:
            return Response(
                {
                    "detail": "User not found for this session.",
                    "errors": {"user": ["No user associated with this session token."]},
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Generate new token
        with transaction.atomic():
            # Clear all existing otp related email_verification associated with user
            OTP.objects.filter(
                user=user, purpose="email_verification", user_type=user.user_type
            ).delete()

            # Create OTP for email verification
            _, raw_code = OTP.objects.create_otp(
                user=user, purpose="email_verification", user_type=user.user_type
            )

        # Send the new OTP via email
        try:
            send_email_verification_otp(email=user.email, otp=raw_code)
        except SMTPException as e:
            logger.error(
                f"Failed to send email verification OTP to {user.email} (user_id: {user.id}): {str(e)}"
            )
            return Response(
                {
                    "status": "error",
                    "message": "Failed to send OTP",
                    "errors": {
                        "email": ["Unable to send OTP. Please try again later."]
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "status": "success",
                "message": "New OTP sent successfully.",
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer
    http_method_names = ["post"]

    @swagger_auto_schema(
        request_body=PasswordResetRequestSerializer,
        tags=["Password Reset"],
        operation_description="Request password reset",
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            email = serializer.validated_data["email"]
            user = User.objects.get(email=email)

            # Check if user is activated
            if not user.is_activated:
                return Response(
                    {
                        "detail": "User account is not activated.",
                        "errors": {
                            "email": "Please activate your account before resetting the password."
                        },
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            with transaction.atomic():
                # Clear all existing otp related password_reset associated with user
                OTP.objects.filter(
                    user=user, purpose="password_reset", user_type=user.user_type
                ).delete()

                # Create OTP for email verification
                _, raw_code = OTP.objects.create_otp(
                    user=user, purpose="password_reset", user_type=user.user_type
                )

                # Create session token
                session_token = SessionToken.objects.create_token(
                    user, purpose="password_reset"
                )

            # Send the new OTP via email
            try:
                send_password_reset_otp(email=user.email, otp=raw_code)
            except SMTPException as e:
                logger.error(
                    f"Failed to send Password Reset OTP to {user.email} (user_id: {user.id}): {str(e)}"
                )
                return Response(
                    {
                        "status": "error",
                        "message": "Failed to send OTP",
                        "errors": {
                            "email": ["Unable to send OTP. Please try again later."]
                        },
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            return Response(
                {
                    "detail": "Password Reset OTP sent successfully to your email.",
                    "data": {"session_token": session_token.token},
                },
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            return Response(
                {
                    "detail": "User not found",
                    "errors": {"email": "No user found with this email address."},
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(
                f"Password reset request failed for {request.data.get('email')}: {str(e)}"
            )
            return Response(
                {
                    "detail": "Server error",
                    "errors": {
                        "general": "An unexpected error occurred. Please try again later."
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PasswordResetOTPResendView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetOTPResendSerializer

    @swagger_auto_schema(
        request_body=PasswordResetOTPResendSerializer,
        tags=["Password Reset"],
        operation_description="Request for Password Reset OTP",
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            session_token = serializer.validated_data["session_token"]

            # Get session token and associated user
            token = SessionToken.objects.filter(
                token=session_token, purpose="password_reset", is_used=False
            ).first()
            if not token or token.is_expired():
                logger.error(
                    f"Invalid or expired session token: {session_token[:10]}..."
                )
                return Response(
                    {
                        "status": "error",
                        "message": "Session failed",
                        "errors": {"session_token": ["Invalid session token."]},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user = token.user

            # Validate if user exists and is not activated
            if not user:
                return Response(
                    {
                        "detail": "User not found for this session.",
                        "errors": {
                            "user": ["No user associated with this session token."]
                        },
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # Generate new token
            with transaction.atomic():
                # Clear all existing otp related email_verification associated with user
                OTP.objects.filter(
                    user=user, purpose="password_reset", user_type=user.user_type
                ).delete()

                # Create OTP for email verification
                _, raw_code = OTP.objects.create_otp(
                    user=user, purpose="password_reset", user_type=user.user_type
                )

            # Send the new OTP via email
            try:
                send_password_reset_otp(email=user.email, otp=raw_code)
            except SMTPException as e:
                logger.error(
                    f"Failed to send Password Reset OTP to {user.email} (user_id: {user.id}): {str(e)}"
                )
                return Response(
                    {
                        "status": "error",
                        "message": "Failed to send OTP",
                        "errors": {
                            "email": ["Unable to send OTP. Please try again later."]
                        },
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(
                {
                    "status": "success",
                    "message": "New OTP sent successfully.",
                },
                status=status.HTTP_200_OK,
            )
        except serializers.ValidationError as e:
            # error = e.detail.get("session_to")
            return Response(
                {
                    "status": "error",
                    "detail": "Validation error",
                    "errors": e.detail,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class PasswordResetConfirmView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    @swagger_auto_schema(
        request_body=PasswordResetConfirmSerializer,
        tags=["Password Reset"],
        operation_description="Confirm Password Reset OTP",
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_password = serializer.validated_data["new_password"]
        session_token = serializer.validated_data["session"]
        otp_obj = serializer.validated_data["otp"]

        user = session_token.user
        # user_user_type = user.user_type
        user.set_password(new_password)
        user.save()

        session_token.is_used = True
        session_token.save(update_fields=["is_used"])

        otp_obj.delete()

        return Response(
            {"detail": "Password reset successful."}, status=status.HTTP_200_OK
        )


class PatientOnboardingView(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PatientOnboardingSerializer
    http_method_names = ["post"]

    @swagger_auto_schema(
        request_body=PatientOnboardingSerializer, tags=["Patient SignUp"]
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )

        try:
            serializer.is_valid(raise_exception=True)
            patient = serializer.save()
            return Response(
                {
                    "status": "success",
                    "message": "Patient onboarding successful",
                    "data": {
                        "patient_id": patient.patient_id,
                        "hospital_id": patient.hospital.hospital_id
                        if patient.hospital
                        else None,
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            error_detail = e.detail
            # If it's the "already exists" case → return 409
            if "patient" in error_detail.get("detail", "") or "already" in str(
                error_detail
            ):
                return Response(error_detail, status=status.HTTP_409_CONFLICT)
            return Response(error_detail, status=status.HTTP_400_BAD_REQUEST)

        except IntegrityError:
            return Response(
                {"detail": "User already has a patient profile."},
                status=status.HTTP_409_CONFLICT,
            )


class DoctorOnboardingAPIView(views.APIView):
    permission_classes = [IsAuthenticated, IsHospital]
    http_method_names = ["post"]

    @swagger_auto_schema(
        request_body=DoctorOnboardingSerializer, tags=["Doctor SignUp"]
    )
    def post(self, request, *args, **kwargs):
        serializer = DoctorOnboardingSerializer(
            data=request.data, context={"request": request}
        )

        try:
            with transaction.atomic():
                serializer.is_valid(raise_exception=True)
                doctor = serializer.save()

            doctor_id = doctor.doctor_id
            hospital_id = doctor.hospital.hospital_id
            response_data = {"doctor_id": doctor_id, "hospital_id": hospital_id}

            if hasattr(doctor, "_raw_password"):
                user_password = doctor._raw_password

            user_email = doctor.user.email
            hospital_name = doctor.hospital.name
            hospital_contact_email = doctor.hospital.contact_email
            hospital_address = doctor.hospital.address

            send_doctor_onboarding_welcome(
                doctor_id,
                hospital_name,
                hospital_id,
                user_email,
                user_password,
                hospital_contact_email,
                hospital_address,
            )

            return Response(
                {
                    "status": "success",
                    "message": "Doctor profile created successful and creds sent to user email",
                    "data": response_data,
                },
                status=status.HTTP_201_CREATED,
            )

        except serializers.ValidationError as e:
            # Make a mutable copy of the error detail
            error_detail = e.detail.copy()

            # Check if a specialization error exists and is a dictionary
            if "specialization" in error_detail and isinstance(
                error_detail["specialization"], dict
            ):
                specialization_errors = []
                # Iterate over the values of the specialization dictionary
                for error_list in error_detail["specialization"].values():
                    # Extend the new list with each error message
                    specialization_errors.extend(error_list)

                # Replace the original specialization error with the new list
                error_detail["specialization"] = specialization_errors

            return Response(
                {"status": "error", "detail": error_detail},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except SMTPException as e:
            logger.error(f"Failed to onboarding {request.user.email}: {str(e)}")
            return Response(
                {
                    "status": "error",
                    "message": "Failed to send onboarding mail",
                    "errors": {
                        "email": ["Unable to send mail. Please try again later."]
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class HospitalOnboardingAPIView(generics.CreateAPIView):
    queryset = Hospital.objects.all()
    serializer_class = HospitalOnboardingSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=HospitalOnboardingSerializer, tags=["Hospital SignUp"]
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(
                {"status": "conflict", "errors": e.detail},
                status=status.HTTP_409_CONFLICT,
            )

        serializer.save()
        data = serializer.data

        return Response(
            {
                "status": "success",
                "message": "Hospital created successfully.",
                "data": {"hospital_id": data.get("hospital_id", None)},
            },
            status=status.HTTP_201_CREATED,
        )


class PatientProfileUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return PatientProfileUpdateSerializer
        return PatientProfileDetailSerializer

    def get_object(self):
        # Ensure only patient updates their own profile
        if not hasattr(self.request.user, "patient"):
            raise ValidationError(
                {"detail": "No patient profile associated with this user."}
            )
        return self.request.user.patient


class DoctorProfileUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        # Use different serializers depending on the request method
        if self.request.method in ["PUT", "PATCH"]:
            return DoctorProfileUpdateSerializer
        return DoctorProfileDetailSerializer

    def get_object(self):
        # Ensure only patient updates their own profile
        if not hasattr(self.request.user, "doctor"):
            raise ValidationError(
                {"detail": "No doctor profile associated with this user."}
            )
        return self.request.user.doctor


class HospitalDoctorListAPIView(views.APIView):
    """
    Patients can:
    - GET: List doctors in their hospital
    """

    permission_classes = [IsAuthenticated, IsActivated]

    @swagger_auto_schema(
        tags=["Doctors"],
        responses={200: DoctorListSerializer(many=True)},
        operation_summary="List Doctors in Patient's Hospital or Hospital Admin's Hospital",
    )
    def get(self, request):
        hospital = None

        # If patient is logged in
        if hasattr(request.user, "patient"):
            hospital = request.user.patient.hospital

        # If hospital admin is logged in
        elif hasattr(request.user, "hospital"):
            hospital = request.user.hospital

        if not hospital:
            return Response(
                {"error": "No hospital information found for this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        doctors = Doctor.objects.filter(hospital=hospital)
        serializer = DoctorListSerializer(doctors, many=True)

        return Response(
            {
                "status": "success",
                "hospital": hospital.name,
                "doctors": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
class PatientListAPIView(views.APIView):
    """
    Patients can:
    - GET: List patients in their hospital
    """

    permission_classes = [IsAuthenticated, IsActivated]

    @swagger_auto_schema(
        tags=["Patient"],
        responses={200: PatientListSerializer(many=True)},
        operation_summary="List Patients in Doctor's Hospital or Hospital Admin's Hospital",
    )
    def get(self, request):
        hospital = None

        # If doctor is logged in
        if hasattr(request.user, "doctor"):
            hospital = request.user.doctor.hospital
            doctors = Patient.objects.filter(hospital=hospital, assigned_doctor=request.user.doctor)

        # If hospital admin is logged in
        elif hasattr(request.user, "hospital"):
            hospital = request.user.hospital
            doctors = Patient.objects.filter(hospital=hospital)

        if not hospital:
            return Response(
                {"error": "No hospital information found for this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        
        serializer = PatientListSerializer(doctors, many=True)

        return Response(
            {
                "status": "success",
                "hospital": hospital.name,
                "doctors": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

class PatientDashboardAPIView(views.APIView):
    """
    Patient Dashboard:
    - Today’s summary
    - Today’s schedule (sorted, with next pending marked)
    """

    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        tags=["Dashboard"],
        operation_summary="Patient dashboard",
    )
    def get(self, request):
        

        user = request.user
        today = date.today()

        # Active prescriptions for patient
        active_prescriptions = Prescription.objects.filter(patient__user=user)

        # Get all drugs for this patient's active prescriptions
        active_drugs = PrescriptionDrug.objects.filter(prescription__patient__user=user)

        # Serialize prescriptions with progress
        active_prescriptions_data = ActivePrescriptionSerializer(
            active_drugs, many=True
        ).data

        # Today’s logs
        logs = PrescriptionLog.objects.filter(
            prescription_drug__prescription__patient__user=user, date=today
        ).order_by("scheduled_time")

        # Mark "next" dose
        now = timezone.localtime().time()
        next_pending = None
        for log in logs:
            if not log.taken and log.scheduled_time >= now:
                next_pending = log
                break

        logs_data = []
        for log in logs:
            serializer = PatientScheduleLogSerializer(log)
            data = serializer.data
            if next_pending and log.id == next_pending.id:
                data["next"] = True
            logs_data.append(data)

        # Summary
        start_of_week = today - timedelta(days=today.weekday())
        missed_count = PrescriptionLog.objects.filter(
            prescription_drug__prescription__patient__user=user,
            date__gte=start_of_week,
            taken=False,
            date__lt=today,
        ).count()

        summary = {
            "today_meds": logs.count(),
            "missed_this_week": missed_count,
            "active_prescriptions": active_prescriptions.count(),
        }

        return Response(
            {
                "today_date": today,
                "summary": summary,
                "today_schedule": logs_data,
                "active_prescriptions": active_prescriptions_data,
            }
        )
class MarkLogTakenAPIView(views.APIView):
    """
    Patient marks a prescription log as taken.
    """

    def post(self, request, log_id):
        try:
            log = PrescriptionLog.objects.get(
                log_id=log_id,
                prescription_drug__prescription__patient__user=request.user
            )
        except PrescriptionLog.DoesNotExist:
            return Response(
                {"error": "Log not found or does not belong to you"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Already taken
        if log.taken:
            return Response(
                {"error": "This log has already been marked as taken."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check status
        if log.get_status() == "missed":
            return Response(
                {"error": "Cannot mark missed logs as taken."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mark as taken
        log.taken = True
        log.taken_at = timezone.now()
        log.save()

        return Response(
            {
                "message": "Log marked as taken successfully",
                "log": PrescriptionLogSerializer(log).data,
            },
            status=status.HTTP_200_OK,
        )