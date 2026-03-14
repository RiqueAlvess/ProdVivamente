from django.urls import path
from . import views

urlpatterns = [
    path('unidades/', views.UnidadeListCreateView.as_view(), name='unidade-list'),
    path('unidades/<int:pk>/', views.UnidadeDetailView.as_view(), name='unidade-detail'),
    path('setores/', views.SetorListCreateView.as_view(), name='setor-list'),
    path('setores/<int:pk>/', views.SetorDetailView.as_view(), name='setor-detail'),
    path('cargos/', views.CargoListCreateView.as_view(), name='cargo-list'),
    path('cargos/<int:pk>/', views.CargoDetailView.as_view(), name='cargo-detail'),
]
