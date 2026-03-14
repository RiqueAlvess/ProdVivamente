from django.urls import path
from . import views

urlpatterns = [
    # Planos de Ação
    path('planos/', views.PlanoAcaoListCreateView.as_view(), name='plano-list'),
    path('planos/<int:pk>/', views.PlanoAcaoDetailView.as_view(), name='plano-detail'),
    path('planos/generate-ai/', views.GenerateAIActionPlanView.as_view(), name='plano-generate-ai'),

    # NR-1 Checklist
    path('checklist/<int:campaign_id>/', views.ChecklistNR1View.as_view(), name='checklist-nr1'),
    path('checklist/items/<int:item_id>/', views.ChecklistItemUpdateView.as_view(), name='checklist-item-update'),
    path('checklist/items/<int:item_id>/evidencias/', views.EvidenceUploadView.as_view(), name='evidence-upload'),

    # Evidence management
    path('evidencias/<int:evidencia_id>/', views.EvidenceDeleteView.as_view(), name='evidence-delete'),
]
