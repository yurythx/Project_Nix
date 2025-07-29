from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .comments import ChapterComment
from .capitulo import Capitulo

User = get_user_model()

class Notification(models.Model):
    """
    Modelo para notificações do sistema.
    """
    NOTIFICATION_TYPES = [
        ('comment_reply', _('Resposta ao Comentário')),
        ('comment_reaction', _('Reação ao Comentário')),
        ('new_chapter', _('Novo Capítulo')),
        ('chapter_update', _('Capítulo Atualizado')),
        ('download_complete', _('Download Concluído')),
        ('moderation_action', _('Ação de Moderação')),
        ('system_announcement', _('Anúncio do Sistema')),
        ('manga_follow', _('Novo Seguidor')),
        ('comment_mention', _('Menção em Comentário')),
    ]

    PRIORITY_CHOICES = [
        ('low', _('Baixa')),
        ('normal', _('Normal')),
        ('high', _('Alta')),
        ('urgent', _('Urgente')),
    ]

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Destinatário')
    )
    notification_type = models.CharField(
        _('Tipo de Notificação'),
        max_length=30,
        choices=NOTIFICATION_TYPES
    )
    title = models.CharField(
        _('Título'),
        max_length=200
    )
    message = models.TextField(
        _('Mensagem'),
        max_length=1000
    )
    data = models.JSONField(
        _('Dados Adicionais'),
        default=dict,
        blank=True,
        help_text=_('Dados extras para a notificação (URLs, IDs, etc.)')
    )
    priority = models.CharField(
        _('Prioridade'),
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal'
    )
    is_read = models.BooleanField(
        _('Lida'),
        default=False
    )
    is_sent = models.BooleanField(
        _('Enviada'),
        default=False,
        help_text=_('Se a notificação foi enviada via push/email')
    )
    sent_at = models.DateTimeField(
        _('Enviada em'),
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        _('Criada em'),
        auto_now_add=True
    )
    expires_at = models.DateTimeField(
        _('Expira em'),
        null=True,
        blank=True,
        help_text=_('Data de expiração da notificação')
    )

    class Meta:
        app_label = 'mangas'
        verbose_name = _('Notificação')
        verbose_name_plural = _('Notificações')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read'], name='notification_recipient_read_idx'),
            models.Index(fields=['notification_type', 'created_at'], name='notification_type_date_idx'),
            models.Index(fields=['priority', 'created_at'], name='notification_priority_date_idx'),
        ]

    def __str__(self):
        return f"{self.recipient.username} - {self.title}"

    @property
    def is_expired(self):
        """Verifica se a notificação expirou."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def mark_as_read(self):
        """Marca a notificação como lida."""
        self.is_read = True
        self.save(update_fields=['is_read'])

    def mark_as_sent(self):
        """Marca a notificação como enviada."""
        self.is_sent = True
        self.sent_at = timezone.now()
        self.save(update_fields=['is_sent', 'sent_at'])

class PushSubscription(models.Model):
    """
    Modelo para assinaturas de notificações push.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='push_subscriptions',
        verbose_name=_('Usuário')
    )
    endpoint = models.URLField(
        _('Endpoint'),
        max_length=500,
        help_text=_('URL do endpoint do service worker')
    )
    p256dh_key = models.CharField(
        _('P256DH Key'),
        max_length=200,
        help_text=_('Chave pública para criptografia')
    )
    auth_token = models.CharField(
        _('Auth Token'),
        max_length=200,
        help_text=_('Token de autenticação')
    )
    device_info = models.JSONField(
        _('Informações do Dispositivo'),
        default=dict,
        blank=True,
        help_text=_('Informações sobre o dispositivo (navegador, OS, etc.)')
    )
    is_active = models.BooleanField(
        _('Ativa'),
        default=True
    )
    created_at = models.DateTimeField(
        _('Criado em'),
        auto_now_add=True
    )
    last_used = models.DateTimeField(
        _('Último Uso'),
        auto_now=True
    )

    class Meta:
        app_label = 'mangas'
        verbose_name = _('Assinatura Push')
        verbose_name_plural = _('Assinaturas Push')
        unique_together = ('user', 'endpoint')
        indexes = [
            models.Index(fields=['user', 'is_active'], name='push_subscription_user_active_idx'),
            models.Index(fields=['is_active', 'last_used'], name='push_subscription_active_used_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.endpoint[:50]}..."

class NotificationPreference(models.Model):
    """
    Modelo para preferências de notificação do usuário.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name=_('Usuário')
    )
    # Preferências por tipo de notificação
    comment_replies = models.BooleanField(
        _('Respostas a Comentários'),
        default=True
    )
    comment_reactions = models.BooleanField(
        _('Reações a Comentários'),
        default=True
    )
    new_chapters = models.BooleanField(
        _('Novos Capítulos'),
        default=True
    )
    chapter_updates = models.BooleanField(
        _('Atualizações de Capítulos'),
        default=False
    )
    download_complete = models.BooleanField(
        _('Downloads Concluídos'),
        default=True
    )
    moderation_actions = models.BooleanField(
        _('Ações de Moderação'),
        default=True
    )
    system_announcements = models.BooleanField(
        _('Anúncios do Sistema'),
        default=True
    )
    manga_follows = models.BooleanField(
        _('Novos Seguidores'),
        default=True
    )
    comment_mentions = models.BooleanField(
        _('Menções em Comentários'),
        default=True
    )
    
    # Preferências de entrega
    push_notifications = models.BooleanField(
        _('Notificações Push'),
        default=True
    )
    email_notifications = models.BooleanField(
        _('Notificações por Email'),
        default=True
    )
    browser_notifications = models.BooleanField(
        _('Notificações do Navegador'),
        default=True
    )
    
    # Configurações de frequência
    notification_frequency = models.CharField(
        _('Frequência de Notificações'),
        max_length=20,
        choices=[
            ('immediate', _('Imediata')),
            ('hourly', _('A cada hora')),
            ('daily', _('Diária')),
            ('weekly', _('Semanal')),
        ],
        default='immediate'
    )
    
    # Horário de silêncio
    quiet_hours_start = models.TimeField(
        _('Início do Horário Silencioso'),
        null=True,
        blank=True,
        help_text=_('Hora de início do período silencioso (formato HH:MM)')
    )
    quiet_hours_end = models.TimeField(
        _('Fim do Horário Silencioso'),
        null=True,
        blank=True,
        help_text=_('Hora de fim do período silencioso (formato HH:MM)')
    )
    
    created_at = models.DateTimeField(
        _('Criado em'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Atualizado em'),
        auto_now=True
    )

    class Meta:
        app_label = 'mangas'
        verbose_name = _('Preferência de Notificação')
        verbose_name_plural = _('Preferências de Notificação')

    def __str__(self):
        return f"Preferências de {self.user.username}"

    @property
    def is_in_quiet_hours(self):
        """Verifica se está no horário silencioso."""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        now = timezone.now().time()
        start = self.quiet_hours_start
        end = self.quiet_hours_end
        
        if start <= end:
            return start <= now <= end
        else:  # Horário silencioso atravessa a meia-noite
            return now >= start or now <= end

class NotificationTemplate(models.Model):
    """
    Modelo para templates de notificação.
    """
    name = models.CharField(
        _('Nome'),
        max_length=100,
        unique=True
    )
    notification_type = models.CharField(
        _('Tipo de Notificação'),
        max_length=30,
        choices=Notification.NOTIFICATION_TYPES
    )
    title_template = models.CharField(
        _('Template do Título'),
        max_length=200,
        help_text=_('Template com variáveis {user}, {manga}, {chapter}, etc.')
    )
    message_template = models.TextField(
        _('Template da Mensagem'),
        max_length=1000,
        help_text=_('Template com variáveis {user}, {manga}, {chapter}, etc.')
    )
    is_active = models.BooleanField(
        _('Ativo'),
        default=True
    )
    created_at = models.DateTimeField(
        _('Criado em'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Atualizado em'),
        auto_now=True
    )

    class Meta:
        app_label = 'mangas'
        verbose_name = _('Template de Notificação')
        verbose_name_plural = _('Templates de Notificação')
        ordering = ['name']

    def __str__(self):
        return self.name

    def render(self, context):
        """Renderiza o template com o contexto fornecido."""
        title = self.title_template
        message = self.message_template
        
        for key, value in context.items():
            title = title.replace(f'{{{key}}}', str(value))
            message = message.replace(f'{{{key}}}', str(value))
        
        return title, message 