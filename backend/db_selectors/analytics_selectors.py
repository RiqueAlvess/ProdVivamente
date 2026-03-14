"""
Analytics selectors - query layer for analytics data.
"""
import logging
from typing import Dict, List

from services.score_service import score_service, DIMENSOES, TIPO_DIMENSAO

logger = logging.getLogger(__name__)


class AnalyticsSelectors:
    """Selectors for analytics queries."""

    @staticmethod
    def compare_campaigns(campaigns) -> Dict:
        """
        Compare multiple campaigns side by side.
        Returns scores and risk levels for each campaign.
        """
        from db_selectors.dashboard_selectors import DashboardSelectors
        from services.risk_service import RiskService

        risk_svc = RiskService()
        comparison = []

        for campaign in campaigns:
            scores = DashboardSelectors.get_dimensoes_scores(campaign)
            metrics = DashboardSelectors.get_metrics(campaign)
            igrp = risk_svc.calcular_igrp(campaign)
            distribuicao = risk_svc.get_distribuicao_riscos(campaign)

            comparison.append({
                'campaign_id': campaign.id,
                'campaign_nome': campaign.nome,
                'data_inicio': campaign.data_inicio,
                'data_fim': campaign.data_fim,
                'closed_at': campaign.closed_at,
                'scores': scores,
                'metrics': metrics,
                'igrp': igrp,
                'distribuicao_riscos': distribuicao,
            })

        # Calculate trends (deltas between campaigns sorted by date)
        comparison_sorted = sorted(
            comparison,
            key=lambda x: x['data_inicio'] or x['campaign_id']
        )

        if len(comparison_sorted) >= 2:
            trends = AnalyticsSelectors._calculate_trends(comparison_sorted)
        else:
            trends = {}

        return {
            'campaigns': comparison,
            'campaigns_sorted': comparison_sorted,
            'trends': trends,
        }

    @staticmethod
    def _calculate_trends(campaigns: List[Dict]) -> Dict:
        """Calculate score trends across campaigns."""
        if len(campaigns) < 2:
            return {}

        first = campaigns[0]
        last = campaigns[-1]

        trends = {}
        for dim in DIMENSOES:
            first_score = first['scores'].get(dim)
            last_score = last['scores'].get(dim)

            if first_score is None or last_score is None:
                continue

            delta = last_score - first_score
            tipo = TIPO_DIMENSAO.get(dim, 'positivo')

            # For positive dims: positive delta = improvement
            # For negative dims: negative delta = improvement
            improved = (
                (tipo == 'positivo' and delta > 0) or
                (tipo == 'negativo' and delta < 0)
            )

            trends[dim] = {
                'delta': round(delta, 3),
                'improved': improved,
                'first_score': first_score,
                'last_score': last_score,
                'tipo': tipo,
            }

        return trends

    @staticmethod
    def get_star_schema_summary(campaign) -> Dict:
        """Get pre-computed star schema data for a campaign."""
        from apps.analytics.models import (
            FactScoreDimensao, FactIndicadorCampanha, DimEstrutura
        )

        try:
            kpis = FactIndicadorCampanha.objects.get(campaign=campaign)
            kpis_data = {
                'total_convidados': kpis.total_convidados,
                'total_respondidos': kpis.total_respondidos,
                'taxa_adesao': kpis.taxa_adesao,
                'igrp': kpis.igrp,
                'score_geral': kpis.score_geral,
                'nivel_risco_geral': kpis.nivel_risco_geral,
            }
        except FactIndicadorCampanha.DoesNotExist:
            kpis_data = {}

        fact_scores = FactScoreDimensao.objects.filter(
            campaign=campaign
        ).select_related('dim_estrutura', 'dim_dimensao')

        scores_data = [
            {
                'setor': fs.dim_estrutura.setor_nome,
                'unidade': fs.dim_estrutura.unidade_nome,
                'dimensao': fs.dim_dimensao.codigo,
                'score_medio': fs.score_medio,
                'nivel_risco': fs.nivel_risco,
                'total_respostas': fs.total_respostas,
            }
            for fs in fact_scores
        ]

        return {
            'kpis': kpis_data,
            'scores_por_setor_dimensao': scores_data,
        }
