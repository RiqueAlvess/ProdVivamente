"""
Responses views - Multi-step survey form.
Token-based, no JWT required for respondents.
Rate limit: 100/hour per IP.
"""
import logging

from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import SurveyResponse
from .serializers import (
    LGPDSerializer, DemographicsSerializer, AnswerSerializer, SubmitSerializer,
    SurveyResponseSerializer,
)
from apps.invitations.models import SurveyInvitation
from apps.surveys.models import Pergunta

logger = logging.getLogger(__name__)

RATE_100H = ratelimit(key='ip', rate='100/h', method='POST', block=True)


def get_valid_invitation(token):
    """Validate token and return invitation or raise appropriate error."""
    try:
        invitation = SurveyInvitation.objects.select_related(
            'campaign', 'unidade', 'setor', 'empresa'
        ).get(hash_token=token)
    except SurveyInvitation.DoesNotExist:
        return None, 'Token inválido.'

    if invitation.status == 'used':
        return None, 'Este link já foi utilizado.'
    if invitation.status == 'expired':
        return None, 'Este link expirou.'
    if invitation.is_expired:
        invitation.status = 'expired'
        invitation.save(update_fields=['status'])
        return None, 'Este link expirou.'
    if invitation.campaign.status != 'active':
        return None, 'Esta pesquisa não está mais ativa.'

    return invitation, None


class SurveyStatusView(APIView):
    """
    GET /api/responses/survey/{token}/status/
    Returns current status of the token/invitation.
    No rate limit on GET.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        invitation, error = get_valid_invitation(token)
        if error:
            return Response({'valid': False, 'error': error}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'valid': True,
            'status': invitation.status,
            'campaign': invitation.campaign.nome,
            'empresa': invitation.empresa.nome_app,
            'expires_at': invitation.expires_at,
        })


@method_decorator(RATE_100H, name='post')
class SurveyLGPDView(APIView):
    """
    POST /api/responses/survey/{token}/lgpd/
    Step 1: Accept LGPD terms. Creates session-like state in invitation.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, token):
        invitation, error = get_valid_invitation(token)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        serializer = LGPDSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Mark invitation as started (sent -> still active until used)
        if invitation.status == 'pending':
            invitation.status = 'sent'
            invitation.sent_at = timezone.now()
            invitation.save(update_fields=['status', 'sent_at'])

        return Response({
            'status': 'ok',
            'message': 'Termos LGPD aceitos. Prossiga com a pesquisa.',
            'next_step': 'demographics',
        })


@method_decorator(RATE_100H, name='post')
class SurveyDemographicsView(APIView):
    """
    POST /api/responses/survey/{token}/demographics/
    Step 2: Save demographic info (all optional).
    Stored in session cache keyed by token.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, token):
        invitation, error = get_valid_invitation(token)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        serializer = DemographicsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Store demographics in Django cache keyed by token
        from django.core.cache import cache
        cache_key = f'survey_session_{token}'
        session_data = cache.get(cache_key, {})
        session_data['demographics'] = serializer.validated_data
        session_data['lgpd_aceito'] = True
        cache.set(cache_key, session_data, timeout=86400)  # 24h

        return Response({
            'status': 'ok',
            'message': 'Dados demográficos salvos.',
            'next_step': 'answer',
        })


@method_decorator(RATE_100H, name='post')
class SurveyAnswerView(APIView):
    """
    POST /api/responses/survey/{token}/answer/
    Step 3 (repeated): Save answer for each question.
    Body: {step: 1-35, value: 0-4}
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, token):
        invitation, error = get_valid_invitation(token)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        step = serializer.validated_data['step']
        value = serializer.validated_data['value']

        from django.core.cache import cache
        cache_key = f'survey_session_{token}'
        session_data = cache.get(cache_key, {})

        if not session_data.get('lgpd_aceito'):
            return Response(
                {'error': 'É necessário aceitar os termos LGPD primeiro.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        answers = session_data.get('answers', {})
        answers[str(step)] = value
        session_data['answers'] = answers
        cache.set(cache_key, session_data, timeout=86400)

        answered_count = len(answers)
        remaining = 35 - answered_count

        return Response({
            'status': 'ok',
            'step': step,
            'answered': answered_count,
            'remaining': remaining,
            'next_step': 'submit' if answered_count >= 35 else 'answer',
        })


@method_decorator(RATE_100H, name='post')
class SurveySubmitView(APIView):
    """
    POST /api/responses/survey/{token}/submit/
    Final step: Create SurveyResponse record (blind drop).
    Invitation is marked as used AFTER creating the response.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, token):
        invitation, error = get_valid_invitation(token)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from django.core.cache import cache
        cache_key = f'survey_session_{token}'
        session_data = cache.get(cache_key, {})

        if not session_data.get('lgpd_aceito'):
            return Response(
                {'error': 'É necessário aceitar os termos LGPD primeiro.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        answers = session_data.get('answers', {})
        if len(answers) < 35:
            return Response(
                {'error': f'Apenas {len(answers)} de 35 perguntas respondidas.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        demographics = session_data.get('demographics', {})

        # Create the response - BLIND DROP (no FK to invitation, user, or cargo)
        survey_response = SurveyResponse.objects.create(
            campaign=invitation.campaign,
            unidade=invitation.unidade,
            setor=invitation.setor,
            faixa_etaria=demographics.get('faixa_etaria', ''),
            tempo_empresa=demographics.get('tempo_empresa', ''),
            genero=demographics.get('genero', ''),
            respostas=answers,
            comentario_livre=serializer.validated_data.get('comentario_livre', ''),
            lgpd_aceito=True,
        )

        # Mark invitation as used AFTER creating response (atomic safety)
        invitation.mark_as_used()

        # Clear session cache
        cache.delete(cache_key)

        # Trigger async sentiment analysis if comment exists
        if survey_response.comentario_livre:
            try:
                from tasks.ai_analysis_tasks import analyze_sentiment
                analyze_sentiment.delay(survey_response.id)
            except Exception:
                pass  # Don't fail submission if task dispatch fails

        return Response({
            'status': 'completed',
            'message': 'Obrigado! Sua resposta foi registrada com sucesso.',
            'response_id': survey_response.id,
        }, status=status.HTTP_201_CREATED)


class ResponseListView(APIView):
    """GET /api/responses/ - Admin/RH view of responses"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.is_staff or user.is_superuser:
            qs = SurveyResponse.objects.all()
        elif hasattr(user, 'profile'):
            qs = SurveyResponse.objects.filter(
                campaign__empresa__in=user.profile.empresas.all()
            )
        else:
            return Response([], status=status.HTTP_200_OK)

        campaign_id = request.query_params.get('campaign_id')
        setor_id = request.query_params.get('setor_id')
        unidade_id = request.query_params.get('unidade_id')

        if campaign_id:
            qs = qs.filter(campaign_id=campaign_id)
        if setor_id:
            qs = qs.filter(setor_id=setor_id)
        if unidade_id:
            qs = qs.filter(unidade_id=unidade_id)

        qs = qs.select_related('campaign', 'unidade', 'setor').order_by('-created_at')[:500]
        serializer = SurveyResponseSerializer(qs, many=True)
        return Response(serializer.data)
