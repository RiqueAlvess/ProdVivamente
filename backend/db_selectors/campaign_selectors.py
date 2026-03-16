"""
Campaign selectors - query layer for campaign data.
"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class CampaignSelectors:
    """Selectors for campaign-related queries."""

    @staticmethod
    def get_campaigns_for_user(user) -> 'QuerySet':
        """Get all accessible campaigns for a user."""
        from apps.surveys.models import Campaign

        if user.is_staff or user.is_superuser:
            return Campaign.objects.all()

        try:
            empresa = user.profile.empresa
            if empresa:
                return Campaign.objects.filter(empresa=empresa)
        except Exception:
            pass
        return Campaign.objects.none()

    @staticmethod
    def get_campaign_summary(campaign) -> Dict:
        """Get a summary of a campaign's current state."""
        from apps.invitations.models import SurveyInvitation

        invitations = SurveyInvitation.objects.filter(campaign=campaign)
        responses = campaign.respostas

        return {
            'id': campaign.id,
            'nome': campaign.nome,
            'status': campaign.status,
            'data_inicio': campaign.data_inicio,
            'data_fim': campaign.data_fim,
            'total_convidados': invitations.count(),
            'total_enviados': invitations.filter(status__in=['sent', 'used']).count(),
            'total_respondidos': responses.count(),
            'taxa_adesao': campaign.taxa_adesao,
            'meta_adesao': campaign.meta_adesao,
        }

    @staticmethod
    def get_invitation_distribution(campaign) -> Dict:
        """Get invitation distribution by status and structure."""
        from django.db.models import Count
        from apps.invitations.models import SurveyInvitation

        by_status = dict(
            SurveyInvitation.objects.filter(campaign=campaign)
            .values('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        )

        by_setor = list(
            SurveyInvitation.objects.filter(campaign=campaign)
            .values('setor__nome')
            .annotate(total=Count('id'), used=Count('id', filter=__import__('django.db.models', fromlist=['Q']).Q(status='used')))
            .order_by('setor__nome')
        )

        return {
            'by_status': by_status,
            'by_setor': by_setor,
        }
