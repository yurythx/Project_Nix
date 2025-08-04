from django import template
from django.contrib.contenttypes.models import ContentType
from apps.comments.models.comment import Comment
from apps.config.services.module_service import ModuleService

register = template.Library()

@register.simple_tag
def is_comments_module_enabled():
    """Verifica se o módulo de comentários está ativo"""
    module_service = ModuleService()
    return module_service.is_module_enabled('comments')

@register.simple_tag
def is_comments_enabled_for_app(app_name):
    """Verifica se comentários estão habilitados para um app específico"""
    module_service = ModuleService()
    
    # Primeiro verifica se o módulo comments está ativo
    if not module_service.is_module_enabled('comments'):
        return False
    
    # Depois verifica se o app específico está ativo
    return module_service.is_module_enabled(app_name)

@register.simple_tag
def can_show_comments(app_name):
    """Verifica se pode mostrar comentários para um app"""
    return is_comments_enabled_for_app(app_name)

@register.simple_tag
def get_content_type(obj):
    """Retorna o ContentType para um objeto"""
    return ContentType.objects.get_for_model(obj)

@register.simple_tag
def get_comment_count(obj):
    """Retorna a contagem de comentários para um objeto"""
    module_service = ModuleService()
    if not module_service.is_module_enabled('comments'):
        return 0
        
    content_type = ContentType.objects.get_for_model(obj)
    return Comment.objects.filter(
        content_type=content_type,
        object_id=obj.id,
        status='approved'
    ).count()

@register.simple_tag
def get_user_comment_count(user):
    """Retorna a contagem de comentários de um usuário"""
    module_service = ModuleService()
    if not module_service.is_module_enabled('comments'):
        return 0
        
    return Comment.objects.filter(
        author=user,
        status='approved'
    ).count()

@register.inclusion_tag('comments/comment_list_for_object.html')
def render_comments_for_object(obj, limit=5):
    """Renderiza comentários para um objeto"""
    module_service = ModuleService()
    if not module_service.is_module_enabled('comments'):
        return {
            'comments': [],
            'object': obj,
            'content_type': None,
            'comments_disabled': True
        }
    
    content_type = ContentType.objects.get_for_model(obj)
    comments = Comment.objects.filter(
        content_type=content_type,
        object_id=obj.id,
        status='approved',
        parent__isnull=True
    ).order_by('-created_at')[:limit]
    
    return {
        'comments': comments,
        'object': obj,
        'content_type': content_type,
        'comments_disabled': False
    }
