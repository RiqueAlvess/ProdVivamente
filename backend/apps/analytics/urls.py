from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('comparison/', views.CampaignComparisonView.as_view(), name='campaign-comparison'),
    path('risk-matrix/<int:campaign_id>/', views.PsychosocialRiskMatrixView.as_view(), name='risk-matrix'),
    path('sector-analysis/generate/', views.GenerateSectorAnalysisView.as_view(), name='sector-analysis-generate'),
    path('sector-analysis/<int:pk>/', views.SectorAnalysisDetailView.as_view(), name='sector-analysis-detail'),
    path('rebuild/', views.RebuildAnalyticsView.as_view(), name='rebuild-analytics'),
    path('export/excel/<int:campaign_id>/', views.ExportDashboardExcelView.as_view(), name='export-excel'),
    path('export/risk-matrix/<int:campaign_id>/', views.ExportRiskMatrixExcelView.as_view(), name='export-risk-matrix'),
]
