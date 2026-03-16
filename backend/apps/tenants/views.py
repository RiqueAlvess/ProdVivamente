import logging
import secrets
import string

from django.contrib.auth.models import User
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Empresa
from .serializers import EmpresaSerializer, EmpresaCreateSerializer

logger = logging.getLogger(__name__)


def _generate_password(length=14):
    alphabet = string.ascii_letters + string.digits + '!@#$'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class EmpresaListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/empresas/ — lista empresas (superadmin vê todas; RH vê só a sua)
    POST /api/empresas/ — cria empresa (superadmin apenas)
    """
    serializer_class = EmpresaSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Empresa.objects.all()
        # Usuário comum vê apenas sua própria empresa
        try:
            empresa = user.profile.empresa
            if empresa:
                return Empresa.objects.filter(pk=empresa.pk, ativo=True)
        except Exception:
            pass
        return Empresa.objects.none()


class EmpresaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/empresas/<id>/"""
    serializer_class = EmpresaSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Empresa.objects.all()
        try:
            empresa = user.profile.empresa
            if empresa:
                return Empresa.objects.filter(pk=empresa.pk)
        except Exception:
            pass
        return Empresa.objects.none()


class EmpresaSetupView(APIView):
    """
    POST /api/empresas/setup/

    Endpoint all-in-one (superadmin) que:
      1. Cria a Empresa
      2. Provisiona o usuário admin RH inicial
      3. Retorna as credenciais (exibidas apenas uma vez)
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        serializer = EmpresaCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        empresa = Empresa.objects.create(
            nome=data['nome'],
            cnpj=data['cnpj'],
            total_funcionarios=data.get('total_funcionarios', 0),
            cnae=data.get('cnae', ''),
            cnae_descricao=data.get('cnae_descricao', ''),
            admin_email=data['admin_email'],
        )

        password = data.get('admin_password') or _generate_password()
        try:
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
            UserProfile.objects.create(user=admin_user, role='rh', empresa=empresa)
        except Exception as e:
            logger.error('Falha ao provisionar admin para %s: %s', empresa.nome, e)
            return Response(
                {
                    'empresa': EmpresaSerializer(empresa).data,
                    'admin_user': None,
                    'aviso': f'Empresa criada, mas falha ao criar usuário admin: {e}',
                },
                status=status.HTTP_207_MULTI_STATUS,
            )

        return Response(
            {
                'empresa': EmpresaSerializer(empresa).data,
                'admin_user': {
                    'email': admin_user.email,
                    'username': admin_user.username,
                    'password': password,
                    'nota': 'Guarde esta senha — ela não será exibida novamente.',
                },
            },
            status=status.HTTP_201_CREATED,
        )


class MinhaEmpresaView(APIView):
    """
    GET  /api/empresas/minha/ — retorna a empresa do usuário logado
    PATCH/PUT                  — atualiza dados da empresa (admin apenas)
    """
    permission_classes = [permissions.IsAuthenticated]

    def _get_empresa(self, user):
        if user.is_staff or user.is_superuser:
            empresa_id = self.request.query_params.get('empresa_id')
            if empresa_id:
                return Empresa.objects.filter(pk=empresa_id).first()
        try:
            return user.profile.empresa
        except Exception:
            return None

    def get(self, request):
        empresa = self._get_empresa(request.user)
        if not empresa:
            return Response({'error': 'Empresa não encontrada'}, status=status.HTTP_404_NOT_FOUND)
        return Response(EmpresaSerializer(empresa).data)

    def patch(self, request):
        return self._update(request, partial=True)

    def put(self, request):
        return self._update(request, partial=False)

    def _update(self, request, partial):
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'Permissão negada'}, status=status.HTTP_403_FORBIDDEN)
        empresa = self._get_empresa(request.user)
        if not empresa:
            return Response({'error': 'Empresa não encontrada'}, status=status.HTTP_404_NOT_FOUND)
        serializer = EmpresaSerializer(empresa, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
