import logging
import secrets
import string

from django.contrib.auth.models import User
from django.db import connection
from django_tenants.utils import tenant_context
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Domain, Empresa
from .serializers import (
    CurrentTenantSerializer,
    DomainSerializer,
    EmpresaPublicSerializer,
    EmpresaSerializer,
    TenantSetupSerializer,
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


class TenantSetupView(APIView):
    """
    POST /api/tenants/setup/

    All-in-one endpoint (superadmin only) that:
      1. Creates the Empresa (auto-creates PostgreSQL schema)
      2. Creates the primary Domain
      3. Provisions the initial RH admin user inside the new schema
      4. Returns the credentials (shown only once)
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        serializer = TenantSetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # 1. Create Empresa (TenantMixin auto-creates the PostgreSQL schema)
        empresa = Empresa.objects.create(
            schema_name=data['schema_name'],
            nome=data['nome'],
            cnpj=data['cnpj'],
            total_funcionarios=data.get('total_funcionarios', 0),
            cnae=data.get('cnae', ''),
            cnae_descricao=data.get('cnae_descricao', ''),
            admin_email=data['admin_email'],
        )

        # 2. Create primary Domain
        domain = Domain.objects.create(
            domain=data['domain'],
            tenant=empresa,
            is_primary=True,
        )

        # 3. Provision initial RH admin inside the new schema
        password = data.get('admin_password') or _generate_password()
        try:
            with tenant_context(empresa):
                from apps.accounts.models import UserProfile

                base_username = data['admin_email'].split('@')[0]
                username = base_username
                n = 1
                while User.objects.filter(username=username).exists():
                    username = f'{base_username}{n}'
                    n += 1

                admin_user = User.objects.create_user(
                    username=username,
                    email=data['admin_email'],
                    password=password,
                    first_name=data.get('admin_first_name', 'Admin'),
                    last_name=data.get('admin_last_name', ''),
                    is_staff=True,
                    is_active=True,
                )
                UserProfile.objects.create(user=admin_user, role='rh')
        except Exception as e:
            logger.error('Falha ao provisionar admin para %s: %s', empresa.schema_name, e)
            return Response(
                {
                    'empresa': EmpresaSerializer(empresa).data,
                    'domain': DomainSerializer(domain).data,
                    'admin_user': None,
                    'warning': f'Tenant criado, mas falha ao criar usuário admin: {e}',
                },
                status=status.HTTP_207_MULTI_STATUS,
            )

        return Response(
            {
                'empresa': EmpresaSerializer(empresa).data,
                'domain': DomainSerializer(domain).data,
                'admin_user': {
                    'email': admin_user.email,
                    'username': admin_user.username,
                    'password': password,
                    'note': 'Guarde esta senha — ela não será exibida novamente.',
                },
            },
            status=status.HTTP_201_CREATED,
        )


def _generate_password(length=14):
    alphabet = string.ascii_letters + string.digits + '!@#$'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


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
