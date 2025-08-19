from django.urls import path

from .views import UserSignUpView

urlpatterns = [
    path('v1/user/signup/', UserSignUpView.as_view(), name='signup'),
]
