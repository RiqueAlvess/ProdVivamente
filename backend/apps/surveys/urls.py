from django.urls import path
from . import views

urlpatterns = [
    path('dimensoes/', views.DimensaoListView.as_view(), name='dimensao-list'),
    path('perguntas/', views.PerguntaListView.as_view(), name='pergunta-list'),
    path('campaigns/', views.CampaignListCreateView.as_view(), name='campaign-list'),
    path('campaigns/<int:pk>/', views.CampaignDetailView.as_view(), name='campaign-detail'),
    path('campaigns/<int:pk>/activate/', views.CampaignActivateView.as_view(), name='campaign-activate'),
    path('campaigns/<int:pk>/close/', views.CampaignCloseView.as_view(), name='campaign-close'),
    path('fatores-risco/', views.FatorRiscoListView.as_view(), name='fator-risco-list'),
    path('categorias-risco/', views.CategoriaFatorRiscoListView.as_view(), name='categoria-risco-list'),
]
