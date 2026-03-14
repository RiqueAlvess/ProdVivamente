"""
Email service - Resend abstraction with easy provider swapping.
"""
import logging
from abc import ABC, abstractmethod

from django.conf import settings

logger = logging.getLogger(__name__)


class EmailServiceBase(ABC):
    """Abstract base - easy to swap email providers."""

    @abstractmethod
    def send(self, to: str, subject: str, html_body: str) -> bool:
        """Send a single email. Returns True on success."""
        ...

    @abstractmethod
    def send_bulk(self, emails: list) -> dict:
        """
        Send multiple emails.
        emails: list of {'to': str, 'subject': str, 'html_body': str}
        Returns: {'success': N, 'failed': N}
        """
        ...


class ResendEmailService(EmailServiceBase):
    """Resend.com email service implementation."""

    def send(self, to: str, subject: str, html_body: str) -> bool:
        try:
            import resend
            resend.api_key = settings.RESEND_API_KEY
            result = resend.Emails.send({
                'from': settings.EMAIL_FROM,
                'to': to,
                'subject': subject,
                'html': html_body,
            })
            logger.info('Email sent to %s: %s', to, result.get('id', ''))
            return True
        except Exception as e:
            logger.error('Email send failed to %s: %s', to, e)
            return False

    def send_bulk(self, emails: list) -> dict:
        success = 0
        failed = 0
        for email in emails:
            if self.send(
                to=email['to'],
                subject=email['subject'],
                html_body=email['html_body'],
            ):
                success += 1
            else:
                failed += 1
        return {'success': success, 'failed': failed}


class ConsoleEmailService(EmailServiceBase):
    """Development email service - logs to console."""

    def send(self, to: str, subject: str, html_body: str) -> bool:
        logger.info('=== EMAIL (console) ===')
        logger.info('To: %s', to)
        logger.info('Subject: %s', subject)
        logger.info('Body: %s...', html_body[:200])
        logger.info('=====================')
        return True

    def send_bulk(self, emails: list) -> dict:
        for email in emails:
            self.send(email['to'], email['subject'], email['html_body'])
        return {'success': len(emails), 'failed': 0}


def get_email_service() -> EmailServiceBase:
    """Factory - easy to swap email providers via EMAIL_PROVIDER setting."""
    provider = getattr(settings, 'EMAIL_PROVIDER', 'resend')
    if provider == 'resend':
        return ResendEmailService()
    elif provider == 'console':
        return ConsoleEmailService()
    raise ValueError(f'Unknown email provider: {provider}')
