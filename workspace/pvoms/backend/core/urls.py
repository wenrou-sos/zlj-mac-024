from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("stations", views.StationViewSet, basename="station")
router.register("devices", views.DeviceViewSet, basename="device")
router.register("alarms", views.AlarmViewSet, basename="alarm")
router.register("inspections", views.InspectionOrderViewSet, basename="inspection")
router.register("cleanings", views.CleaningPlanViewSet, basename="cleaning")
router.register("defects", views.DefectRecordViewSet, basename="defect")

urlpatterns = [
    path("", include(router.urls)),
    path("overview/", views.overview, name="overview"),
]
