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


class VideoAudioOwnerOrStaffMixin(BaseOwnerOrStaffMixin):
    """
    Mixin que verifica se o usuário é o proprietário do vídeo ou tem permissão de staff.
    """
    permission_denied_message = "🚫 Acesso negado! Você só pode editar ou excluir vídeos que você criou."
    redirect_url = 'audiobooks:video_list'
    
    def _get_owner(self, obj):
        """Obtém o criador do vídeo."""
        return getattr(obj, 'created_by', None)


class VideoAudioCreatorRequiredMixin(CreatorRequiredMixin):
    """
    Mixin que requer que o usuário seja o criador do vídeo.
    Mais restritivo que VideoAudioOwnerOrStaffMixin.
    """
    permission_denied_message = "🚫 Acesso negado! Apenas o criador do vídeo pode realizar esta ação."
    redirect_url = 'audiobooks:video_list'


class VideoAudioReadOnlyMixin(ReadOnlyMixin):
    """
    Mixin para views de vídeo somente leitura.
    """
    redirect_url = 'audiobooks:video_list'


class VideoProgressOwnerOrStaffMixin(BaseOwnerOrStaffMixin):
    """
    Mixin que verifica se o usuário é o proprietário do progresso do vídeo ou tem permissão de staff.
    """
    permission_denied_message = "🚫 Acesso negado! Você só pode editar seu próprio progresso de vídeo."
    redirect_url = 'audiobooks:video_list'
    
    def _get_owner(self, obj):
        """Obtém o usuário do progresso do vídeo."""
        return getattr(obj, 'user', None)


class VideoFavoriteOwnerOrStaffMixin(BaseOwnerOrStaffMixin):
    """
    Mixin que verifica se o usuário é o proprietário do favorito ou tem permissão de staff.
    """
    permission_denied_message = "🚫 Acesso negado! Você só pode gerenciar seus próprios favoritos."
    redirect_url = 'audiobooks:video_list'
    
    def _get_owner(self, obj):
        """Obtém o usuário do favorito."""
        return getattr(obj, 'user', None)