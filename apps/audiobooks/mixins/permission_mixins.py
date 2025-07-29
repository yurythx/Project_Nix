"""
Módulo contendo mixins personalizados para controle de permissões nas views de audiolivros.
"""
from apps.common.mixins import (
    BaseOwnerOrStaffMixin,
    StaffOrSuperuserRequiredMixin,
    ReadOnlyMixin,
    CreatorRequiredMixin
)
from typing import Optional, Any


class AudiobookOwnerOrStaffMixin(BaseOwnerOrStaffMixin):
    """
    Mixin que verifica se o usuário é o proprietário do audiolivro ou tem permissão de staff.
    """
    permission_denied_message = "🚫 Acesso negado! Você só pode editar ou excluir audiolivros que você criou."
    redirect_url = 'audiobooks:audiobook_list'
    
    def _get_owner(self, obj):
        """Obtém o criador do audiolivro."""
        return getattr(obj, 'criado_por', None)


class AudiobookCreatorRequiredMixin(CreatorRequiredMixin):
    """
    Mixin que requer que o usuário seja o criador do audiolivro.
    Mais restritivo que AudiobookOwnerOrStaffMixin.
    """
    permission_denied_message = "🚫 Acesso negado! Apenas o criador do audiolivro pode realizar esta ação."
    redirect_url = 'audiobooks:audiobook_list'


class AudiobookReadOnlyMixin(ReadOnlyMixin):
    """
    Mixin para views de audiolivro somente leitura.
    """
    redirect_url = 'audiobooks:audiobook_list'


class AudiobookProgressOwnerOrStaffMixin(BaseOwnerOrStaffMixin):
    """
    Mixin que verifica se o usuário é o proprietário do progresso do audiolivro ou tem permissão de staff.
    """
    permission_denied_message = "🚫 Acesso negado! Você só pode editar seu próprio progresso de audiolivro."
    redirect_url = 'audiobooks:audiobook_list'
    
    def _get_owner(self, obj):
        """Obtém o usuário do progresso do audiolivro."""
        return getattr(obj, 'user', None)


class AudiobookFavoriteOwnerOrStaffMixin(BaseOwnerOrStaffMixin):
    """
    Mixin que verifica se o usuário é o proprietário do favorito ou tem permissão de staff.
    """
    permission_denied_message = "🚫 Acesso negado! Você só pode gerenciar seus próprios favoritos."
    redirect_url = 'audiobooks:audiobook_list'
    
    def _get_owner(self, obj):
        """Obtém o usuário do favorito."""
        return getattr(obj, 'user', None) 