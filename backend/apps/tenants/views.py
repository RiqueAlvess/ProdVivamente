import logging

from django.db import connection
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Domain, Empresa
from .serializers import (
    CurrentTenantSerializer,
    DomainSerializer,
    EmpresaPublicSerializer,
    EmpresaSerializer,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public-schema views (used in urls_public.py)
# ---------------------------------------------------------------------------

class EmpresaListCreateView(generics.ListCreateAPIView):
    """List and create companies (superadmin only for write). Public schema."""
    serializer_class = EmpresaSerializer
    queryset = Empresa.objects.all()

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return Empresa.objects.all()
        return Empresa.objects.filter(ativo=True)


class EmpresaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a company. Public schema."""
    serializer_class = EmpresaSerializer
    queryset = Empresa.objects.all()

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]


class EmpresaBySlugView(APIView):
    """Public endpoint to look up a company by slug (for branding)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        try:
            empresa = Empresa.objects.get(slug=slug, ativo=True)
            return Response(EmpresaPublicSerializer(empresa).data)
        except Empresa.DoesNotExist:
            return Response({'error': 'Empresa não encontrada'}, status=404)


class DomainListCreateView(generics.ListCreateAPIView):
    """List and create domains for tenants. Admin only."""
    serializer_class = DomainSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Domain.objects.select_related('tenant').all()


class DomainDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a domain. Admin only."""
    serializer_class = DomainSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Domain.objects.all()


# ---------------------------------------------------------------------------
# Tenant-schema views (used in urls.py / ROOT_URLCONF)
# ---------------------------------------------------------------------------

class CurrentTenantView(APIView):
    """
    GET  /api/tenant/  — return current tenant info (from connection.tenant)
    PATCH/PUT          — update current tenant settings (admin only)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tenant = connection.tenant
        return Response(CurrentTenantSerializer(tenant).data)

    def patch(self, request):
        return self._update(request, partial=True)

    def put(self, request):
        return self._update(request, partial=False)

    def _update(self, request, partial):
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'Permissão negada'}, status=status.HTTP_403_FORBIDDEN)
        tenant = connection.tenant
        serializer = CurrentTenantSerializer(tenant, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
