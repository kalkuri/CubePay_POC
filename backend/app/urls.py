
from django.urls import path
from .views import GenerateTokenView, QueueListView, ScanTokenView, ReportView,GetTokenView,ValidateTokenView,GenerateReportView,SummaryReportView

urlpatterns = [
    path('generate-token/', GenerateTokenView.as_view(), name='generate_token'),
    path('get-token/',GetTokenView.as_view(),name='get-token'),
    path('queues/', QueueListView.as_view(), name='queue-list'),
    path('validate-token/',ValidateTokenView.as_view(),name = 'validate-token'),
    path('scan-token/', ScanTokenView.as_view(), name='scan-token'),
    path('report/', ReportView.as_view(), name='report'),
    path('summary-report/', SummaryReportView.as_view(), name='summary-report'),
    path('generate-report/',GenerateReportView.as_view(),name='generate-report')
]

