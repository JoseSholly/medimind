import logging
from smtplib import SMTPException

from django.contrib.auth import get_user_model
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status, views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import OTP, SessionToken
from .serializers import (
    DoctorRegistrationSerializer,
    EmailLoginSerializer,
    HospitalRegistrationSerializer,
    PatientRegistrationSerializer,
)
from .utils import send_email_verification_otp

logger = logging.getLogger(__name__)

User = get_user_model()


class PatientSignUpView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = PatientRegistrationSerializer
    http_method_names = ['post']

    @swagger_auto_schema(request_body=PatientRegistrationSerializer, tags=["Patient SignUp"])
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
                    status=status.HTTP_409_CONFLICT
                )

            with transaction.atomic():
                user =serializer.save()

                # Clear all existing otp related email_verification associated with user
                OTP.objects.filter(user=user, purpose='email_verification', user_type="patient").delete()

                # Create OTP for email verification
                _, raw_code = OTP.objects.create_otp(user=user, purpose="email_verification", user_type="patient")

                # Create session token
                session_token = SessionToken.objects.create_token(user, purpose="email_verification", expiry_minutes=10)
            # Send OTP via email
            try:
                send_email_verification_otp(email=user.email, otp=raw_code)
            except SMTPException as e:
                logger.error(f"Failed to send email verification OTP to {user.email} (user_id: {user.id}): {str(e)}")
                return Response(
                    {
                        "status": "error",
                        "message": "Failed to send OTP",
                        "errors": {"email": ["Unable to send OTP. Please try again later."]}
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            return Response(
                {
                    "status": "success",
                    "data": {
                        "user_id": user.user_id,
                        "session_token": session_token.token
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
    http_method_names = ['post']

    @swagger_auto_schema(request_body=DoctorRegistrationSerializer, tags=["Doctor SignUp"])
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
                    status=status.HTTP_409_CONFLICT
                )

            with transaction.atomic():
                user =serializer.save()

                # Clear all existing otp related email_verification associated with user
                OTP.objects.filter(user=user, purpose='email_verification', user_type="doctor").delete()

                # Create OTP for email verification
                _, raw_code = OTP.objects.create_otp(user=user, purpose="email_verification", user_type="doctor")

                # Create session token
                session_token = SessionToken.objects.create_token(user, purpose="email_verification", expiry_minutes=10)
            # Send OTP via email
            try:
                send_email_verification_otp(email=user.email, otp=raw_code)
            except SMTPException as e:
                logger.error(f"Failed to send email verification OTP to {user.email} (user_id: {user.id}): {str(e)}")
                return Response(
                    {
                        "status": "error",
                        "message": "Failed to send OTP",
                        "errors": {"email": ["Unable to send OTP. Please try again later."]}
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
    http_method_names = ['post']

    @swagger_auto_schema(request_body=HospitalRegistrationSerializer, tags=["Hospital SignUp"])
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
                    status=status.HTTP_409_CONFLICT
                )

            with transaction.atomic():
                user =serializer.save()

                # Clear all existing otp related email_verification associated with user
                OTP.objects.filter(user=user, purpose='email_verification', user_type="hospital").delete()

                # Create OTP for email verification
                _, raw_code = OTP.objects.create_otp(user=user, purpose="email_verification", user_type="hospital")

                # Create session token
                session_token = SessionToken.objects.create_token(user, purpose="email_verification", expiry_minutes=10)
            
            # Send OTP via email
            try:
                send_email_verification_otp(email=user.email, otp=raw_code)
            except SMTPException as e:
                logger.error(f"Failed to send email verification OTP to {user.email} (user_id: {user.id}): {str(e)}")
                return Response(
                    {
                        "status": "error",
                        "message": "Failed to send OTP",
                        "errors": {"email": ["Unable to send OTP. Please try again later."]}
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
    http_method_names = ['post']


    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data.get("user")
            user = User.objects.get(id=user.get('id'))


            
            # if user.is_activated is False:
            #     return Response({
            #         "status": "error",
            #         "detail": "User account is not activated. Please contact support"
            #     }, status=status.HTTP_403_FORBIDDEN)
            
            data = serializer.validated_data
            return Response({
                "status": "success",
                "detail": "Login successful",
                "user_data": {
                    "user_id": user.user_id,
                    "user_type": user.user_type
                },
                "token": {
                    "refresh": data.get("refresh"),
                    "access": data.get("access"),
                },
            }, status=status.HTTP_200_OK)
        
        except serializers.ValidationError as e:
            # Check if non_field_errors exist (invalid credentials)
            non_field_errors = e.detail.get("non_field_errors")
            if non_field_errors:
                return Response({
                    "status": "error",
                    "detail": non_field_errors[0],
                }, status=status.HTTP_401_UNAUTHORIZED)

            # Otherwise, field errors
            return Response({
                "status": "error",
                "detail": "Validation error",
                "errors": e.detail,
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": "error",
                "detail": f"An unexpected error occurred: {str(e)}",
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)