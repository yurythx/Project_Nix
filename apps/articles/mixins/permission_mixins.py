"""
Módulo contendo mixins personalizados para controle de permissões nas views de artigos.
"""
from apps.common.mixins import (
    BaseOwnerOrStaffMixin,
    StaffOrSuperuserRequiredMixin,
    ReadOnlyMixin,
    CreatorRequiredMixin,
    AuthorOrStaffMixin
)
from typing import Optional, Any


class ArticleOwnerOrStaffMixin(AuthorOrStaffMixin):
    """
    Mixin que verifica se o usuário é o autor do artigo ou tem permissão de staff.
    """
    permission_denied_message = "🚫 Acesso negado! Você só pode editar ou excluir artigos que você escreveu."
    redirect_url = 'articles:article_list'
    
    def _get_owner(self, obj):
        """Obtém o autor do artigo."""
        return getattr(obj, 'author', None)


class ArticleCreatorRequiredMixin(CreatorRequiredMixin):
    """
    Mixin que requer que o usuário seja o autor do artigo.
    Mais restritivo que ArticleOwnerOrStaffMixin.
    """
    permission_denied_message = "🚫 Acesso negado! Apenas o autor do artigo pode realizar esta ação."
    redirect_url = 'articles:article_list'
    
    def _check_permissions(self, user) -> bool:
        """Verifica se o usuário é o autor do artigo."""
        # Superusuários sempre têm acesso
        if user.is_superuser:
            return True
        
        # Para outros usuários, verifica se é o autor
        try:
            obj = self.get_object()
            author = getattr(obj, 'author', None)
            has_access = author == user if author else False
            
            # Log da tentativa
            self.log_access_attempt(
                user, 
                has_access, 
                f"Article author: {author.username if author else 'None'}"
            )
            
            return has_access
            
        except Exception as e:
            self.log_access_attempt(user, False, f"Error: {str(e)}")
            return False


class ArticleReadOnlyMixin(ReadOnlyMixin):
    """
    Mixin para views de artigo somente leitura.
    """
    redirect_url = 'articles:article_list'


class CategoryOwnerOrStaffMixin(BaseOwnerOrStaffMixin):
    """
    Mixin que verifica se o usuário é o proprietário da categoria ou tem permissão de staff.
    """
    permission_denied_message = "🚫 Acesso negado! Você só pode editar ou excluir categorias que você criou."
    redirect_url = 'articles:category_list'
    
    def _get_owner(self, obj):
        """Obtém o criador da categoria."""
        return getattr(obj, 'criado_por', None)


class TagOwnerOrStaffMixin(BaseOwnerOrStaffMixin):
    """
    Mixin que verifica se o usuário é o proprietário da tag ou tem permissão de staff.
    """
    permission_denied_message = "🚫 Acesso negado! Você só pode editar ou excluir tags que você criou."
    redirect_url = 'articles:tag_list'
    
    def _get_owner(self, obj):
        """Obtém o criador da tag."""
        return getattr(obj, 'criado_por', None)


# CommentOwnerOrStaffMixin removido - migrado para apps.comments


class ArticleEditorOrAdminMixin(StaffOrSuperuserRequiredMixin):
    """
    Mixin para editores e administradores de artigos.
    
    Permite acesso para:
    - Superusuários
    - Usuários staff
    - Usuários do grupo 'administrador'
    - Usuários do grupo 'admin'
    - Usuários do grupo 'editor'
    """
    permission_denied_message = "🚫 Acesso negado! Apenas editores ou administradores podem realizar esta ação."
    redirect_url = 'articles:article_list'
    allowed_groups = ['administrador', 'admin', 'editor']