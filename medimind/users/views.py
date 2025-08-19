import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers, status, views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import UserRegistrationSerializer

logger = logging.getLogger(__name__)

User = get_user_model()


class UserSignUpView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

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
                "message": "Validation failed",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )