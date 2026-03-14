"""
Sector AI analysis service.
"""
import logging

from services.score_service import score_service, DIMENSOES
from services.risk_service import RiskService

logger = logging.getLogger(__name__)


class SectorAnalysisService:
    """Generates AI-powered sector analysis."""

    def __init__(self):
        self.risk_service = RiskService()

    def preparar_dados_setor(self, campaign, setor) -> dict:
        """Prepare sector data for AI analysis."""
        from apps.responses.models import SurveyResponse
        from django.conf import settings

        respostas = SurveyResponse.objects.filter(
            campaign=campaign, setor=setor
        )

        if not respostas.exists():
            return {}

        # Calculate scores per dimension
        scores = {}
        for dimensao_codigo in DIMENSOES:
            valores = []
            for r in respostas:
                s = score_service.calcular_score_dimensao(r.respostas, dimensao_codigo)
                if s is not None:
                    valores.append(s)
            scores[dimensao_codigo] = round(sum(valores) / len(valores), 3) if valores else None

        # Get critical dimensions
        from services.score_service import TIPO_DIMENSAO
        dimensoes_criticas = []
        for dim, score in scores.items():
            if score is None:
                continue
            tipo = TIPO_DIMENSAO.get(dim, 'positivo')
            nivel = score_service.classificar_risco(score, tipo)
            if nivel in ('alto', 'critico'):
                dimensoes_criticas.append({'dimensao': dim, 'score': score, 'nivel': nivel})

        # Collect comments summary (no PII)
        comentarios = list(
            respostas.exclude(comentario_livre='')
            .values_list('comentario_livre', flat=True)[:20]
        )
        comentarios_resumo = ' | '.join(comentarios[:10]) if comentarios else ''

        return {
            'setor_nome': setor.nome,
            'empresa_nome': campaign.empresa.nome_app,
            'total_respondentes': respostas.count(),
            'scores': scores,
            'dimensoes_criticas': dimensoes_criticas,
            'comentarios_resumo': comentarios_resumo[:2000],
        }

    def gerar_analise(self, campaign, setor) -> dict:
        """Generate complete sector analysis."""
        from apps.analytics.models import SectorAnalysis
        from services.ai_service import get_ai_service
        from django.conf import settings

        dados = self.preparar_dados_setor(campaign, setor)
        if not dados:
            raise ValueError(f'Sem dados suficientes para análise do setor {setor.nome}')

        # Check K-anonymity
        min_respostas = getattr(settings, 'K_ANONYMITY_MIN_RESPONSES', 5)
        if dados['total_respondentes'] < min_respostas:
            raise ValueError(
                f'Mínimo de {min_respostas} respostas necessário para análise. '
                f'Setor tem {dados["total_respondentes"]}.'
            )

        ai = get_ai_service()
        result = ai.analisar_setor(dados)
        result['modelo_ia'] = getattr(settings, 'OPENROUTER_MODEL', 'unknown')

        return result


sector_analysis_service = SectorAnalysisService()
