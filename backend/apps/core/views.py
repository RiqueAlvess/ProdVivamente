"""
Core views - Task status, notifications.
"""
import logging

from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import TaskQueue, UserNotification
from .serializers import TaskQueueSerializer, UserNotificationSerializer

logger = logging.getLogger(__name__)


class TaskStatusView(generics.RetrieveAPIView):
    """GET /api/core/tasks/{id}/ - Poll task status"""
    serializer_class = TaskQueueSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return TaskQueue.objects.all()
        return TaskQueue.objects.filter(user=user)


class TaskListView(generics.ListAPIView):
    """GET /api/core/tasks/ - List user's tasks"""
    serializer_class = TaskQueueSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            qs = TaskQueue.objects.all()
        else:
            qs = TaskQueue.objects.filter(user=user)

        status_filter = self.request.query_params.get('status')
        task_type = self.request.query_params.get('task_type')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if task_type:
            qs = qs.filter(task_type=task_type)
        return qs[:50]


class NotificationListView(generics.ListAPIView):
    """GET /api/core/notifications/ - List user's notifications"""
    serializer_class = UserNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserNotification.objects.filter(user=self.request.user)


class NotificationMarkReadView(APIView):
    """POST /api/core/notifications/{id}/read/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        notification = get_object_or_404(UserNotification, pk=pk, user=request.user)
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=['is_read', 'read_at'])
        return Response({'status': 'ok'})


class NotificationMarkAllReadView(APIView):
    """POST /api/core/notifications/mark-all-read/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        count = UserNotification.objects.filter(
            user=request.user, is_read=False
        ).update(is_read=True, read_at=timezone.now())
        return Response({'marked_read': count})


class UnreadNotificationCountView(APIView):
    """GET /api/core/notifications/unread-count/"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = UserNotification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})
