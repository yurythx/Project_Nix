from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .manga import Manga

User = get_user_model()

class UserList(models.Model):
    """
    Modelo para listas personalizadas de mangá dos usuários.
    """
    LIST_TYPES = [
        ('reading', _('Lendo')),
        ('completed', _('Concluído')),
        ('plan_to_read', _('Planejo Ler')),
        ('on_hold', _('Em Pausa')),
        ('dropped', _('Abandonado')),
        ('favorites', _('Favoritos')),
        ('custom', _('Personalizada')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='manga_lists',
        verbose_name=_('Usuário')
    )
    name = models.CharField(
        _('Nome da Lista'),
        max_length=100,
        help_text=_('Nome da lista personalizada')
    )
    list_type = models.CharField(
        _('Tipo de Lista'),
        max_length=20,
        choices=LIST_TYPES,
        default='custom'
    )
    description = models.TextField(
        _('Descrição'),
        blank=True,
        help_text=_('Descrição opcional da lista')
    )
    is_public = models.BooleanField(
        _('Lista Pública'),
        default=False,
        help_text=_('Se a lista é visível para outros usuários')
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
        verbose_name = _('Lista de Usuário')
        verbose_name_plural = _('Listas de Usuário')
        unique_together = ('user', 'name')
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'list_type'], name='user_list_user_type_idx'),
            models.Index(fields=['is_public', 'updated_at'], name='user_list_public_date_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.name}"

    @property
    def manga_count(self):
        """Retorna o número de mangás na lista."""
        return self.manga_entries.count()

class UserListEntry(models.Model):
    """
    Entrada individual de mangá em uma lista de usuário.
    """
    user_list = models.ForeignKey(
        UserList,
        on_delete=models.CASCADE,
        related_name='manga_entries',
        verbose_name=_('Lista')
    )
    manga = models.ForeignKey(
        Manga,
        on_delete=models.CASCADE,
        related_name='list_entries',
        verbose_name=_('Mangá')
    )
    added_at = models.DateTimeField(
        _('Adicionado em'),
        auto_now_add=True
    )
    notes = models.TextField(
        _('Notas'),
        blank=True,
        help_text=_('Notas pessoais sobre este mangá')
    )
    rating = models.PositiveSmallIntegerField(
        _('Avaliação'),
        null=True,
        blank=True,
        choices=[(i, str(i)) for i in range(1, 11)],
        help_text=_('Avaliação de 1 a 10')
    )

    class Meta:
        app_label = 'mangas'
        verbose_name = _('Entrada da Lista')
        verbose_name_plural = _('Entradas da Lista')
        unique_together = ('user_list', 'manga')
        ordering = ['-added_at']
        indexes = [
            models.Index(fields=['user_list', 'added_at'], name='list_entry_list_date_idx'),
        ]

    def __str__(self):
        return f"{self.user_list.name} - {self.manga.title}"

class Favorite(models.Model):
    """
    Modelo para favoritos dos usuários.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='manga_favorites',
        verbose_name=_('Usuário')
    )
    manga = models.ForeignKey(
        Manga,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name=_('Mangá')
    )
    added_at = models.DateTimeField(
        _('Adicionado em'),
        auto_now_add=True
    )
    notes = models.TextField(
        _('Notas'),
        blank=True,
        help_text=_('Por que você gosta deste mangá?')
    )

    class Meta:
        app_label = 'mangas'
        verbose_name = _('Favorito')
        verbose_name_plural = _('Favoritos')
        unique_together = ('user', 'manga')
        ordering = ['-added_at']
        indexes = [
            models.Index(fields=['user', 'added_at'], name='favorite_user_date_idx'),
            models.Index(fields=['manga'], name='favorite_manga_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} ♥ {self.manga.title}" 