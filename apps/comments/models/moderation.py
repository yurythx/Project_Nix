from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from .comment import Comment

User = get_user_model()


class CommentModeration(models.Model):
    """
    Configurações de moderação para diferentes tipos de conteúdo
    
    Permite configurar regras específicas de moderação para cada app/modelo
    """
    
    MODERATION_CHOICES = [
        ('auto_approve', 'Aprovação Automática'),
        ('manual_review', 'Revisão Manual'),
        ('auto_reject', 'Rejeição Automática'),
    ]
    
    # Tipo de conteúdo
    app_label = models.CharField(
        'app',
        max_length=100,
        help_text='Nome do app (ex: books, pages)'
    )
    
    model_name = models.CharField(
        'modelo',
        max_length=100,
        help_text='Nome do modelo (ex: Book, Page)'
    )
    
    # Configurações de moderação
    moderation_type = models.CharField(
        'tipo de moderação',
        max_length=20,
        choices=MODERATION_CHOICES,
        default='manual_review',
        help_text='Tipo de moderação aplicada'
    )
    
    # Configurações específicas
    auto_approve_trusted_users = models.BooleanField(
        'aprovar usuários confiáveis',
        default=True,
        help_text='Aprova automaticamente comentários de usuários confiáveis'
    )
    
    require_email_verification = models.BooleanField(
        'exigir email verificado',
        default=True,
        help_text='Exige que o usuário tenha email verificado'
    )
    
    max_comment_length = models.PositiveIntegerField(
        'tamanho máximo',
        default=1000,
        help_text='Tamanho máximo do comentário em caracteres'
    )
    
    min_comment_length = models.PositiveIntegerField(
        'tamanho mínimo',
        default=3,
        help_text='Tamanho mínimo do comentário em caracteres'
    )
    
    # Filtros de spam
    enable_spam_filter = models.BooleanField(
        'filtro de spam',
        default=True,
        help_text='Habilita filtro automático de spam'
    )
    
    blocked_words = models.TextField(
        'palavras bloqueadas',
        blank=True,
        help_text='Lista de palavras bloqueadas (uma por linha)'
    )
    
    blocked_ips = models.TextField(
        'IPs bloqueados',
        blank=True,
        help_text='Lista de IPs bloqueados (um por linha)'
    )
    
    # Rate limiting
    max_comments_per_hour = models.PositiveIntegerField(
        'comentários por hora',
        default=10,
        help_text='Máximo de comentários por usuário por hora'
    )
    
    max_comments_per_day = models.PositiveIntegerField(
        'comentários por dia',
        default=50,
        help_text='Máximo de comentários por usuário por dia'
    )
    
    # Configurações de notificação
    notify_moderators = models.BooleanField(
        'notificar moderadores',
        default=True,
        help_text='Notifica moderadores sobre novos comentários'
    )
    
    notify_authors = models.BooleanField(
        'notificar autores',
        default=True,
        help_text='Notifica autores sobre respostas'
    )
    
    # Metadados
    is_active = models.BooleanField(
        'ativo',
        default=True,
        help_text='Se esta configuração está ativa'
    )
    
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
        verbose_name = 'configuração de moderação'
        verbose_name_plural = 'configurações de moderação'
        unique_together = ['app_label', 'model_name']
        indexes = [
            models.Index(fields=['app_label', 'model_name']),
        ]
    
    def __str__(self):
        return f'Moderação para {self.app_label}.{self.model_name}'
    
    def get_blocked_words_list(self):
        """Retorna lista de palavras bloqueadas"""
        if not self.blocked_words:
            return []
        return [word.strip().lower() for word in self.blocked_words.split('\n') if word.strip()]
    
    def get_blocked_ips_list(self):
        """Retorna lista de IPs bloqueados"""
        if not self.blocked_ips:
            return []
        return [ip.strip() for ip in self.blocked_ips.split('\n') if ip.strip()]
    
    def should_auto_approve(self, user, content, ip_address=None):
        """Determina se um comentário deve ser aprovado automaticamente"""
        if self.moderation_type == 'auto_reject':
            return False
        
        if self.moderation_type == 'auto_approve':
            return True
        
        # Verificações para aprovação automática
        if self.auto_approve_trusted_users and user.is_staff:
            return True
        
        if self.require_email_verification and not getattr(user, 'is_verified', True):
            return False
        
        # Verifica palavras bloqueadas
        if self.enable_spam_filter:
            blocked_words = self.get_blocked_words_list()
            content_lower = content.lower()
            if any(word in content_lower for word in blocked_words):
                return False
        
        # Verifica IP bloqueado
        if ip_address and ip_address in self.get_blocked_ips_list():
            return False
        
        # Verifica rate limiting
        if not self.check_rate_limit(user):
            return False
        
        return self.moderation_type == 'auto_approve'
    
    def check_rate_limit(self, user):
        """Verifica se o usuário não excedeu o limite de comentários"""
        now = timezone.now()
        
        # Verifica limite por hora
        hour_ago = now - timezone.timedelta(hours=1)
        comments_last_hour = Comment.objects.filter(
            author=user,
            created_at__gte=hour_ago
        ).count()
        
        if comments_last_hour >= self.max_comments_per_hour:
            return False
        
        # Verifica limite por dia
        day_ago = now - timezone.timedelta(days=1)
        comments_last_day = Comment.objects.filter(
            author=user,
            created_at__gte=day_ago
        ).count()
        
        if comments_last_day >= self.max_comments_per_day:
            return False
        
        return True


