"""
Tenant-schema URL conf (included in ROOT_URLCONF → config/urls.py).
Only the current-tenant endpoint lives here; empresa/domain management
is handled in the public schema (config/urls_public.py).
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.CurrentTenantView.as_view(), name='current-tenant'),
]
