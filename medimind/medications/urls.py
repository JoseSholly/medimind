from django.urls import path

from .views import PrescriptionCreateAPIView

urlpatterns = [
    
    path(
        "v1/prescription/create/",
        PrescriptionCreateAPIView.as_view(),
        name="create-prescription",
    ),
]
