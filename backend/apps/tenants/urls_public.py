"""
Public-schema URL conf for tenant/domain management.
Included in config/urls_public.py.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.EmpresaListCreateView.as_view(), name='empresa-list'),
    path('<int:pk>/', views.EmpresaDetailView.as_view(), name='empresa-detail'),
    path('slug/<slug:slug>/', views.EmpresaBySlugView.as_view(), name='empresa-by-slug'),
    path('domains/', views.DomainListCreateView.as_view(), name='domain-list'),
    path('domains/<int:pk>/', views.DomainDetailView.as_view(), name='domain-detail'),
]
