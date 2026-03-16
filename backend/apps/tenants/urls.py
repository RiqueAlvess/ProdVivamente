from django.urls import path
from . import views

urlpatterns = [
    path('', views.EmpresaListCreateView.as_view(), name='empresa-list-create'),
    path('minha/', views.MinhaEmpresaView.as_view(), name='minha-empresa'),
    path('setup/', views.EmpresaSetupView.as_view(), name='empresa-setup'),
    path('<int:pk>/', views.EmpresaDetailView.as_view(), name='empresa-detail'),
]
