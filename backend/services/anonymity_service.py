"""
Anonymity service - Blind-drop validation and K-anonymity enforcement.
"""
from django.conf import settings


K_ANONYMITY_MIN = getattr(settings, 'K_ANONYMITY_MIN_RESPONSES', 5)


class AnonymityService:
    """
    K-anonymity enforcement: minimum N responses required to show segment data.
    """

    @staticmethod
    def check_minimum_sample_size(queryset, min_size: int = None) -> tuple:
        """
        Check if a queryset meets the minimum sample size for K-anonymity.

        Returns:
            (bool, int): (is_sufficient, count)
        """
        min_size = min_size or K_ANONYMITY_MIN
        count = queryset.count()
        return count >= min_size, count

    @staticmethod
    def filter_sufficient_groups(data_dict: dict, min_size: int = None) -> dict:
        """
        Filter out groups that don't meet minimum sample size.
        data_dict: {group_key: {'count': N, ...}}
        """
        min_size = min_size or K_ANONYMITY_MIN
        return {
            k: v for k, v in data_dict.items()
            if v.get('count', 0) >= min_size
        }

    @staticmethod
    def can_show_demographic_breakdown(responses_qs, demographic_field: str, min_size: int = None) -> bool:
        """
        Check if demographic breakdown can be shown without de-anonymization risk.
        """
        min_size = min_size or K_ANONYMITY_MIN
        from django.db.models import Count
        groups = responses_qs.values(demographic_field).annotate(count=Count('id'))
        for group in groups:
            if 0 < group['count'] < min_size:
                return False
        return True

    @staticmethod
    def get_demographic_breakdown(responses_qs, demographic_field: str, score_calc_fn, min_size: int = None) -> list:
        """
        Returns demographic breakdown only for groups meeting K-anonymity.
        Omits groups below threshold and indicates they were suppressed.
        """
        min_size = min_size or K_ANONYMITY_MIN
        from django.db.models import Count

        groups = responses_qs.values(demographic_field).annotate(count=Count('id'))
        result = []
        suppressed = 0

        for group in groups:
            group_val = group[demographic_field]
            count = group['count']
            if count < min_size:
                suppressed += 1
                continue
            group_qs = responses_qs.filter(**{demographic_field: group_val})
            scores = score_calc_fn(group_qs)
            result.append({
                'grupo': group_val or 'Não informado',
                'total': count,
                'scores': scores,
            })

        if suppressed > 0:
            result.append({
                'grupo': f'Outros ({suppressed} grupos com menos de {min_size} respondentes)',
                'total': None,
                'scores': None,
                'suppressed': True,
            })

        return result
