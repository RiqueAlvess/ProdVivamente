from django.urls import path
from . import views
from . import campaign_nested_views as nested

urlpatterns = [
    # ─── Core survey resources ───────────────────────────────────────────────
    path('dimensoes/', views.DimensaoListView.as_view(), name='dimensao-list'),
    path('perguntas/', views.PerguntaListView.as_view(), name='pergunta-list'),
    path('fatores-risco/', views.FatorRiscoListView.as_view(), name='fator-risco-list'),
    path('categorias-risco/', views.CategoriaFatorRiscoListView.as_view(), name='categoria-risco-list'),

    # ─── Campaign CRUD ───────────────────────────────────────────────────────
    path('campaigns/', views.CampaignListCreateView.as_view(), name='campaign-list'),
    path('campaigns/<int:pk>/', views.CampaignDetailView.as_view(), name='campaign-detail'),
    path('campaigns/<int:pk>/activate/', views.CampaignActivateView.as_view(), name='campaign-activate'),
    path('campaigns/<int:pk>/close/', views.CampaignCloseView.as_view(), name='campaign-close'),

    # ─── Campaign → Invitations (nested) ─────────────────────────────────────
    path('campaigns/<int:pk>/invitations/',
         nested.CampaignInvitationListCreateView.as_view(), name='campaign-invitation-list'),
    path('campaigns/<int:pk>/invitations/import/',
         nested.CampaignInvitationImportView.as_view(), name='campaign-invitation-import'),
    path('campaigns/<int:pk>/invitations/template/',
         nested.CampaignInvitationTemplateView.as_view(), name='campaign-invitation-template'),
    path('campaigns/<int:pk>/invitations/send_all/',
         nested.CampaignInvitationSendAllView.as_view(), name='campaign-invitation-send-all'),
    path('campaigns/<int:pk>/invitations/<int:inv_id>/',
         nested.CampaignInvitationDeleteView.as_view(), name='campaign-invitation-delete'),

    # ─── Campaign → NR-1 Checklist (nested) ──────────────────────────────────
    path('campaigns/<int:pk>/checklist/',
         nested.CampaignChecklistView.as_view(), name='campaign-checklist'),
    path('campaigns/<int:pk>/checklist/create/',
         nested.CampaignChecklistCreateView.as_view(), name='campaign-checklist-create'),
    path('campaigns/<int:pk>/checklist/items/<int:item_id>/',
         nested.CampaignChecklistItemUpdateView.as_view(), name='campaign-checklist-item'),
    path('campaigns/<int:pk>/checklist/items/<int:item_id>/upload_evidence/',
         nested.CampaignChecklistItemEvidenceView.as_view(), name='campaign-checklist-evidence'),

    # ─── Campaign → Action Plans (nested) ────────────────────────────────────
    path('campaigns/<int:pk>/actions/',
         nested.CampaignActionsView.as_view(), name='campaign-actions'),
    path('campaigns/<int:pk>/actions/<int:action_id>/',
         nested.CampaignActionDetailView.as_view(), name='campaign-action-detail'),
    path('campaigns/<int:pk>/actions/export_word/',
         nested.CampaignActionsExportWordView.as_view(), name='campaign-actions-export'),
]
