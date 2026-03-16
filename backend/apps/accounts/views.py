"""
Accounts views - autenticação JWT.
Sem endpoint de registro — apenas admin cria usuários.
"""
import logging

from django.contrib.auth.models import User
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import AuditLog, UserProfile
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer,
    CreateUserSerializer,
    ChangePasswordSerializer,
    AuditLogSerializer,
)

logger = logging.getLogger(__name__)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def get_user_agent(request):
    return request.META.get('HTTP_USER_AGENT', '')[:500]


def _get_empresa_do_usuario(user):
    """Retorna a Empresa do usuário logado, ou None."""
    try:
        return user.profile.empresa
    except Exception:
        return None


@method_decorator(ratelimit(key='ip', rate='3/m', method='POST', block=True), name='post')
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/auth/token/
    Rate limitado: 3 requisições/minuto por IP.
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            logger.warning(
                'Tentativa de login falhou para email=%s do IP=%s',
                request.data.get('email', ''),
                get_client_ip(request),
            )
            raise

        user = serializer.user
        empresa = _get_empresa_do_usuario(user)

        try:
            AuditLog.objects.create(
                user=user,
                empresa=empresa,
                acao='login',
                descricao=f'Login via JWT - {user.username}',
                ip=get_client_ip(request),
                user_agent=get_user_agent(request),
            )
        except Exception:
            pass

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


@method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True), name='post')
class CustomTokenRefreshView(TokenRefreshView):
    """POST /api/auth/token/refresh/"""
    pass


class LogoutView(APIView):
    """POST /api/auth/logout/ — invalida o refresh token."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        empresa = _get_empresa_do_usuario(user)

        try:
            AuditLog.objects.create(
                user=user,
                empresa=empresa,
                acao='logout',
                descricao=f'Logout - {user.username}',
                ip=get_client_ip(request),
                user_agent=get_user_agent(request),
            )
        except Exception:
            pass

        return Response({'detail': 'Logout realizado com sucesso.'}, status=status.HTTP_200_OK)


class MeView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/auth/me/ — dados do usuário logado
    PATCH /api/auth/me/ — atualiza dados básicos do perfil
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        allowed_fields = {'first_name', 'last_name'}
        data = {k: v for k, v in request.data.items() if k in allowed_fields}
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class ChangePasswordView(APIView):
    """POST /api/auth/change-password/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'old_password': 'Senha atual incorreta'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({'detail': 'Senha alterada com sucesso.'}, status=status.HTTP_200_OK)


class AuditLogListView(generics.ListAPIView):
    """GET /api/auth/audit-log/ — apenas admin"""
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        user = self.request.user
        qs = AuditLog.objects.select_related('user').all()
        # Admin comum vê apenas logs da sua empresa
        if not user.is_superuser:
            empresa = _get_empresa_do_usuario(user)
            if empresa:
                qs = qs.filter(empresa=empresa)
        acao = self.request.query_params.get('acao')
        if acao:
            qs = qs.filter(acao=acao)
        return qs


class UserListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/auth/users/ — lista usuários da empresa (admin apenas)
    POST /api/auth/users/ — cria usuário na empresa (admin apenas)
    """
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        user = self.request.user
        qs = User.objects.select_related('profile').filter(is_superuser=False).order_by('email')
        if not user.is_superuser:
            empresa = _get_empresa_do_usuario(user)
            if empresa:
                qs = qs.filter(profile__empresa=empresa)
        return qs

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateUserSerializer
        return UserSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['empresa'] = _get_empresa_do_usuario(self.request.user)
        return ctx

    def create(self, request, *args, **kwargs):
        serializer = CreateUserSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/auth/users/<id>/ — detalhe do usuário
    PATCH  /api/auth/users/<id>/ — atualiza dados
    DELETE /api/auth/users/<id>/ — desativa usuário (soft delete)
    """
    permission_classes = [permissions.IsAdminUser]
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        qs = User.objects.select_related('profile').filter(is_superuser=False)
        if not user.is_superuser:
            empresa = _get_empresa_do_usuario(user)
            if empresa:
                qs = qs.filter(profile__empresa=empresa)
        return qs

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'detail': 'Usuário desativado.'}, status=status.HTTP_200_OK)
