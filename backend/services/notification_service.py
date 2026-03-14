"""
Notification service - in-app notifications and email alerts.
Privacy-first: NO PII in alerts, only aggregate/anonymized data.
"""
import logging

from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Manages notifications for users and email alerts.
    Maintains blind-drop privacy - no PII in alerts.
    """

    def criar_notificacao(
        self,
        user: User,
        notification_type: str,
        title: str,
        message: str,
        task=None,
        link_url: str = '',
    ):
        """Create an in-app notification for a user."""
        from apps.core.models import UserNotification
        try:
            notif = UserNotification.objects.create(
                user=user,
                task=task,
                notification_type=notification_type,
                title=title,
                message=message,
                link_url=link_url,
            )
            return notif
        except Exception as e:
            logger.error('Failed to create notification: %s', e)
            return None

    def notificar_tarefa_concluida(self, task):
        """Notify user that their task completed successfully."""
        if not task.user:
            return

        tipo = 'file_ready' if task.file_url else 'task_completed'
        mensagem = f'Sua tarefa "{task.task_type}" foi concluída.'
        if task.file_url:
            mensagem += ' O arquivo está pronto para download.'

        self.criar_notificacao(
            user=task.user,
            notification_type=tipo,
            title='Tarefa Concluída',
            message=mensagem,
            task=task,
            link_url=task.file_url,
        )

    def notificar_tarefa_falhou(self, task):
        """Notify user that their task failed."""
        if not task.user:
            return

        self.criar_notificacao(
            user=task.user,
            notification_type='task_failed',
            title='Tarefa Falhou',
            message=f'Sua tarefa "{task.task_type}" falhou após {task.attempts} tentativas.',
            task=task,
        )

    def alerta_adesao_baixa(self, campaign, empresa):
        """
        Email alert when participation < 50%.
        Sent to RH users of the empresa.
        NO PII included.
        """
        from services.email_service import get_email_service
        from apps.accounts.models import UserProfile

        taxa = campaign.taxa_adesao
        if taxa >= 50:
            return

        usuarios_rh = User.objects.filter(
            profile__role='rh',
            profile__empresas=empresa,
            is_active=True,
        ).exclude(email='')

        email_svc = get_email_service()
        for user in usuarios_rh:
            subject = f'[VIVAMENTE] Alerta: Baixa adesão na campanha "{campaign.nome}"'
            html_body = f"""
            <h2>Alerta de Adesão</h2>
            <p>A campanha <strong>{campaign.nome}</strong> está com taxa de adesão de <strong>{taxa}%</strong>.</p>
            <p>Meta: {campaign.meta_adesao}%</p>
            <p>Considere enviar lembretes ou verificar se os convites foram entregues corretamente.</p>
            <p><em>Equipe VIVAMENTE 360º</em></p>
            """
            email_svc.send(to=user.email, subject=subject, html_body=html_body)
            logger.info('Low adherence alert sent to %s for campaign %s', user.email, campaign.id)

    def alerta_risco_critico(self, setor_nome: str, dimensao_nome: str, empresa):
        """
        Email alert when NR >= 13 (critical risk level).
        NO PII - only sector name, dimension name.
        """
        from services.email_service import get_email_service

        usuarios_rh = User.objects.filter(
            profile__role='rh',
            profile__empresas=empresa,
            is_active=True,
        ).exclude(email='')

        email_svc = get_email_service()
        for user in usuarios_rh:
            subject = f'[VIVAMENTE] ⚠️ Risco Crítico detectado - {setor_nome}'
            html_body = f"""
            <h2>⚠️ Alerta de Risco Psicossocial Crítico</h2>
            <p>Foi detectado um risco <strong>CRÍTICO</strong> na dimensão <strong>{dimensao_nome}</strong>
            no setor <strong>{setor_nome}</strong>.</p>
            <p>De acordo com a NR-1, riscos críticos exigem ação imediata.</p>
            <p>Acesse o painel para visualizar o relatório completo e iniciar um plano de ação.</p>
            <p><em>Equipe VIVAMENTE 360º</em></p>
            """
            email_svc.send(to=user.email, subject=subject, html_body=html_body)
            logger.info('Critical risk alert sent for setor=%s, dim=%s', setor_nome, dimensao_nome)

    def alerta_prazo_vencendo(self, plano_acao, days_remaining: int = 7):
        """Email alert 7 days before action plan deadline."""
        from services.email_service import get_email_service

        if not plano_acao.responsavel:
            return

        usuarios = User.objects.filter(
            profile__empresas=plano_acao.empresa,
            is_active=True,
        ).filter(
            email=plano_acao.responsavel
        )

        email_svc = get_email_service()
        for user in usuarios:
            subject = f'[VIVAMENTE] Prazo vencendo em {days_remaining} dias - Plano de Ação #{plano_acao.id}'
            html_body = f"""
            <h2>Lembrete de Prazo</h2>
            <p>O Plano de Ação <strong>#{plano_acao.id}</strong> vence em
            <strong>{days_remaining} dias</strong> ({plano_acao.prazo}).</p>
            <p><strong>Ação:</strong> {plano_acao.acao_proposta[:200]}...</p>
            <p>Acesse o sistema para atualizar o status do plano.</p>
            """
            email_svc.send(to=user.email, subject=subject, html_body=html_body)


notification_service = NotificationService()
