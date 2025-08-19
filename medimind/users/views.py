import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status, views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import EmailLoginSerializer, UserRegistrationSerializer

logger = logging.getLogger(__name__)

User = get_user_model()


class UserSignUpView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
    http_method_names = ['post']

    @swagger_auto_schema(request_body=UserRegistrationSerializer, tags=["SignUp"])
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

            return Response(
                {
                    "status": "success",
                    "data": {
                        "user_id": user.id,
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
                    "id": user.get('id'),
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