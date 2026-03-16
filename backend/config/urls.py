"""
VIVAMENTE 360º — URL Configuration.
"""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView as SpectacularSwaggerUIView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include([
        path('auth/', include('apps.accounts.urls')),
        path('empresas/', include('apps.tenants.urls')),
        path('structure/', include('apps.structure.urls')),
        path('surveys/', include('apps.surveys.urls')),
        path('campaigns/', include('apps.surveys.urls')),    # alias para compatibilidade frontend
        path('invitations/', include('apps.invitations.urls')),
        path('responses/', include('apps.responses.urls')),
        path('actions/', include('apps.actions.urls')),
        path('analytics/', include('apps.analytics.urls')),
        path('core/', include('apps.core.urls')),
    ])),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerUIView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
