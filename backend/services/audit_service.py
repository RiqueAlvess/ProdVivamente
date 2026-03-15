"""
Audit logging service.
"""
import logging

logger = logging.getLogger(__name__)


class AuditService:
    """Centralized audit logging."""

    @staticmethod
    def log(user, empresa, acao: str, descricao: str, request=None) -> None:
        """
        Create an audit log entry.
        Tenant isolation is handled by django-tenants (schema-based).
        The empresa parameter is accepted for call-site compatibility but not stored.
        """
        from apps.accounts.models import AuditLog

        ip = None
        ua = ''

        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')
            ua = request.META.get('HTTP_USER_AGENT', '')[:500]

        try:
            AuditLog.objects.create(
                user=user,
                acao=acao,
                descricao=descricao,
                ip=ip,
                user_agent=ua,
            )
        except Exception as e:
            logger.error('Failed to create audit log: %s', e)
