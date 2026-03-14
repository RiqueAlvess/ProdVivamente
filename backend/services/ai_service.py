"""
AI service - OpenRouter client with easy provider swapping.
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

import requests
from django.conf import settings

from services.ai_prompts import (
    PROMPT_ANALISE_SETOR,
    PROMPT_ANALISE_SENTIMENTO,
    PROMPT_PLANO_ACAO,
    PROMPT_COMPARACAO_CAMPANHAS,
    PROMPT_RECOMENDACOES,
)

logger = logging.getLogger(__name__)


class AIServiceBase(ABC):
    """Abstract base class - easy to swap AI providers."""

    @abstractmethod
    def completar(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
        response_format: Optional[dict] = None,
        timeout: int = 60,
    ) -> str:
        raise NotImplementedError

    def analisar_setor(self, setor_data: dict) -> dict:
        """Analyze a sector's HSE-IT data and return insights."""
        prompt = PROMPT_ANALISE_SETOR.format(
            setor_nome=setor_data.get('setor_nome', ''),
            empresa_nome=setor_data.get('empresa_nome', ''),
            total_respondentes=setor_data.get('total_respondentes', 0),
            scores=json.dumps(setor_data.get('scores', {}), ensure_ascii=False, indent=2),
            dimensoes_criticas=json.dumps(setor_data.get('dimensoes_criticas', []), ensure_ascii=False),
            comentarios=setor_data.get('comentarios_resumo', ''),
        )
        response_text = self.completar(prompt, max_tokens=2500, temperature=0.4)
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {
                'pontos_criticos': [],
                'recomendacoes': [],
                'analise_completa': response_text,
            }

    def analisar_sentimento(self, comentario: str) -> dict:
        """Analyze sentiment of a free text comment."""
        prompt = PROMPT_ANALISE_SENTIMENTO.format(comentario=comentario)
        response_text = self.completar(
            prompt,
            max_tokens=500,
            temperature=0.1,
            response_format={'type': 'json_object'},
        )
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {'score': 0.0, 'categorias': [], 'raw': response_text}

    def gerar_plano_acao(self, context: dict) -> dict:
        """Generate an action plan for a risk dimension."""
        prompt = PROMPT_PLANO_ACAO.format(
            dimensao=context.get('dimensao', ''),
            nivel_risco=context.get('nivel_risco', ''),
            score=context.get('score', ''),
            empresa=context.get('empresa', ''),
            setor=context.get('setor', ''),
            fatores=json.dumps(context.get('fatores_risco', []), ensure_ascii=False),
        )
        response_text = self.completar(prompt, max_tokens=3000, temperature=0.3)
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {'acao_proposta': response_text, 'recursos': '', 'indicadores': '', 'prazo_sugerido': '90 dias'}

    def gerar_recomendacoes(self, context: dict) -> list:
        """Generate recommendations for a campaign."""
        prompt = PROMPT_RECOMENDACOES.format(
            scores=json.dumps(context.get('scores', {}), ensure_ascii=False, indent=2),
            nivel_geral=context.get('nivel_geral', ''),
            empresa=context.get('empresa', ''),
            total_respondentes=context.get('total_respondentes', 0),
        )
        response_text = self.completar(prompt, max_tokens=2000, temperature=0.4)
        try:
            data = json.loads(response_text)
            return data if isinstance(data, list) else data.get('recomendacoes', [])
        except json.JSONDecodeError:
            return [response_text]

    def analisar_comparacao(self, comparison_data: dict) -> dict:
        """Analyze and compare multiple campaigns."""
        prompt = PROMPT_COMPARACAO_CAMPANHAS.format(
            dados=json.dumps(comparison_data, ensure_ascii=False, indent=2)
        )
        response_text = self.completar(prompt, max_tokens=2000, temperature=0.4)
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {'analise': response_text}


class OpenRouterAIService(AIServiceBase):
    """OpenRouter implementation of AI service."""

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.OPENROUTER_MODEL
        self.base_url = settings.OPENROUTER_BASE_URL

    def completar(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
        response_format: Optional[dict] = None,
        timeout: int = 60,
    ) -> str:
        """Call OpenRouter API."""
        if not self.api_key:
            raise ValueError('OPENROUTER_API_KEY não configurada.')

        url = f'{self.base_url}/chat/completions'
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://vivamente360.com.br',
            'X-Title': 'VIVAMENTE 360',
        }

        payload = {
            'model': self.model,
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': max_tokens,
            'temperature': temperature,
        }

        if response_format:
            payload['response_format'] = response_format

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            content = data['choices'][0]['message']['content']
            return content.strip()
        except requests.exceptions.Timeout:
            logger.error('OpenRouter API timeout after %ds', timeout)
            raise
        except requests.exceptions.HTTPError as e:
            logger.error('OpenRouter API HTTP error: %s - %s', e.response.status_code, e.response.text)
            raise
        except (KeyError, IndexError) as e:
            logger.error('Unexpected OpenRouter response format: %s', e)
            raise ValueError(f'Resposta inesperada da API: {e}')


def get_ai_service() -> AIServiceBase:
    """Factory function - easy to swap AI provider via settings."""
    provider = getattr(settings, 'AI_PROVIDER', 'openrouter')
    if provider == 'openrouter':
        return OpenRouterAIService()
    raise ValueError(f'Unknown AI provider: {provider}')
