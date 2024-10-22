from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EntryPointView, PilgrimViewSet, ReportView

router = DefaultRouter()
router.register(r'pilgrims', PilgrimViewSet)

urlpatterns = [
    path('', include(router.urls)),  # This includes routes for the PilgrimViewSet
    path('entry/<int:entry_level>/', EntryPointView.as_view(), name='entry-point'),  # This is your entry point
    path('report/', ReportView.as_view(), name='generate-report'),
]
