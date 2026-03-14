"""
Risk service - IGRP calculation and risk distribution.
"""
import logging
from typing import Dict, Optional

from services.score_service import score_service, DIMENSOES, TIPO_DIMENSAO

logger = logging.getLogger(__name__)

NIVEL_PESO = {
    'baixo': 1,
    'moderado': 2,
    'alto': 3,
    'critico': 4,
    'sem_dados': 0,
}


class RiskService:
    """
    Calculates IGRP (Índice Geral de Risco Psicossocial) and risk distribution.
    """

    def calcular_igrp(self, campaign, filters: dict = None) -> Optional[float]:
        """
        IGRP = Weighted average of dimension risk levels.
        Scale: 0-100 (0=no risk, 100=maximum risk).
        """
        from selectors.dashboard_selectors import DashboardSelectors
        scores = DashboardSelectors.get_dimensoes_scores(campaign, filters)

        if not scores:
            return None

        total_peso = 0
        total = 0
        count = 0

        for dimensao_codigo, score in scores.items():
            if score is None:
                continue
            tipo = TIPO_DIMENSAO.get(dimensao_codigo, 'positivo')
            nivel = score_service.classificar_risco(score, tipo)
            peso = NIVEL_PESO.get(nivel, 0)
            total += peso
            count += 1

        if count == 0:
            return None

        # Normalize to 0-100 scale (max weight per dimension = 4)
        igrp = (total / (count * 4)) * 100
        return round(igrp, 1)

    def get_distribuicao_riscos(self, campaign, filters: dict = None) -> Dict:
        """
        Get count of dimensions in each risk level.
        Returns: {'baixo': N, 'moderado': N, 'alto': N, 'critico': N}
        """
        from selectors.dashboard_selectors import DashboardSelectors
        scores = DashboardSelectors.get_dimensoes_scores(campaign, filters)

        distribuicao = {'baixo': 0, 'moderado': 0, 'alto': 0, 'critico': 0}

        for dimensao_codigo, score in scores.items():
            if score is None:
                continue
            tipo = TIPO_DIMENSAO.get(dimensao_codigo, 'positivo')
            nivel = score_service.classificar_risco(score, tipo)
            if nivel in distribuicao:
                distribuicao[nivel] += 1

        return distribuicao

    def get_dimensoes_criticas(self, campaign, filters: dict = None, top_n: int = 3) -> list:
        """Get top N most critical dimensions."""
        from selectors.dashboard_selectors import DashboardSelectors
        scores = DashboardSelectors.get_dimensoes_scores(campaign, filters)

        dimensoes_com_nivel = []
        for dimensao_codigo, score in scores.items():
            if score is None:
                continue
            tipo = TIPO_DIMENSAO.get(dimensao_codigo, 'positivo')
            nivel = score_service.classificar_risco(score, tipo)
            peso = NIVEL_PESO.get(nivel, 0)
            dimensoes_com_nivel.append({
                'dimensao': dimensao_codigo,
                'score': score,
                'nivel': nivel,
                'peso': peso,
                'tipo': tipo,
            })

        # Sort by weight descending (most critical first)
        dimensoes_com_nivel.sort(key=lambda x: x['peso'], reverse=True)
        return dimensoes_com_nivel[:top_n]
