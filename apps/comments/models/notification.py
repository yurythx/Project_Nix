from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from .comment import Comment
import uuid

User = get_user_model()


class CommentNotification(models.Model):
    """
    Sistema de notificações para comentários
    
    Gerencia notificações em tempo real para:
    - Respostas a comentários
    - Menções em comentários
    - Moderação de comentários
    - Curtidas em comentários
    """
    
    NOTIFICATION_TYPES = [
        ('reply', 'Resposta ao Comentário'),
        ('mention', 'Menção em Comentário'),
        ('like', 'Curtida no Comentário'),
        ('moderation', 'Moderação do Comentário'),
        ('report', 'Comentário Reportado'),
        ('approval', 'Comentário Aprovado'),
        ('rejection', 'Comentário Rejeitado'),
    ]
    
    # Identificador único
    uuid = models.UUIDField(
        'UUID',
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text='Identificador único da notificação'
    )
    
    # Destinatário da notificação
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comment_notifications',
        verbose_name='destinatário',
        help_text='Usuário que receberá a notificação'
    )
    
    # Remetente da notificação (quem causou a ação)
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_comment_notifications',
        verbose_name='remetente',
        help_text='Usuário que causou a notificação'
    )
    
    # Comentário relacionado
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='comentário',
        help_text='Comentário relacionado à notificação'
    )
    
    # Tipo de notificação
    notification_type = models.CharField(
        'tipo',
        max_length=20,
        choices=NOTIFICATION_TYPES,
        help_text='Tipo de notificação'
    )
    
    # Conteúdo da notificação
    title = models.CharField(
        'título',
        max_length=200,
        help_text='Título da notificação'
    )
    
    message = models.TextField(
        'mensagem',
        help_text='Conteúdo da notificação'
    )
    
    # Objeto relacionado (opcional - para contexto adicional)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='tipo de conteúdo'
    )
    object_id = models.PositiveIntegerField(
        'ID do objeto',
        null=True,
        blank=True
    )
    content_object = GenericForeignKey(
        'content_type',
        'object_id'
    )
    
    # Status da notificação
    is_read = models.BooleanField(
        'lida',
        default=False,
        help_text='Se a notificação foi lida'
    )
    
    is_sent = models.BooleanField(
        'enviada',
        default=False,
        help_text='Se a notificação foi enviada (email/push)'
    )
    
    is_real_time_sent = models.BooleanField(
        'enviada em tempo real',
        default=False,
        help_text='Se foi enviada via WebSocket'
    )
    
    # Metadados
    data = models.JSONField(
        'dados adicionais',
        default=dict,
        blank=True,
        help_text='Dados adicionais da notificação'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        'criado em',
        auto_now_add=True
    )
    
    read_at = models.DateTimeField(
        'lida em',
        null=True,
        blank=True,
        help_text='Data e hora em que foi lida'
    )
    
    sent_at = models.DateTimeField(
        'enviada em',
        null=True,
        blank=True,
        help_text='Data e hora em que foi enviada'
    )
    
    class Meta:
        app_label = 'comments'
        verbose_name = 'notificação de comentário'
        verbose_name_plural = 'notificações de comentários'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', 'created_at']),
            models.Index(fields=['comment', 'notification_type']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['is_sent', 'created_at']),
        ]
    
    def __str__(self):
        return f'Notificação para {self.recipient.username}: {self.title}'
    
    def mark_as_read(self):
        """Marca a notificação como lida"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def mark_as_sent(self):
        """Marca a notificação como enviada"""
        if not self.is_sent:
            self.is_sent = True
            self.sent_at = timezone.now()
            self.save(update_fields=['is_sent', 'sent_at'])
    
    def mark_as_real_time_sent(self):
        """Marca como enviada via WebSocket"""
        self.is_real_time_sent = True
        self.save(update_fields=['is_real_time_sent'])
    
    def get_url(self):
        """Retorna URL para a notificação"""
        return self.comment.get_absolute_url()
    
    def to_dict(self):
        """Converte para dicionário (para WebSocket)"""
        return {
            'uuid': str(self.uuid),
            'type': self.notification_type,
            'title': self.title,
            'message': self.message,
            'url': self.get_url(),
            'sender': {
                'username': self.sender.username,
                'avatar': getattr(self.sender, 'avatar', None),
            },
            'comment': {
                'uuid': str(self.comment.uuid),
                'content': self.comment.content[:100] + '...' if len(self.comment.content) > 100 else self.comment.content,
            },
            'created_at': self.created_at.isoformat(),
            'is_read': self.is_read,
            'data': self.data,
        }
    
    @classmethod
    def create_reply_notification(cls, comment, sender):
        """Cria notificação para resposta a comentário"""
        if not comment.parent or comment.parent.author == sender:
            return None
        
        # Evita notificações duplicadas
        existing = cls.objects.filter(
            recipient=comment.parent.author,
            comment=comment,
            notification_type='reply',
            sender=sender
        ).exists()
        
        if existing:
            return None
        
        return cls.objects.create(
            recipient=comment.parent.author,
            sender=sender,
            comment=comment,
            notification_type='reply',
            title=f'{sender.username} respondeu seu comentário',
            message=f'{sender.username} respondeu ao seu comentário: "{comment.content[:100]}..."',
            content_object=comment.content_object,
        )
    
    @classmethod
    def create_mention_notification(cls, comment, mentioned_user, sender):
        """Cria notificação para menção em comentário"""
        if mentioned_user == sender:
            return None
        
        return cls.objects.create(
            recipient=mentioned_user,
            sender=sender,
            comment=comment,
            notification_type='mention',
            title=f'{sender.username} mencionou você',
            message=f'{sender.username} mencionou você em um comentário: "{comment.content[:100]}..."',
            content_object=comment.content_object,
        )
    
    @classmethod
    def create_like_notification(cls, comment, sender):
        """Cria notificação para curtida em comentário"""
        if comment.author == sender:
            return None
        
        # Evita spam de notificações de curtidas
        recent_like = cls.objects.filter(
            recipient=comment.author,
            comment=comment,
            notification_type='like',
            sender=sender,
            created_at__gte=timezone.now() - timezone.timedelta(hours=1)
        ).exists()
        
        if recent_like:
            return None
        
        return cls.objects.create(
            recipient=comment.author,
            sender=sender,
            comment=comment,
            notification_type='like',
            title=f'{sender.username} curtiu seu comentário',
            message=f'{sender.username} curtiu seu comentário: "{comment.content[:100]}..."',
            content_object=comment.content_object,
        )
    
    @classmethod
    def create_moderation_notification(cls, comment, moderator, action, reason=''):
        """Cria notificação para ação de moderação"""
        action_messages = {
            'approved': 'foi aprovado',
            'rejected': 'foi rejeitado',
            'spam': 'foi marcado como spam',
            'deleted': 'foi removido',
        }
        
        action_msg = action_messages.get(action, f'teve status alterado para {action}')
        
        return cls.objects.create(
            recipient=comment.author,
            sender=moderator,
            comment=comment,
            notification_type='moderation',
            title=f'Seu comentário {action_msg}',
            message=f'Seu comentário "{comment.content[:100]}..." {action_msg}.' + 
                   (f' Motivo: {reason}' if reason else ''),
            content_object=comment.content_object,
            data={'action': action, 'reason': reason},
        )


class NotificationPreference(models.Model):
    """
    Preferências de notificação do usuário
    
    Permite que usuários configurem quais notificações desejam receber
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='comment_notification_preferences',
        verbose_name='usuário'
    )
    
    # Notificações por email
    email_on_reply = models.BooleanField(
        'email para respostas',
        default=True,
        help_text='Receber email quando alguém responder seus comentários'
    )
    
    email_on_mention = models.BooleanField(
        'email para menções',
        default=True,
        help_text='Receber email quando for mencionado'
    )
    
    email_on_like = models.BooleanField(
        'email para curtidas',
        default=False,
        help_text='Receber email quando curtirem seus comentários'
    )
    
    email_on_moderation = models.BooleanField(
        'email para moderação',
        default=True,
        help_text='Receber email sobre moderação de comentários'
    )
    
    # Notificações em tempo real
    realtime_on_reply = models.BooleanField(
        'tempo real para respostas',
        default=True,
        help_text='Receber notificações em tempo real para respostas'
    )
    
    realtime_on_mention = models.BooleanField(
        'tempo real para menções',
        default=True,
        help_text='Receber notificações em tempo real para menções'
    )
    
    realtime_on_like = models.BooleanField(
        'tempo real para curtidas',
        default=True,
        help_text='Receber notificações em tempo real para curtidas'
    )
    
    realtime_on_moderation = models.BooleanField(
        'tempo real para moderação',
        default=True,
        help_text='Receber notificações em tempo real para moderação'
    )
    
    # Configurações gerais
    digest_frequency = models.CharField(
        'frequência do resumo',
        max_length=20,
        choices=[
            ('never', 'Nunca'),
            ('daily', 'Diário'),
            ('weekly', 'Semanal'),
            ('monthly', 'Mensal'),
        ],
        default='weekly',
        help_text='Frequência do resumo de notificações por email'
    )
    
    quiet_hours_start = models.TimeField(
        'início do período silencioso',
        null=True,
        blank=True,
        help_text='Hora de início do período sem notificações'
    )
    
    quiet_hours_end = models.TimeField(
        'fim do período silencioso',
        null=True,
        blank=True,
        help_text='Hora de fim do período sem notificações'
    )
    
    # Metadados
    created_at = models.DateTimeField(
        'criado em',
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        'atualizado em',
        auto_now=True
    )
    
    class Meta:
        app_label = 'comments'
        verbose_name = 'preferência de notificação'
        verbose_name_plural = 'preferências de notificação'
    
    def __str__(self):
        return f'Preferências de {self.user.username}'
    
    def should_send_email(self, notification_type):
        """Verifica se deve enviar email para o tipo de notificação"""
        mapping = {
            'reply': self.email_on_reply,
            'mention': self.email_on_mention,
            'like': self.email_on_like,
            'moderation': self.email_on_moderation,
        }
        return mapping.get(notification_type, False)
    
    def should_send_realtime(self, notification_type):
        """Verifica se deve enviar notificação em tempo real"""
        mapping = {
            'reply': self.realtime_on_reply,
            'mention': self.realtime_on_mention,
            'like': self.realtime_on_like,
            'moderation': self.realtime_on_moderation,
        }
        return mapping.get(notification_type, False)
    
    def is_quiet_time(self):
        """Verifica se está no período silencioso"""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        now = timezone.now().time()
        
        if self.quiet_hours_start <= self.quiet_hours_end:
            # Mesmo dia (ex: 22:00 - 08:00)
            return self.quiet_hours_start <= now <= self.quiet_hours_end
        else:
            # Atravessa meia-noite (ex: 22:00 - 08:00)
            return now >= self.quiet_hours_start or now <= self.quiet_hours_end