from django.urls import path

from .views import PrescriptionCreateAPIView, PrescriptionDetailView

urlpatterns = [
    path(
        "v1/prescription/create/",
        PrescriptionCreateAPIView.as_view(),
        name="create-prescription",
    ),
    path(
        "v1/prescription/detail/<str:prescription_id>/<str:drug_id>/",
        PrescriptionDetailView.as_view(),
        name="prescription-detail",
    ),
]
