from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator, MaxLengthValidator
from .capitulo import Capitulo

User = get_user_model()

class ChapterComment(models.Model):
    """
    Modelo para comentários em capítulos de mangá.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chapter_comments',
        verbose_name=_('Usuário')
    )
    capitulo = models.ForeignKey(
        Capitulo,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('Capítulo')
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_('Comentário Pai')
    )
    content = models.TextField(
        _('Conteúdo'),
        validators=[
            MinLengthValidator(2, _('O comentário deve ter pelo menos 2 caracteres.')),
            MaxLengthValidator(2000, _('O comentário não pode ter mais de 2000 caracteres.'))
        ],
        help_text=_('Conteúdo do comentário')
    )
    page_number = models.PositiveIntegerField(
        _('Número da Página'),
        null=True,
        blank=True,
        help_text=_('Página específica do capítulo (opcional)')
    )
    is_edited = models.BooleanField(
        _('Editado'),
        default=False,
        help_text=_('Se o comentário foi editado')
    )
    edited_at = models.DateTimeField(
        _('Editado em'),
        null=True,
        blank=True
    )
    is_deleted = models.BooleanField(
        _('Deletado'),
        default=False,
        help_text=_('Se o comentário foi deletado')
    )
    deleted_at = models.DateTimeField(
        _('Deletado em'),
        null=True,
        blank=True
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
        verbose_name = _('Comentário de Capítulo')
        verbose_name_plural = _('Comentários de Capítulo')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['capitulo', 'created_at'], name='comment_chapter_date_idx'),
            models.Index(fields=['user', 'created_at'], name='comment_user_date_idx'),
            models.Index(fields=['parent'], name='comment_parent_idx'),
            models.Index(fields=['page_number'], name='comment_page_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.capitulo.manga.title} Cap. {self.capitulo.number}"

    @property
    def is_reply(self):
        """Verifica se é uma resposta a outro comentário."""
        return self.parent is not None

    @property
    def reply_count(self):
        """Retorna o número de respostas."""
        return self.replies.filter(is_deleted=False).count()

    def mark_as_edited(self):
        """Marca o comentário como editado."""
        from django.utils import timezone
        self.is_edited = True
        self.edited_at = timezone.now()
        self.save(update_fields=['is_edited', 'edited_at'])

    def soft_delete(self):
        """Deleta o comentário de forma suave."""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

class CommentReaction(models.Model):
    """
    Modelo para reações em comentários (like, dislike, etc.).
    """
    REACTION_TYPES = [
        ('like', _('👍 Gostei')),
        ('dislike', _('👎 Não Gostei')),
        ('love', _('❤️ Amor')),
        ('laugh', _('😂 Riso')),
        ('wow', _('😮 Surpreso')),
        ('sad', _('😢 Triste')),
        ('angry', _('😠 Bravo')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comment_reactions',
        verbose_name=_('Usuário')
    )
    comment = models.ForeignKey(
        ChapterComment,
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name=_('Comentário')
    )
    reaction_type = models.CharField(
        _('Tipo de Reação'),
        max_length=10,
        choices=REACTION_TYPES,
        default='like'
    )
    created_at = models.DateTimeField(
        _('Criado em'),
        auto_now_add=True
    )

    class Meta:
        app_label = 'mangas'
        verbose_name = _('Reação de Comentário')
        verbose_name_plural = _('Reações de Comentário')
        unique_together = ('user', 'comment')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['comment', 'reaction_type'], name='reaction_comment_type_idx'),
            models.Index(fields=['user', 'created_at'], name='reaction_user_date_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_reaction_type_display()}"

class CommentReport(models.Model):
    """
    Modelo para denúncias de comentários.
    """
    REPORT_REASONS = [
        ('spam', _('Spam')),
        ('inappropriate', _('Conteúdo Inapropriado')),
        ('harassment', _('Assédio')),
        ('spoiler', _('Spoiler sem Aviso')),
        ('other', _('Outro')),
    ]

    STATUS_CHOICES = [
        ('pending', _('Pendente')),
        ('reviewed', _('Revisado')),
        ('resolved', _('Resolvido')),
        ('dismissed', _('Descartado')),
    ]

    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comment_reports',
        verbose_name=_('Denunciante')
    )
    comment = models.ForeignKey(
        ChapterComment,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_('Comentário Denunciado')
    )
    reason = models.CharField(
        _('Motivo'),
        max_length=20,
        choices=REPORT_REASONS
    )
    description = models.TextField(
        _('Descrição'),
        blank=True,
        help_text=_('Descrição detalhada da denúncia')
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_reports',
        verbose_name=_('Revisado por')
    )
    reviewed_at = models.DateTimeField(
        _('Revisado em'),
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        _('Criado em'),
        auto_now_add=True
    )

    class Meta:
        app_label = 'mangas'
        verbose_name = _('Denúncia de Comentário')
        verbose_name_plural = _('Denúncias de Comentário')
        unique_together = ('reporter', 'comment')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at'], name='report_status_date_idx'),
            models.Index(fields=['comment', 'status'], name='report_comment_status_idx'),
        ]

    def __str__(self):
        return f"Denúncia de {self.reporter.username} - {self.get_reason_display()}"

    def mark_as_reviewed(self, reviewer):
        """Marca a denúncia como revisada."""
        from django.utils import timezone
        self.status = 'reviewed'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at']) 