from django.urls import path
from . import views

urlpatterns = [
    # JWT auth
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token-obtain'),
    path('token/refresh/', views.CustomTokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # Current user
    path('me/', views.MeView.as_view(), name='me'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),

    # User management (admin only — tenant-scoped)
    path('users/', views.UserListCreateView.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),

    # Audit log (admin only)
    path('audit-log/', views.AuditLogListView.as_view(), name='audit-log'),
]
