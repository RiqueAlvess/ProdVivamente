from rest_framework import serializers
from .models import TaskQueue, UserNotification


class TaskQueueSerializer(serializers.ModelSerializer):
    user_name = serializers.StringRelatedField(source='user')
    empresa_nome = serializers.StringRelatedField(source='empresa')

    class Meta:
        model = TaskQueue
        fields = [
            'id', 'task_type', 'status', 'attempts', 'max_attempts',
            'error_message', 'file_path', 'file_name', 'file_size', 'file_url',
            'progress', 'progress_message',
            'user', 'user_name', 'empresa', 'empresa_nome',
            'started_at', 'completed_at', 'created_at',
        ]
        read_only_fields = fields


class UserNotificationSerializer(serializers.ModelSerializer):
    task_type = serializers.CharField(source='task.task_type', read_only=True, default=None)

    class Meta:
        model = UserNotification
        fields = [
            'id', 'notification_type', 'title', 'message', 'link_url',
            'is_read', 'read_at', 'task', 'task_type', 'created_at',
        ]
        read_only_fields = [
            'id', 'notification_type', 'title', 'message', 'link_url',
            'task', 'task_type', 'read_at', 'created_at',
        ]
