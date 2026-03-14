from django.urls import path
from . import views

urlpatterns = [
    path('tasks/', views.TaskListView.as_view(), name='task-list'),
    path('tasks/<int:pk>/', views.TaskStatusView.as_view(), name='task-status'),
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/unread-count/', views.UnreadNotificationCountView.as_view(), name='notification-unread-count'),
    path('notifications/mark-all-read/', views.NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
    path('notifications/<int:pk>/read/', views.NotificationMarkReadView.as_view(), name='notification-mark-read'),
]
