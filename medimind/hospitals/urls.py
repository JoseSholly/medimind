from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import HospitalListViewSet

router = DefaultRouter()
router.register(r'hospitals', HospitalListViewSet)

urlpatterns = [
    path('v1/', include(router.urls)),
]