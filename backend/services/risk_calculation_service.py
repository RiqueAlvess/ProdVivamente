"""
NR-1 Risk Matrix calculation service.
NR = Probabilidade × Severidade (P × S matrix).
"""
import logging
from typing import Dict, List, Optional

from services.score_service import score_service, DIMENSOES, TIPO_DIMENSAO

logger = logging.getLogger(__name__)

# Risk matrix thresholds
RISK_MATRIX = {
    # NR score -> level
    (1, 4): 'baixo',
    (5, 9): 'moderado',
    (10, 15): 'alto',
    (16, 20): 'critico',
}

# Dimensao -> default probability and severity mappings
DIMENSAO_RISK_PARAMS = {
    'demandas': {'probabilidade': 3, 'severidade': 4},
    'controle': {'probabilidade': 2, 'severidade': 3},
    'apoio_chefia': {'probabilidade': 2, 'severidade': 3},
    'apoio_colegas': {'probabilidade': 2, 'severidade': 2},
    'relacionamentos': {'probabilidade': 2, 'severidade': 4},
    'cargo': {'probabilidade': 2, 'severidade': 3},
    'comunicacao_mudancas': {'probabilidade': 2, 'severidade': 2},
}

# CNAE severity modifiers
CNAE_SEVERITY_MAP = {
    '10': 1.2,  # Food manufacturing - higher demands
    '47': 1.0,  # Retail
    '62': 0.9,  # IT services
    '84': 1.3,  # Public admin - high demands
    '85': 1.1,  # Education
    '86': 1.4,  # Healthcare - highest
    '88': 1.2,  # Social services
}


def calcular_nivel_risco_nr(nr_score: int) -> str:
    """Map NR score to risk level."""
    if nr_score <= 4:
        return 'baixo'
    elif nr_score <= 9:
        return 'moderado'
    elif nr_score <= 15:
        return 'alto'
    return 'critico'


class RiskCalculationService:
    """
    Calculates psychosocial risk matrix based on HSE-IT scores.
    Uses P × S (Probability × Severity) matrix per NR-1 methodology.
    """

    def get_cnae_modifier(self, cnae: str) -> float:
        """Get severity modifier for CNAE."""
        if not cnae:
            return 1.0
        prefix_2 = cnae[:2]
        prefix_4 = cnae[:4]
        # Check 4-digit prefix first, then 2-digit
        return CNAE_SEVERITY_MAP.get(prefix_4, CNAE_SEVERITY_MAP.get(prefix_2, 1.0))

    def calcular_probabilidade(self, score: float, tipo: str) -> int:
        """
        Convert HSE-IT score to probability (1-5).
        Negative dimensions: higher score = higher probability.
        Positive dimensions: lower score = higher probability.
        """
        if score is None:
            return 2  # Default moderate

        if tipo == 'negativo':
            if score >= 3.5:
                return 5
            elif score >= 2.5:
                return 4
            elif score >= 1.5:
                return 3
            elif score >= 0.5:
                return 2
            return 1
        else:
            # Positive: invert
            inverted = 4 - score
            if inverted >= 3.5:
                return 5
            elif inverted >= 2.5:
                return 4
            elif inverted >= 1.5:
                return 3
            elif inverted >= 0.5:
                return 2
            return 1

    def calcular_severidade(self, dimensao_codigo: str, cnae: str = '') -> int:
        """Get base severity for a dimension, adjusted by CNAE."""
        params = DIMENSAO_RISK_PARAMS.get(dimensao_codigo, {'probabilidade': 2, 'severidade': 2})
        base_sev = params['severidade']
        modifier = self.get_cnae_modifier(cnae)
        adjusted = min(5, round(base_sev * modifier))
        return adjusted

    def calcular_risco_dimensao(
        self,
        dimensao_codigo: str,
        score: Optional[float],
        cnae: str = ''
    ) -> Dict:
        """Calculate risk for a single dimension."""
        tipo = TIPO_DIMENSAO.get(dimensao_codigo, 'positivo')
        probabilidade = self.calcular_probabilidade(score, tipo)
        severidade = self.calcular_severidade(dimensao_codigo, cnae)
        nr_score = probabilidade * severidade
        nivel = calcular_nivel_risco_nr(nr_score)

        return {
            'dimensao': dimensao_codigo,
            'score_hse': score,
            'probabilidade': probabilidade,
            'severidade': severidade,
            'nr_score': nr_score,
            'nivel': nivel,
            'tipo': tipo,
        }

    def gerar_matriz_completa(self, campaign, cnae: str = '') -> Dict:
        """
        Generate complete risk matrix for a campaign.
        """
        from apps.responses.models import SurveyResponse

        respostas = SurveyResponse.objects.filter(campaign=campaign)
        total = respostas.count()

        if total == 0:
            return {
                'total_respostas': 0,
                'fatores': [],
                'nivel_geral': 'sem_dados',
                'cnae': cnae,
            }

        # Calculate averages per dimension
        scores_medios = {}
        for dimensao_codigo in DIMENSOES:
            scores = []
            for r in respostas:
                s = score_service.calcular_score_dimensao(r.respostas, dimensao_codigo)
                if s is not None:
                    scores.append(s)
            scores_medios[dimensao_codigo] = sum(scores) / len(scores) if scores else None

        # Build risk matrix
        fatores = []
        nr_scores = []
        for dimensao_codigo, score in scores_medios.items():
            risco = self.calcular_risco_dimensao(dimensao_codigo, score, cnae)
            fatores.append(risco)
            nr_scores.append(risco['nr_score'])

        # Overall risk
        media_nr = sum(nr_scores) / len(nr_scores) if nr_scores else 0
        nivel_geral = calcular_nivel_risco_nr(round(media_nr))

        # Sort by NR score descending (most critical first)
        fatores.sort(key=lambda x: x['nr_score'], reverse=True)

        return {
            'total_respostas': total,
            'fatores': fatores,
            'nivel_geral': nivel_geral,
            'media_nr': round(media_nr, 2),
            'cnae': cnae,
        }

    def get_fatores_risco_associados(self, dimensao_codigo: str, nivel: str) -> List[Dict]:
        """Get associated FatorRisco records for a dimension and risk level."""
        from apps.surveys.models import FatorRisco, Dimensao
        try:
            dimensao = Dimensao.objects.get(codigo=dimensao_codigo)
            fatores = FatorRisco.objects.filter(dimensao=dimensao).select_related('categoria')
            return [
                {
                    'nome': f.nome,
                    'categoria': f.categoria.nome,
                    'acoes_preventivas': f.acoes_preventivas,
                }
                for f in fatores
            ]
        except Exception:
            return []
