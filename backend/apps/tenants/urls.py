from django.urls import path
from . import views

urlpatterns = [
    path('', views.EmpresaListCreateView.as_view(), name='empresa-list'),
    path('<int:pk>/', views.EmpresaDetailView.as_view(), name='empresa-detail'),
    path('slug/<slug:slug>/', views.EmpresaBySlugView.as_view(), name='empresa-by-slug'),
]
