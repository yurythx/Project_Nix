"""
Módulo contendo mixins personalizados para controle de permissões nas views de mangás.
"""
from apps.common.mixins import (
    BaseOwnerOrStaffMixin,
    StaffOrSuperuserRequiredMixin,
    ReadOnlyMixin,
    CreatorRequiredMixin
)
from abc import ABC, abstractmethod
from typing import Optional, Any


class BasePermissionMixin(ABC):
    """Mixin base abstrato para permissões."""
    
    @abstractmethod
    def has_permission(self, request, obj=None) -> bool:
        pass
    
    @abstractmethod
    def get_permission_denied_message(self) -> str:
        pass

class MangaOwnerOrStaffMixin(BasePermissionMixin, BaseOwnerOrStaffMixin):
    """Mixin extensível para verificação de proprietário do mangá."""
    
    def has_permission(self, request, obj=None) -> bool:
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        if obj and hasattr(obj, 'criado_por'):
            return obj.criado_por == request.user
        
        return False
    
    def get_permission_denied_message(self) -> str:
        return "🚫 Acesso negado! Você só pode editar ou excluir mangás que você criou."
    
    def _get_owner(self, obj):
        return getattr(obj, 'criado_por', None)


class ChapterOwnerOrStaffMixin(BaseOwnerOrStaffMixin):
    """
    Mixin que verifica se o usuário é o proprietário do capítulo ou tem permissão de staff.
    """
    permission_denied_message = "🚫 Acesso negado! Você só pode editar ou excluir capítulos de mangás que você criou."
    redirect_url = 'mangas:manga_list'
    
    def _get_owner(self, obj):
        """
        Obtém o criador do mangá relacionado ao capítulo.
        Considera a estrutura hierárquica: Manga → Volume → Capitulo
        """
        try:
            # Tenta acessar através da propriedade manga (para compatibilidade)
            if hasattr(obj, 'manga'):
                return getattr(obj.manga, 'criado_por', None)
            
            # Acessa através da estrutura hierárquica
            if hasattr(obj, 'volume') and obj.volume:
                return getattr(obj.volume.manga, 'criado_por', None)
                
            return None
        except Exception:
            return None


class PageOwnerOrStaffMixin(BaseOwnerOrStaffMixin):
    """
    Mixin que verifica se o usuário é o proprietário da página ou tem permissão de staff.
    """
    permission_denied_message = "🚫 Acesso negado! Você só pode editar ou excluir páginas de capítulos que você criou."
    redirect_url = 'mangas:manga_list'
    
    def _get_owner(self, obj):
        """
        Obtém o criador do mangá relacionado à página.
        Considera a estrutura hierárquica: Manga → Volume → Capitulo → Pagina
        """
        try:
            if hasattr(obj, 'capitulo') and obj.capitulo:
                # Usa o mixin de capítulo para reutilizar a lógica
                chapter_mixin = ChapterOwnerOrStaffMixin()
                chapter_mixin.request = self.request
                return chapter_mixin._get_owner(obj.capitulo)
            return None
        except Exception:
            return None


class VolumeOwnerOrStaffMixin(BaseOwnerOrStaffMixin):
    """
    Mixin que verifica se o usuário é o proprietário do volume ou tem permissão de staff.
    """
    permission_denied_message = "🚫 Acesso negado! Você só pode editar ou excluir volumes de mangás que você criou."
    redirect_url = 'mangas:manga_list'
    
    def _get_owner(self, obj):
        """Obtém o criador do mangá relacionado ao volume."""
        try:
            if hasattr(obj, 'manga'):
                return getattr(obj.manga, 'criado_por', None)
            return None
        except Exception:
            return None


# Mixins específicos para mangás
class MangaCreatorRequiredMixin(CreatorRequiredMixin):
    """
    Mixin que requer que o usuário seja o criador do mangá.
    Mais restritivo que MangaOwnerOrStaffMixin.
    """
    permission_denied_message = "🚫 Acesso negado! Apenas o criador do mangá pode realizar esta ação."
    redirect_url = 'mangas:manga_list'


class MangaReadOnlyMixin(ReadOnlyMixin):
    """
    Mixin para views de mangá somente leitura.
    """
    redirect_url = 'mangas:manga_list'
