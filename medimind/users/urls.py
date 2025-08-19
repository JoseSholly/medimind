from django.urls import path

from .views import EmailLoginView, UserSignUpView

urlpatterns = [
    path('v1/user/signup/', UserSignUpView.as_view(), name='signup'),
    path('v1/user/login/', EmailLoginView.as_view(), name='signin'),
]
