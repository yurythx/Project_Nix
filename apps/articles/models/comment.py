from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import EmailValidator
from django.utils import timezone

User = get_user_model()

class CommentManager(models.Manager):
    def get_replies(self, comment):
        return self.filter(parent=comment, is_approved=True).order_by('created_at')

    def approve(self, comment):
        comment.is_approved = True
        comment.approved_at = timezone.now()
        comment.save()
        return comment

    def mark_as_spam(self, comment):
        comment.is_spam = True
        comment.is_approved = False
        comment.save()
        return comment

class Comment(models.Model):
    """Modelo para comentários de artigos"""
    
    article = models.ForeignKey(
        'articles.Article',
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='artigo',
        help_text='Artigo comentado'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='comentário pai',
        help_text='Comentário pai para criar thread de respostas'
    )
    
    # Autor (pode ser usuário registrado ou visitante)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='comments',
        verbose_name='usuário',
        help_text='Usuário registrado (se aplicável)'
    )
    name = models.CharField(
        'nome',
        max_length=100,
        help_text='Nome do comentarista'
    )
    email = models.EmailField(
        'email',
        validators=[EmailValidator()],
        help_text='Email do comentarista'
    )
    website = models.URLField(
        'website',
        blank=True,
        null=True,
        help_text='Website do comentarista (opcional)'
    )
    
    # Conteúdo
    content = models.TextField(
        'comentário',
        help_text='Conteúdo do comentário'
    )
    
    # Moderação
    is_approved = models.BooleanField(
        'aprovado',
        default=False,
        help_text='Se o comentário foi aprovado para exibição'
    )
    is_spam = models.BooleanField(
        'spam',
        default=False,
        help_text='Se o comentário foi marcado como spam'
    )
    
    # Dados técnicos
    ip_address = models.GenericIPAddressField(
        'endereço IP',
        null=True,
        blank=True,
        help_text='IP do comentarista'
    )
    user_agent = models.TextField(
        'user agent',
        blank=True,
        help_text='Informações do navegador'
    )
    
    created_at = models.DateTimeField(
        'criado em',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        'atualizado em',
        auto_now=True
    )
    approved_at = models.DateTimeField(
        'aprovado em',
        null=True,
        blank=True,
        help_text='Data e hora da aprovação'
    )

    objects = CommentManager()

    class Meta:
        verbose_name = 'comentário'
        verbose_name_plural = 'comentários'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['article', 'is_approved', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_approved', '-created_at']),
            models.Index(fields=['parent', '-created_at']),
        ]

    def __str__(self):
        return f"Comentário de {self.name} em {self.article.title}"

    def save(self, *args, **kwargs):
        """Preenche nome e email do usuário se estiver logado"""
        if self.user and not self.name:
            self.name = self.user.get_full_name() or self.user.username
        if self.user and not self.email:
            self.email = self.user.email
        super().save(*args, **kwargs)

    def get_replies(self):
        return Comment.objects.get_replies(self)

    def approve(self):
        return Comment.objects.approve(self)

    def mark_as_spam(self):
        return Comment.objects.mark_as_spam(self)

    @property
    def is_reply(self):
        """Verifica se é uma resposta a outro comentário"""
        return self.parent is not None

    @property
    def reply_count(self):
        """Retorna número de respostas aprovadas"""
        return self.get_replies().count()

    @property
    def author_name(self):
        """Retorna nome do autor do comentário"""
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.name

    @property
    def can_be_replied(self):
        """Verifica se o comentário pode receber respostas"""
        return self.is_approved and not self.is_spam and self.article.allow_comments
