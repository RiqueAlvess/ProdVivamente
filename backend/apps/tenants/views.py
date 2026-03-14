import logging

from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Empresa
from .serializers import EmpresaSerializer, EmpresaPublicSerializer

logger = logging.getLogger(__name__)


class EmpresaListCreateView(generics.ListCreateAPIView):
    """List and create companies. Admin only for write."""
    serializer_class = EmpresaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Empresa.objects.all()
        if hasattr(user, 'profile'):
            return user.profile.empresas.filter(ativo=True)
        return Empresa.objects.none()

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]


class EmpresaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a company."""
    serializer_class = EmpresaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Empresa.objects.all()
        if hasattr(user, 'profile'):
            return user.profile.empresas.filter(ativo=True)
        return Empresa.objects.none()

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
            serializer = EmpresaPublicSerializer(empresa)
            return Response(serializer.data)
        except Empresa.DoesNotExist:
            return Response({'error': 'Empresa não encontrada'}, status=404)
