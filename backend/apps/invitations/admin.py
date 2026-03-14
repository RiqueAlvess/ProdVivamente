from django.contrib import admin
from .models import SurveyInvitation


@admin.register(SurveyInvitation)
class SurveyInvitationAdmin(admin.ModelAdmin):
    list_display = ['hash_token', 'empresa', 'campaign', 'unidade', 'setor', 'status', 'expires_at', 'created_at']
    list_filter = ['status', 'empresa', 'campaign']
    search_fields = ['hash_token']
    readonly_fields = ['hash_token', 'email_encrypted', 'nome_encrypted', 'created_at', 'sent_at', 'used_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        # Invitations are created via CSV import, not directly
        return False
