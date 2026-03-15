"""
Anonymity service - Data release gate based on campaign finalization.

Before a campaign is finalized (status='closed'), no data is shown.
"""


class AnonymityService:
    """
    Data release gate: data is only shown after campaign is finalized (status='closed').
    """

    @staticmethod
    def is_data_released(campaign) -> bool:
        """
        Returns True only if the campaign has been finalized (closed).
        Data must not be displayed before finalization.
        """
        return campaign.status == 'closed'

    @staticmethod
    def get_demographic_breakdown(responses_qs, demographic_field: str, score_calc_fn) -> list:
        """
        Returns demographic breakdown for all groups.
        Only called after is_data_released() check passes.
        """
        from django.db.models import Count

        groups = responses_qs.values(demographic_field).annotate(count=Count('id'))
        result = []

        for group in groups:
            group_val = group[demographic_field]
            count = group['count']
            group_qs = responses_qs.filter(**{demographic_field: group_val})
            scores = score_calc_fn(group_qs)
            result.append({
                'grupo': group_val or 'Não informado',
                'total': count,
                'scores': scores,
            })

        return result
