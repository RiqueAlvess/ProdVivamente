"""
Sentiment analysis service for survey comments.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SentimentService:
    """Analyzes sentiment of free-text comments using AI."""

    def analisar(self, comentario: str) -> dict:
        """
        Analyze sentiment of a comment.

        Returns:
            {
                'score': float (-1.0 to 1.0),
                'categorias': list[str],
                'emocoes_detectadas': list[str],
                'urgencia': str,
                'requer_atencao_imediata': bool,
            }
        """
        if not comentario or not comentario.strip():
            return {
                'score': None,
                'categorias': [],
                'emocoes_detectadas': [],
                'urgencia': 'baixa',
                'requer_atencao_imediata': False,
            }

        try:
            from services.ai_service import get_ai_service
            ai = get_ai_service()
            result = ai.analisar_sentimento(comentario)
            return result
        except Exception as e:
            logger.error('Sentiment analysis failed: %s', e)
            return {
                'score': None,
                'categorias': [],
                'emocoes_detectadas': [],
                'urgencia': 'baixa',
                'requer_atencao_imediata': False,
                'error': str(e),
            }

    def analisar_batch(self, comentarios: list) -> list:
        """Analyze a batch of comments."""
        results = []
        for comentario in comentarios:
            result = self.analisar(comentario)
            results.append(result)
        return results


sentiment_service = SentimentService()
