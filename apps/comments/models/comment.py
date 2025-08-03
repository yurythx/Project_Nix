from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.validators import MinLengthValidator
from django.utils import timezone
from django.urls import reverse
import uuid

User = get_user_model()


class Comment(models.Model):
    """
    Modelo para comentários genéricos que podem ser anexados a qualquer modelo
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas gerencia comentários
    - Open/Closed: Extensível via herança
    - Liskov Substitution: Pode ser usado em qualquer contexto
    - Interface Segregation: Interface específica para comentários
    - Dependency Inversion: Usa GenericForeignKey para flexibilidade
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('approved', 'Aprovado'),
        ('rejected', 'Rejeitado'),
        ('spam', 'Spam'),
        ('deleted', 'Deletado'),
    ]
    
    # Identificador único
    uuid = models.UUIDField(
        'UUID',
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text='Identificador único do comentário'
    )
    
    # Conteúdo do comentário
    content = models.TextField(
        'conteúdo',
        validators=[MinLengthValidator(3)],
        help_text='Conteúdo do comentário'
    )
    
    # Autor do comentário
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_comments',
        verbose_name='autor',
        help_text='Usuário que fez o comentário'
    )
    
    # Objeto ao qual o comentário está anexado (Generic Foreign Key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name='tipo de conteúdo'
    )
    object_id = models.PositiveIntegerField(
        'ID do objeto'
    )
    content_object = GenericForeignKey(
        'content_type',
        'object_id'
    )
    
    # Comentário pai para aninhamento
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='comentário pai',
        help_text='Comentário ao qual este é uma resposta'
    )
    
    # Status de moderação
    status = models.CharField(
        'status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Status de moderação do comentário'
    )
    
    # Metadados
    ip_address = models.GenericIPAddressField(
        'endereço IP',
        null=True,
        blank=True,
        help_text='Endereço IP do autor'
    )
    
    user_agent = models.TextField(
        'user agent',
        blank=True,
        help_text='User agent do navegador'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        'criado em',
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        'atualizado em',
        auto_now=True
    )
    
    # Moderação
    moderated_at = models.DateTimeField(
        'moderado em',
        null=True,
        blank=True,
        help_text='Data e hora da moderação'
    )
    
    moderated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_comments',
        verbose_name='moderado por',
        help_text='Usuário que moderou o comentário'
    )
    
    # Flags
    is_edited = models.BooleanField(
        'editado',
        default=False,
        help_text='Se o comentário foi editado'
    )
    
    is_pinned = models.BooleanField(
        'fixado',
        default=False,
        help_text='Se o comentário está fixado no topo'
    )
    
    # Contadores
    likes_count = models.PositiveIntegerField(
        'curtidas',
        default=0,
        help_text='Número de curtidas'
    )
    
    dislikes_count = models.PositiveIntegerField(
        'descurtidas',
        default=0,
        help_text='Número de descurtidas'
    )
    
    replies_count = models.PositiveIntegerField(
        'respostas',
        default=0,
        help_text='Número de respostas'
    )
    
    class Meta:
        app_label = 'comments'
        verbose_name = 'comentário'
        verbose_name_plural = 'comentários'
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['parent']),
        ]
        
    def __str__(self):
        return f'Comentário de {self.author.username} em {self.content_object}'
    
    def save(self, *args, **kwargs):
        """Override save para atualizar contadores"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Atualiza contador de respostas do comentário pai
        if is_new and self.parent:
            self.parent.update_replies_count()
    
    def get_absolute_url(self):
        """Retorna URL absoluta do comentário"""
        return f"{self.content_object.get_absolute_url()}#comment-{self.uuid}"
    
    def get_depth(self):
        """Retorna a profundidade do comentário na árvore"""
        depth = 0
        parent = self.parent
        while parent:
            depth += 1
            parent = parent.parent
        return depth
    
    def get_thread_root(self):
        """Retorna o comentário raiz da thread"""
        if not self.parent:
            return self
        return self.parent.get_thread_root()
    
    def get_replies(self):
        """Retorna respostas aprovadas ordenadas"""
        return self.replies.filter(
            status='approved'
        ).order_by('-is_pinned', 'created_at')
    
    def update_replies_count(self):
        """Atualiza contador de respostas"""
        self.replies_count = self.replies.filter(status='approved').count()
        self.save(update_fields=['replies_count'])
    
    def can_be_edited_by(self, user):
        """Verifica se o usuário pode editar o comentário"""
        if not user.is_authenticated:
            return False
        
        # Autor pode editar dentro de 15 minutos
        if user == self.author:
            time_limit = timezone.now() - timezone.timedelta(minutes=15)
            return self.created_at > time_limit and not self.is_edited
        
        # Staff sempre pode editar
        return user.is_staff
    
    def can_be_deleted_by(self, user):
        """Verifica se o usuário pode deletar o comentário"""
        if not user.is_authenticated:
            return False
        
        # Autor pode deletar
        if user == self.author:
            return True
        
        # Staff sempre pode deletar
        return user.is_staff
    
    def moderate(self, status, moderator, reason=''):
        """Modera o comentário"""
        self.status = status
        self.moderated_by = moderator
        self.moderated_at = timezone.now()
        self.save(update_fields=['status', 'moderated_by', 'moderated_at'])
        
        # Cria registro de moderação
        from .moderation import ModerationAction
        ModerationAction.objects.create(
            comment=self,
            moderator=moderator,
            action=status,
            reason=reason
        )
    
    @property
    def is_approved(self):
        """Verifica se o comentário está aprovado"""
        return self.status == 'approved'
    
    @property
    def is_pending(self):
        """Verifica se o comentário está pendente"""
        return self.status == 'pending'
    
    @property
    def is_rejected(self):
        """Verifica se o comentário foi rejeitado"""
        return self.status in ['rejected', 'spam', 'deleted']
    
    @property
    def can_have_replies(self):
        """Verifica se o comentário pode ter respostas"""
        # Limita profundidade máxima
        return self.get_depth() < 3 and self.is_approved


