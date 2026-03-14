"""
Dashboard selectors - query layer for dashboard data.
Enforces K-anonymity on all segmented data.
"""
import logging
from typing import Dict, List, Optional

from services.score_service import score_service, DIMENSOES, TIPO_DIMENSAO
from services.anonymity_service import AnonymityService

logger = logging.getLogger(__name__)


class DashboardSelectors:
    """Selectors for dashboard data queries."""

    @staticmethod
    def get_responses(campaign, filters: dict = None):
        """Get filtered responses for a campaign."""
        from apps.responses.models import SurveyResponse
        qs = SurveyResponse.objects.filter(campaign=campaign).select_related('unidade', 'setor')

        if filters:
            if filters.get('unidade_id'):
                qs = qs.filter(unidade_id=filters['unidade_id'])
            if filters.get('setor_id'):
                qs = qs.filter(setor_id=filters['setor_id'])
            if filters.get('faixa_etaria'):
                qs = qs.filter(faixa_etaria=filters['faixa_etaria'])
            if filters.get('genero'):
                qs = qs.filter(genero=filters['genero'])

        return qs

    @staticmethod
    def get_dimensoes_scores(campaign, filters: dict = None) -> Dict[str, Optional[float]]:
        """Calculate average scores per dimension."""
        responses = DashboardSelectors.get_responses(campaign, filters)
        if not responses.exists():
            return {dim: None for dim in DIMENSOES}

        scores = {dim: [] for dim in DIMENSOES}

        for response in responses:
            for dim in DIMENSOES:
                s = score_service.calcular_score_dimensao(response.respostas, dim)
                if s is not None:
                    scores[dim].append(s)

        return {
            dim: round(sum(ss) / len(ss), 3) if ss else None
            for dim, ss in scores.items()
        }

    @staticmethod
    def get_metrics(campaign, filters: dict = None) -> Dict:
        """Get campaign participation metrics."""
        responses = DashboardSelectors.get_responses(campaign, filters)
        total_invited = campaign.invitations.count()
        total_responded = responses.count()
        taxa_adesao = round(total_responded / total_invited * 100, 1) if total_invited > 0 else 0.0

        return {
            'total_convidados': total_invited,
            'total_respondidos': total_responded,
            'taxa_adesao': taxa_adesao,
            'meta_adesao': campaign.meta_adesao,
            'meta_atingida': taxa_adesao >= campaign.meta_adesao,
        }

    @staticmethod
    def get_scores_por_setor(campaign, filters: dict = None, top_n: int = 5) -> List[Dict]:
        """
        Top N critical sectors by average score.
        Requires minimum 5 responses per sector (K-anonymity).
        """
        responses = DashboardSelectors.get_responses(campaign, filters)
        setores = responses.values_list('setor', flat=True).distinct()

        result = []
        for setor_id in setores:
            setor_responses = responses.filter(setor_id=setor_id)
            ok, count = AnonymityService.check_minimum_sample_size(setor_responses)
            if not ok:
                continue

            setor_filters = {**(filters or {}), 'setor_id': setor_id}
            scores = DashboardSelectors.get_dimensoes_scores(campaign, setor_filters)

            # Calculate weighted average (considering dimension types)
            valid_scores = []
            for dim, sc in scores.items():
                if sc is None:
                    continue
                tipo = TIPO_DIMENSAO.get(dim, 'positivo')
                # Normalize to 0-1 scale where 0=best, 1=worst for comparison
                if tipo == 'negativo':
                    normalized = sc / 4.0
                else:
                    normalized = (4.0 - sc) / 4.0
                valid_scores.append(normalized)

            if not valid_scores:
                continue

            avg_risk = sum(valid_scores) / len(valid_scores)

            try:
                from apps.structure.models import Setor
                setor = Setor.objects.get(pk=setor_id)
                setor_nome = setor.nome
                unidade_nome = setor.unidade.nome
            except Exception:
                setor_nome = str(setor_id)
                unidade_nome = ''

            result.append({
                'setor_id': setor_id,
                'setor_nome': setor_nome,
                'unidade_nome': unidade_nome,
                'total_respondentes': count,
                'score_risco_medio': round(avg_risk, 3),
                'scores': scores,
            })

        # Sort by risk score descending (most at-risk first)
        result.sort(key=lambda x: x['score_risco_medio'], reverse=True)
        return result[:top_n]

    @staticmethod
    def get_heatmap(campaign, filters: dict = None) -> List[Dict]:
        """
        Sector × Dimension heatmap data.
        K-anonymity enforced - only sectors with >= 5 responses included.
        """
        responses = DashboardSelectors.get_responses(campaign, filters)
        setores = responses.values_list('setor__nome', 'setor_id').distinct()

        heatmap = []
        for setor_nome, setor_id in setores:
            setor_responses = responses.filter(setor_id=setor_id)
            ok, count = AnonymityService.check_minimum_sample_size(setor_responses)
            if not ok:
                continue

            scores = DashboardSelectors.get_dimensoes_scores(
                campaign, {**(filters or {}), 'setor_id': setor_id}
            )

            # Add risk levels
            scores_with_levels = {}
            for dim, sc in scores.items():
                tipo = TIPO_DIMENSAO.get(dim, 'positivo')
                nivel = score_service.classificar_risco(sc, tipo) if sc is not None else 'sem_dados'
                scores_with_levels[dim] = {
                    'score': sc,
                    'nivel': nivel,
                    'tipo': tipo,
                }

            heatmap.append({
                'setor': setor_nome,
                'setor_id': setor_id,
                'total': count,
                'scores': scores_with_levels,
            })

        return sorted(heatmap, key=lambda x: x['setor'])

    @staticmethod
    def get_demographic_scores(campaign, filters: dict = None) -> Dict:
        """
        Scores by demographics - K-anonymity enforced.
        Only shows groups with >= 5 responses.
        """
        responses = DashboardSelectors.get_responses(campaign, filters)

        result = {}
        for field in ['faixa_etaria', 'genero', 'tempo_empresa']:
            result[field] = AnonymityService.get_demographic_breakdown(
                responses_qs=responses,
                demographic_field=field,
                score_calc_fn=lambda qs: DashboardSelectors._calc_scores_for_qs(qs),
            )

        return result

    @staticmethod
    def _calc_scores_for_qs(qs) -> Dict:
        """Helper to calculate dimension scores for a queryset."""
        scores = {}
        for dim in DIMENSOES:
            valores = []
            for r in qs:
                s = score_service.calcular_score_dimensao(r.respostas, dim)
                if s is not None:
                    valores.append(s)
            scores[dim] = round(sum(valores) / len(valores), 3) if valores else None
        return scores

    @staticmethod
    def get_timeline(campaign) -> List[Dict]:
        """Get weekly response counts over time."""
        from apps.responses.models import SurveyResponse
        from django.db.models import Count
        from django.db.models.functions import TruncWeek

        weekly = (
            SurveyResponse.objects.filter(campaign=campaign)
            .annotate(week=TruncWeek('created_at'))
            .values('week')
            .annotate(count=Count('id'))
            .order_by('week')
        )

        return [
            {'week': w['week'].strftime('%Y-%m-%d'), 'count': w['count']}
            for w in weekly
        ]
