"""
Módulo contendo mixins personalizados para controle de permissões nas views de livros.
"""
from apps.common.mixins import (
    BaseOwnerOrStaffMixin,
    StaffOrSuperuserRequiredMixin,
    ReadOnlyMixin,
    CreatorRequiredMixin
)
from typing import Optional, Any


class BookOwnerOrStaffMixin(BaseOwnerOrStaffMixin):
    """
    Mixin que verifica se o usuário é o proprietário do livro ou tem permissão de staff.
    """
    permission_denied_message = "🚫 Acesso negado! Você só pode editar ou excluir livros que você criou."
    redirect_url = 'books:book_list'
    
    def _get_owner(self, obj):
        """Obtém o criador do livro."""
        return getattr(obj, 'criado_por', None)


class BookCreatorRequiredMixin(CreatorRequiredMixin):
    """
    Mixin que requer que o usuário seja o criador do livro.
    Mais restritivo que BookOwnerOrStaffMixin.
    """
    permission_denied_message = "🚫 Acesso negado! Apenas o criador do livro pode realizar esta ação."
    redirect_url = 'books:book_list'


class BookReadOnlyMixin(ReadOnlyMixin):
    """
    Mixin para views de livro somente leitura.
    """
    redirect_url = 'books:book_list'


class BookProgressOwnerOrStaffMixin(BaseOwnerOrStaffMixin):
    """
    Mixin que verifica se o usuário é o proprietário do progresso do livro ou tem permissão de staff.
    """
    permission_denied_message = "🚫 Acesso negado! Você só pode editar seu próprio progresso de leitura."
    redirect_url = 'books:book_list'
    
    def _get_owner(self, obj):
        """Obtém o usuário do progresso do livro."""
        return getattr(obj, 'user', None)


class BookFavoriteOwnerOrStaffMixin(BaseOwnerOrStaffMixin):
    """
    Mixin que verifica se o usuário é o proprietário do favorito ou tem permissão de staff.
    """
    permission_denied_message = "🚫 Acesso negado! Você só pode gerenciar seus próprios favoritos."
    redirect_url = 'books:book_list'
    
    def _get_owner(self, obj):
        """Obtém o usuário do favorito."""
        return getattr(obj, 'user', None) 