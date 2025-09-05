from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import HospitalListViewSet, HospitalProfileUpdateView

router = DefaultRouter()
router.register(r'hospitals', HospitalListViewSet)

urlpatterns = [
    path('v1/', include(router.urls)),
    path('v1/hospital/profile/', HospitalProfileUpdateView.as_view(), name='hospital-profile'),
]