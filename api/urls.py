from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet, CycleViewSet, LarvaHarvestViewSet, SensorDataViewSet, WasteViewSet, EggHarvestViewSet, PhaseViewSet, YoutubeViewSet, NotificationViewSet, nameIoTViewSet, IoTDataViewSet

router = DefaultRouter()
router.register(r'cycles', CycleViewSet)
router.register(r'wastes', WasteViewSet)
router.register(r'phases', PhaseViewSet)
router.register(r'larva_harvests', LarvaHarvestViewSet)
router.register(r'egg_harvests', EggHarvestViewSet)
router.register(r'articles', ArticleViewSet)
router.register(r'youtube', YoutubeViewSet)
router.register(r'notifikasi', NotificationViewSet)
router.register(r'sensor-data', SensorDataViewSet)
router.register(r'iot-names', nameIoTViewSet)
router.register(r'iot-data', IoTDataViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
