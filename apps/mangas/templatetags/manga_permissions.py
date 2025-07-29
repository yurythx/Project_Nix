from django import template
from django.db.models import Q

register = template.Library()

@register.filter
def has_manga_permission(user):
    """
    Verifica se o usuário tem permissão para gerenciar mangas.
    
    Permite acesso para:
    - Superusuários
    - Usuários staff
    - Usuários do grupo 'administrador'
    - Usuários do grupo 'admin'
    - Usuários do grupo 'editor'
    """
    if not user.is_authenticated:
        return False
    
    # Superuser e staff sempre têm acesso
    if user.is_superuser or user.is_staff:
        return True
    
    # Verifica grupos específicos
    allowed_groups = ['administrador', 'admin', 'editor']
    query = Q()
    for group in allowed_groups:
        query |= Q(name__iexact=group)
    return user.groups.filter(query).exists()

@register.filter
def can_edit_manga(user, manga):
    """
    Verifica se o usuário pode editar um mangá específico.
    """
    if not user.is_authenticated:
        return False
    
    # Se tem permissão geral, pode editar
    if has_manga_permission(user):
        return True
    
    # Se é o criador do mangá, pode editar
    return manga.criado_por == user 