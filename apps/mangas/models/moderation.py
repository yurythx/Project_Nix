from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .comments import ChapterComment
from .notifications import Notification

User = get_user_model()

class ModerationRule(models.Model):
    """
    Modelo para regras de moderação automática.
    """
    RULE_TYPES = [
        ('keyword_filter', _('Filtro de Palavras-chave')),
        ('spam_detection', _('Detecção de Spam')),
        ('toxicity_detection', _('Detecção de Toxicidade')),
        ('length_limit', _('Limite de Comprimento')),
        ('frequency_limit', _('Limite de Frequência')),
        ('user_reputation', _('Reputação do Usuário')),
        ('content_pattern', _('Padrão de Conteúdo')),
    ]

    ACTION_CHOICES = [
        ('flag', _('Marcar para Revisão')),
        ('auto_delete', _('Deletar Automaticamente')),
        ('warn_user', _('Avisar Usuário')),
        ('temp_ban', _('Banimento Temporário')),
        ('permanent_ban', _('Banimento Permanente')),
        ('require_approval', _('Requer Aprovação')),
    ]

    SEVERITY_CHOICES = [
        ('low', _('Baixa')),
        ('medium', _('Média')),
        ('high', _('Alta')),
        ('critical', _('Crítica')),
    ]

    name = models.CharField(
        _('Nome da Regra'),
        max_length=100
    )
    rule_type = models.CharField(
        _('Tipo de Regra'),
        max_length=30,
        choices=RULE_TYPES
    )
    description = models.TextField(
        _('Descrição'),
        blank=True
    )
    conditions = models.JSONField(
        _('Condições'),
        default=dict,
        help_text=_('Condições da regra em formato JSON')
    )
    action = models.CharField(
        _('Ação'),
        max_length=20,
        choices=ACTION_CHOICES
    )
    severity = models.CharField(
        _('Severidade'),
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='medium'
    )
    is_active = models.BooleanField(
        _('Ativa'),
        default=True
    )
    priority = models.PositiveIntegerField(
        _('Prioridade'),
        default=0,
        help_text=_('Prioridade da regra (maior número = maior prioridade)')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_moderation_rules',
        verbose_name=_('Criado por')
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
        verbose_name = _('Regra de Moderação')
        verbose_name_plural = _('Regras de Moderação')
        ordering = ['-priority', 'name']
        indexes = [
            models.Index(fields=['rule_type', 'is_active'], name='moderation_rule_type_active_idx'),
            models.Index(fields=['severity', 'is_active'], name='moderation_rule_severity_active_idx'),
        ]

    def __str__(self):
        return self.name

    def evaluate(self, content, user, context=None):
        """
        Avalia se o conteúdo viola esta regra.
        Retorna (violates, confidence, details)
        """
        if not self.is_active:
            return False, 0, {}
        
        if self.rule_type == 'keyword_filter':
            return self._evaluate_keyword_filter(content)
        elif self.rule_type == 'spam_detection':
            return self._evaluate_spam_detection(content, user, context)
        elif self.rule_type == 'length_limit':
            return self._evaluate_length_limit(content)
        elif self.rule_type == 'frequency_limit':
            return self._evaluate_frequency_limit(user, context)
        elif self.rule_type == 'user_reputation':
            return self._evaluate_user_reputation(user)
        
        return False, 0, {}

    def _evaluate_keyword_filter(self, content):
        """Avalia filtro de palavras-chave."""
        keywords = self.conditions.get('keywords', [])
        if not keywords:
            return False, 0, {}
        
        content_lower = content.lower()
        found_keywords = [kw for kw in keywords if kw.lower() in content_lower]
        
        if found_keywords:
            confidence = min(len(found_keywords) / len(keywords), 1.0)
            return True, confidence, {'found_keywords': found_keywords}
        
        return False, 0, {}

    def _evaluate_spam_detection(self, content, user, context):
        """Avalia detecção de spam."""
        # Verificar repetição de caracteres
        char_repetition = self._check_char_repetition(content)
        if char_repetition > 0.3:  # Mais de 30% de repetição
            return True, char_repetition, {'reason': 'char_repetition'}
        
        # Verificar links suspeitos
        suspicious_links = self._check_suspicious_links(content)
        if suspicious_links:
            return True, 0.8, {'reason': 'suspicious_links', 'links': suspicious_links}
        
        # Verificar padrões de spam
        spam_patterns = self.conditions.get('spam_patterns', [])
        for pattern in spam_patterns:
            if pattern.lower() in content.lower():
                return True, 0.9, {'reason': 'spam_pattern', 'pattern': pattern}
        
        return False, 0, {}

    def _evaluate_length_limit(self, content):
        """Avalia limite de comprimento."""
        min_length = self.conditions.get('min_length', 0)
        max_length = self.conditions.get('max_length', float('inf'))
        
        content_length = len(content)
        
        if content_length < min_length:
            return True, 1.0, {'reason': 'too_short', 'length': content_length, 'min_required': min_length}
        elif content_length > max_length:
            return True, 1.0, {'reason': 'too_long', 'length': content_length, 'max_allowed': max_length}
        
        return False, 0, {}

    def _evaluate_frequency_limit(self, user, context):
        """Avalia limite de frequência."""
        max_comments_per_hour = self.conditions.get('max_comments_per_hour', 10)
        max_comments_per_day = self.conditions.get('max_comments_per_day', 50)
        
        now = timezone.now()
        one_hour_ago = now - timezone.timedelta(hours=1)
        one_day_ago = now - timezone.timedelta(days=1)
        
        hourly_count = ChapterComment.objects.filter(
            user=user,
            created_at__gte=one_hour_ago
        ).count()
        
        daily_count = ChapterComment.objects.filter(
            user=user,
            created_at__gte=one_day_ago
        ).count()
        
        if hourly_count >= max_comments_per_hour:
            return True, 1.0, {'reason': 'hourly_limit_exceeded', 'count': hourly_count, 'limit': max_comments_per_hour}
        elif daily_count >= max_comments_per_day:
            return True, 1.0, {'reason': 'daily_limit_exceeded', 'count': daily_count, 'limit': max_comments_per_day}
        
        return False, 0, {}

    def _evaluate_user_reputation(self, user):
        """Avalia reputação do usuário."""
        min_reputation = self.conditions.get('min_reputation', 0)
        
        # Calcular reputação baseada em reports, comentários deletados, etc.
        reputation = self._calculate_user_reputation(user)
        
        if reputation < min_reputation:
            return True, 1.0, {'reason': 'low_reputation', 'reputation': reputation, 'min_required': min_reputation}
        
        return False, 0, {}

    def _check_char_repetition(self, content):
        """Verifica repetição de caracteres."""
        if len(content) < 10:
            return 0
        
        char_counts = {}
        for char in content:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        max_repetition = max(char_counts.values())
        return max_repetition / len(content)

    def _check_suspicious_links(self, content):
        """Verifica links suspeitos."""
        import re
        suspicious_domains = self.conditions.get('suspicious_domains', [])
        
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, content)
        
        suspicious_links = []
        for url in urls:
            for domain in suspicious_domains:
                if domain in url:
                    suspicious_links.append(url)
                    break
        
        return suspicious_links

    def _calculate_user_reputation(self, user):
        """Calcula reputação do usuário."""
        # Base: 100 pontos
        reputation = 100
        
        # Penalizar por reports
        reports_received = ChapterComment.objects.filter(
            user=user,
            reports__isnull=False
        ).count()
        reputation -= reports_received * 10
        
        # Penalizar por comentários deletados
        deleted_comments = ChapterComment.objects.filter(
            user=user,
            is_deleted=True
        ).count()
        reputation -= deleted_comments * 20
        
        # Bonificar por comentários bem recebidos
        positive_reactions = sum(
            comment.reactions.filter(
                reaction_type__in=['like', 'love', 'laugh']
            ).count()
            for comment in ChapterComment.objects.filter(user=user, is_deleted=False)
        )
        reputation += positive_reactions * 2
        
        return max(0, reputation)

