"""
HSE-IT score calculation service.
Maps 35 questions to 7 dimensions and calculates risk levels.
"""
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# HSE-IT Question to Dimension mapping
# ---------------------------------------------------------------------------
DIMENSOES: Dict[str, List[int]] = {
    'demandas': [3, 6, 9, 12, 16, 18, 20, 22],
    'controle': [2, 10, 15, 19, 25, 30],
    'apoio_chefia': [8, 23, 29, 33, 35],
    'apoio_colegas': [7, 24, 27, 31],
    'relacionamentos': [5, 14, 21, 34],
    'cargo': [1, 4, 11, 13, 17],
    'comunicacao_mudancas': [26, 28, 32],
}

TIPO_DIMENSAO: Dict[str, str] = {
    'demandas': 'negativo',
    'relacionamentos': 'negativo',
    'controle': 'positivo',
    'apoio_chefia': 'positivo',
    'apoio_colegas': 'positivo',
    'cargo': 'positivo',
    'comunicacao_mudancas': 'positivo',
}

# Risk classification thresholds (scores 0-4)
# For positive dimensions: higher score = lower risk
# For negative dimensions: higher score = higher risk (inverted)
RISK_THRESHOLDS = {
    'positivo': {
        'baixo': (3.0, 4.0),      # Score >= 3.0
        'moderado': (2.0, 3.0),   # Score >= 2.0
        'alto': (1.0, 2.0),       # Score >= 1.0
        'critico': (0.0, 1.0),    # Score < 1.0
    },
    'negativo': {
        'baixo': (0.0, 1.0),      # Score < 1.0 (low demand/conflict)
        'moderado': (1.0, 2.0),
        'alto': (2.0, 3.0),
        'critico': (3.0, 4.01),   # Score >= 3.0 (high demand/conflict)
    },
}


class ScoreService:
    """
    Calculates HSE-IT psychosocial risk scores.
    """

    def calcular_score_dimensao(self, respostas: dict, dimensao_codigo: str) -> Optional[float]:
        """
        Calculate the average score for a dimension.

        Args:
            respostas: {str(question_number): int(value 0-4)}
            dimensao_codigo: e.g. 'demandas'

        Returns:
            float score 0-4, or None if no valid answers
        """
        perguntas = DIMENSOES.get(dimensao_codigo, [])
        valores = []
        for p in perguntas:
            val = respostas.get(str(p)) or respostas.get(p)
            if val is not None:
                try:
                    valores.append(float(val))
                except (TypeError, ValueError):
                    pass

        if not valores:
            return None

        return round(sum(valores) / len(valores), 3)

    def classificar_risco(self, score: float, tipo: str) -> str:
        """
        Classify risk level based on score and dimension type.

        Args:
            score: 0-4
            tipo: 'positivo' or 'negativo'

        Returns:
            'baixo', 'moderado', 'alto', or 'critico'
        """
        if score is None:
            return 'sem_dados'

        thresholds = RISK_THRESHOLDS.get(tipo, RISK_THRESHOLDS['positivo'])

        if tipo == 'negativo':
            if score >= 3.0:
                return 'critico'
            elif score >= 2.0:
                return 'alto'
            elif score >= 1.0:
                return 'moderado'
            return 'baixo'
        else:
            if score >= 3.0:
                return 'baixo'
            elif score >= 2.0:
                return 'moderado'
            elif score >= 1.0:
                return 'alto'
            return 'critico'

    def calcular_nivel_risco(self, score: float, dimensao_codigo: str) -> str:
        """Calculate risk level for a specific dimension."""
        tipo = TIPO_DIMENSAO.get(dimensao_codigo, 'positivo')
        return self.classificar_risco(score, tipo)

    def calcular_scores_completos(self, respostas: dict) -> Dict[str, dict]:
        """
        Calculate scores and risk levels for all dimensions.

        Returns:
            {
                'demandas': {'score': 2.5, 'nivel': 'moderado', 'tipo': 'negativo'},
                ...
            }
        """
        resultado = {}
        for dimensao_codigo in DIMENSOES:
            score = self.calcular_score_dimensao(respostas, dimensao_codigo)
            tipo = TIPO_DIMENSAO[dimensao_codigo]
            nivel = self.classificar_risco(score, tipo) if score is not None else 'sem_dados'
            resultado[dimensao_codigo] = {
                'score': score,
                'nivel': nivel,
                'tipo': tipo,
            }
        return resultado

    def calcular_score_geral(self, respostas: dict) -> Optional[float]:
        """
        Calculate overall wellbeing score (weighted average of all dimensions).
        Negative dimensions are inverted before averaging.
        """
        scores = []
        for dimensao_codigo, tipo in TIPO_DIMENSAO.items():
            score = self.calcular_score_dimensao(respostas, dimensao_codigo)
            if score is not None:
                # Invert negative dimensions for overall score
                if tipo == 'negativo':
                    score = 4 - score
                scores.append(score)

        if not scores:
            return None
        return round(sum(scores) / len(scores), 3)

    def processar_resposta_completa(self, resposta_obj) -> Dict:
        """
        Process a complete SurveyResponse object and return all scores.
        """
        respostas = resposta_obj.respostas or {}
        scores_dimensoes = self.calcular_scores_completos(respostas)
        score_geral = self.calcular_score_geral(respostas)

        # Overall risk level based on geral score
        nivel_geral = 'sem_dados'
        if score_geral is not None:
            # Overall is treated as positive (higher = better)
            nivel_geral = self.classificar_risco(score_geral, 'positivo')

        return {
            'dimensoes': scores_dimensoes,
            'score_geral': score_geral,
            'nivel_geral': nivel_geral,
        }

    def calcular_medias_campanha(self, campaign) -> Dict:
        """
        Calculate average scores across all responses for a campaign.
        """
        from apps.responses.models import SurveyResponse
        respostas = SurveyResponse.objects.filter(campaign=campaign)

        if not respostas.exists():
            return {}

        scores_por_dimensao: Dict[str, List[float]] = {d: [] for d in DIMENSOES}

        for r in respostas:
            for dimensao_codigo in DIMENSOES:
                score = self.calcular_score_dimensao(r.respostas, dimensao_codigo)
                if score is not None:
                    scores_por_dimensao[dimensao_codigo].append(score)

        return {
            dim: {
                'media': round(sum(ss) / len(ss), 3) if ss else None,
                'nivel': self.classificar_risco(
                    sum(ss) / len(ss) if ss else None,
                    TIPO_DIMENSAO[dim]
                ) if ss else 'sem_dados',
                'tipo': TIPO_DIMENSAO[dim],
                'n': len(ss),
            }
            for dim, ss in scores_por_dimensao.items()
        }


score_service = ScoreService()
