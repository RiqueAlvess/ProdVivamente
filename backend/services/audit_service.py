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

        Args:
            user: Django User instance
            empresa: Empresa instance
            acao: Action code from AuditLog.ACOES
            descricao: Human-readable description
            request: Optional Django request for IP/UA extraction
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
                empresa=empresa,
                acao=acao,
                descricao=descricao,
                ip=ip,
                user_agent=ua,
            )
        except Exception as e:
            logger.error('Failed to create audit log: %s', e)