class ModerationAction(models.Model):
    """
    Modelo para ações de moderação executadas.
    """
    comment = models.ForeignKey(
        ChapterComment,
        on_delete=models.CASCADE,
        related_name='moderation_actions',
        verbose_name=_('Comentário')
    )
    rule = models.ForeignKey(
        ModerationRule,
        on_delete=models.SET_NULL,
        null=True,
        related_name='actions',
        verbose_name=_('Regra')
    )
    moderator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderation_actions',
        verbose_name=_('Moderador')
    )
    action_type = models.CharField(
        _('Tipo de Ação'),
        max_length=20,
        choices=ModerationRule.ACTION_CHOICES
    )
    reason = models.TextField(
        _('Motivo'),
        blank=True
    )
    confidence = models.FloatField(
        _('Confiança'),
        default=0.0,
        help_text=_('Nível de confiança da ação (0.0 a 1.0)')
    )
    details = models.JSONField(
        _('Detalhes'),
        default=dict,
        blank=True
    )
    is_automated = models.BooleanField(
        _('Automática'),
        default=False
    )
    created_at = models.DateTimeField(
        _('Criado em'),
        auto_now_add=True
    )

    class Meta:
        app_label = 'mangas'
        verbose_name = _('Ação de Moderação')
        verbose_name_plural = _('Ações de Moderação')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action_type', 'created_at'], name='moderation_action_type_date_idx'),
            models.Index(fields=['is_automated', 'created_at'], name='moderation_action_automated_date_idx'),
        ]

    def __str__(self):
        return f"{self.action_type} - {self.comment.id}"

    def execute(self):
        """Executa a ação de moderação."""
        if self.action_type == 'auto_delete':
            self.comment.soft_delete()
        elif self.action_type == 'warn_user':
            self._send_warning_notification()
        elif self.action_type == 'temp_ban':
            self._apply_temporary_ban()
        elif self.action_type == 'permanent_ban':
            self._apply_permanent_ban()
        elif self.action_type == 'require_approval':
            self._mark_for_approval()

    def _send_warning_notification(self):
        """Envia notificação de aviso ao usuário."""
        Notification.objects.create(
            recipient=self.comment.user,
            notification_type='moderation_action',
            title='Aviso de Moderação',
            message=f'Seu comentário foi marcado para revisão. Motivo: {self.reason}',
            data={'comment_id': self.comment.id, 'action_type': self.action_type}
        )

    def _apply_temporary_ban(self):
        """Aplica banimento temporário."""
        ban_duration = self.details.get('ban_duration', 24)  # horas
        # Implementar lógica de banimento temporário
        pass

    def _apply_permanent_ban(self):
        """Aplica banimento permanente."""
        # Implementar lógica de banimento permanente
        pass

    def _mark_for_approval(self):
        """Marca comentário para aprovação manual."""
        # Implementar lógica de aprovação manual
        pass

