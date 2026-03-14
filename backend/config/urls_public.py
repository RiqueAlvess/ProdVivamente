"""
VIVAMENTE 360º — Public Schema URL Configuration (PUBLIC_SCHEMA_URLCONF).
Served when the request matches no tenant domain (public schema).
Handles tenant/domain management and public branding lookups.
"""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerUIView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include([
        path('tenants/', include('apps.tenants.urls_public')),  # Empresa + Domain CRUD
        path('auth/', include('apps.accounts.urls')),           # login/refresh from public domain
    ])),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerUIView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
