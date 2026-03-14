from django.contrib import admin
from .models import TaskQueue, UserNotification


@admin.register(TaskQueue)
class TaskQueueAdmin(admin.ModelAdmin):
    list_display = ['id', 'task_type', 'status', 'progress', 'user', 'empresa', 'created_at', 'completed_at']
    list_filter = ['status', 'task_type']
    readonly_fields = [
        'task_type', 'payload', 'status', 'attempts', 'error_message',
        'file_path', 'file_name', 'file_size', 'file_url',
        'progress', 'progress_message',
        'started_at', 'completed_at', 'created_at',
    ]
    date_hierarchy = 'created_at'
    search_fields = ['task_type', 'user__username']

    def has_add_permission(self, request):
        return False


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['user', 'task', 'notification_type', 'title', 'message', 'link_url', 'created_at']