class ModerationQueue(models.Model):
    """
    Modelo para fila de moderação manual.
    """
    comment = models.ForeignKey(
        ChapterComment,
        on_delete=models.CASCADE,
        related_name='moderation_queue_entries',
        verbose_name=_('Comentário')
    )
    priority = models.CharField(
        _('Prioridade'),
        max_length=10,
        choices=ModerationRule.SEVERITY_CHOICES,
        default='medium'
    )
    flagged_by_rules = models.ManyToManyField(
        ModerationRule,
        related_name='flagged_comments',
        verbose_name=_('Regras que Flaggaram')
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_moderation_queue',
        verbose_name=_('Atribuído a')
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=[
            ('pending', _('Pendente')),
            ('in_review', _('Em Revisão')),
            ('resolved', _('Resolvido')),
            ('dismissed', _('Descartado')),
        ],
        default='pending'
    )
    notes = models.TextField(
        _('Notas'),
        blank=True
    )
    created_at = models.DateTimeField(
        _('Criado em'),
        auto_now_add=True
    )
    resolved_at = models.DateTimeField(
        _('Resolvido em'),
        null=True,
        blank=True
    )

    class Meta:
        app_label = 'mangas'
        verbose_name = _('Fila de Moderação')
        verbose_name_plural = _('Filas de Moderação')
        ordering = ['-priority', 'created_at']
        indexes = [
            models.Index(fields=['status', 'priority'], name='moderation_queue_status_priority_idx'),
            models.Index(fields=['assigned_to', 'status'], name='moderation_queue_assigned_status_idx'),
        ]

    def __str__(self):
        return f"Moderação {self.comment.id} - {self.status}"

    def assign_to_moderator(self, moderator):
        """Atribui a um moderador."""
        self.assigned_to = moderator
        self.status = 'in_review'
        self.save()

    def resolve(self, action, moderator, notes=''):
        """Resolve a entrada da fila."""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.notes = notes
        self.save()
        
        # Criar ação de moderação
        ModerationAction.objects.create(
            comment=self.comment,
            moderator=moderator,
            action_type=action,
            reason=notes,
            is_automated=False
        )

    def dismiss(self, moderator, notes=''):
        """Descartar a entrada da fila."""
        self.status = 'dismissed'
        self.resolved_at = timezone.now()
        self.notes = notes
        self.save() 