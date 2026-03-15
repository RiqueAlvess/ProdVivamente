"""
Accounts views - JWT auth only. NO registration endpoint.
Admin creates users via Django admin.
"""
import logging

from django.contrib.auth.models import User
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import AuditLog
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer,
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


@method_decorator(ratelimit(key='ip', rate='3/m', method='POST', block=True), name='post')
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/auth/token/
    Rate limited: 3 requests/minute per IP.
    Logs successful and failed login attempts.
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            logger.warning(
                'Failed login attempt for email=%s from IP=%s',
                request.data.get('email', ''),
                get_client_ip(request),
            )
            raise

        user = serializer.user
        ip = get_client_ip(request)
        ua = get_user_agent(request)

        AuditLog.objects.create(
            user=user,
            acao='login',
            descricao=f'Login via JWT - {user.username}',
            ip=ip,
            user_agent=ua,
        )

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


@method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True), name='post')
class CustomTokenRefreshView(TokenRefreshView):
    """POST /api/auth/token/refresh/"""
    pass


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blacklists the refresh token.
    """
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

        AuditLog.objects.create(
            user=user,
            acao='logout',
            descricao=f'Logout - {user.username}',
            ip=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        return Response({'detail': 'Logout realizado com sucesso.'}, status=status.HTTP_200_OK)


class MeView(generics.RetrieveUpdateAPIView):
    """
    GET /api/auth/me/ - Get current user info with profile
    PATCH /api/auth/me/ - Update basic profile info
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        return UserSerializer

    def update(self, request, *args, **kwargs):
        # Only allow updating safe fields
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
    """GET /api/auth/audit-log/ - Admin only"""
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        qs = AuditLog.objects.select_related('user').all()
        acao = self.request.query_params.get('acao')
        if acao:
            qs = qs.filter(acao=acao)
        return qs