class ModerationAction(models.Model):
    """
    Registro de ações de moderação realizadas
    
    Mantém histórico de todas as ações de moderação para auditoria
    """
    
    ACTION_CHOICES = [
        ('approved', 'Aprovado'),
        ('rejected', 'Rejeitado'),
        ('spam', 'Marcado como Spam'),
        ('deleted', 'Deletado'),
        ('edited', 'Editado'),
        ('pinned', 'Fixado'),
        ('unpinned', 'Desfixado'),
    ]
    
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='moderation_actions',
        verbose_name='comentário'
    )
    
    moderator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='moderation_actions',
        verbose_name='moderador'
    )
    
    action = models.CharField(
        'ação',
        max_length=20,
        choices=ACTION_CHOICES,
        help_text='Ação realizada'
    )
    
    reason = models.TextField(
        'motivo',
        blank=True,
        help_text='Motivo da ação de moderação'
    )
    
    # Dados antes da ação (para auditoria)
    previous_status = models.CharField(
        'status anterior',
        max_length=20,
        blank=True,
        help_text='Status do comentário antes da ação'
    )
    
    previous_content = models.TextField(
        'conteúdo anterior',
        blank=True,
        help_text='Conteúdo do comentário antes da edição'
    )
    
    # Metadados
    ip_address = models.GenericIPAddressField(
        'endereço IP',
        null=True,
        blank=True,
        help_text='IP do moderador'
    )
    
    user_agent = models.TextField(
        'user agent',
        blank=True,
        help_text='User agent do moderador'
    )
    
    created_at = models.DateTimeField(
        'criado em',
        auto_now_add=True
    )
    
    class Meta:
        app_label = 'comments'
        verbose_name = 'ação de moderação'
        verbose_name_plural = 'ações de moderação'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['comment', 'created_at']),
            models.Index(fields=['moderator', 'created_at']),
            models.Index(fields=['action', 'created_at']),
        ]
    
    def __str__(self):
        return f'{self.moderator.username} {self.action} comentário {self.comment.uuid}'


class ModerationQueue(models.Model):
    """
    Fila de moderação para comentários pendentes
    
    Organiza comentários que precisam de revisão manual
    """
    
    PRIORITY_CHOICES = [
        ('low', 'Baixa'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    
    comment = models.OneToOneField(
        Comment,
        on_delete=models.CASCADE,
        related_name='moderation_queue',
        verbose_name='comentário'
    )
    
    priority = models.CharField(
        'prioridade',
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal',
        help_text='Prioridade na fila de moderação'
    )
    
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_moderation_queue',
        verbose_name='atribuído para',
        help_text='Moderador responsável'
    )
    
    # Flags automáticas
    is_spam_suspected = models.BooleanField(
        'suspeita de spam',
        default=False,
        help_text='Se o comentário é suspeito de spam'
    )
    
    is_reported = models.BooleanField(
        'reportado',
        default=False,
        help_text='Se o comentário foi reportado por usuários'
    )
    
    reports_count = models.PositiveIntegerField(
        'número de reports',
        default=0,
        help_text='Número de vezes que foi reportado'
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
        verbose_name = 'fila de moderação'
        verbose_name_plural = 'filas de moderação'
        ordering = ['-priority', '-reports_count', 'created_at']
        indexes = [
            models.Index(fields=['priority', 'created_at']),
            models.Index(fields=['assigned_to', 'created_at']),
            models.Index(fields=['is_spam_suspected']),
            models.Index(fields=['is_reported']),
        ]
    
    def __str__(self):
        return f'Moderação: {self.comment}'
    
    def assign_to_moderator(self, moderator):
        """Atribui comentário a um moderador"""
        self.assigned_to = moderator
        self.save(update_fields=['assigned_to', 'updated_at'])
    
    def mark_as_spam_suspected(self):
        """Marca como suspeita de spam"""
        self.is_spam_suspected = True
        self.priority = 'high'
        self.save(update_fields=['is_spam_suspected', 'priority', 'updated_at'])
    
    def add_report(self):
        """Adiciona um report ao comentário"""
        self.reports_count += 1
        self.is_reported = True
        
        # Aumenta prioridade baseado no número de reports
        if self.reports_count >= 5:
            self.priority = 'urgent'
        elif self.reports_count >= 3:
            self.priority = 'high'
        
        self.save(update_fields=['reports_count', 'is_reported', 'priority', 'updated_at'])