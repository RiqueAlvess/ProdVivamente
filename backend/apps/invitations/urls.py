from django.urls import path
from . import views

urlpatterns = [
    path('', views.InvitationListView.as_view(), name='invitation-list'),
    path('import/', views.ImportCSVView.as_view(), name='import-csv'),
    path('campaigns/<int:campaign_id>/dispatch/', views.DispatchEmailsView.as_view(), name='dispatch-emails'),
    path('campaigns/<int:campaign_id>/stats/', views.InvitationStatsView.as_view(), name='invitation-stats'),
]