class CommentLike(models.Model):
    """Modelo para curtidas em comentários"""
    
    REACTION_CHOICES = [
        ('like', 'Curtir'),
        ('dislike', 'Descurtir'),
    ]
    
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name='comentário'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comment_reactions',
        verbose_name='usuário'
    )
    
    reaction = models.CharField(
        'reação',
        max_length=10,
        choices=REACTION_CHOICES,
        help_text='Tipo de reação'
    )
    
    created_at = models.DateTimeField(
        'criado em',
        auto_now_add=True
    )
    
    class Meta:
        app_label = 'comments'
        verbose_name = 'reação ao comentário'
        verbose_name_plural = 'reações aos comentários'
        unique_together = ['comment', 'user']
        indexes = [
            models.Index(fields=['comment', 'reaction']),
        ]
    
    def __str__(self):
        return f'{self.user.username} {self.reaction} comentário {self.comment.uuid}'
    
    def save(self, *args, **kwargs):
        """Override save para atualizar contadores"""
        # Remove reação anterior se existir
        if self.pk:
            old_reaction = CommentLike.objects.get(pk=self.pk).reaction
            if old_reaction != self.reaction:
                self.comment.update_reaction_counts()
        
        super().save(*args, **kwargs)
        self.comment.update_reaction_counts()
    
    def delete(self, *args, **kwargs):
        """Override delete para atualizar contadores"""
        comment = self.comment
        super().delete(*args, **kwargs)
        comment.update_reaction_counts()


# Adiciona método para atualizar contadores de reações
def update_reaction_counts(self):
    """Atualiza contadores de curtidas e descurtidas"""
    likes = self.reactions.filter(reaction='like').count()
    dislikes = self.reactions.filter(reaction='dislike').count()
    
    Comment.objects.filter(pk=self.pk).update(
        likes_count=likes,
        dislikes_count=dislikes
    )

# Adiciona o método à classe Comment
Comment.update_reaction_counts = update_reaction_counts