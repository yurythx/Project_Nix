from django import template
from django.contrib.contenttypes.models import ContentType
from apps.comments.models.comment import Comment

register = template.Library()

@register.simple_tag
def get_content_type(obj):
    """Retorna o ContentType para um objeto"""
    return ContentType.objects.get_for_model(obj)

@register.simple_tag
def get_comment_count(obj):
    """Retorna a contagem de comentários para um objeto"""
    content_type = ContentType.objects.get_for_model(obj)
    return Comment.objects.filter(
        content_type=content_type,
        object_id=obj.id,
        status='approved'
    ).count()

@register.simple_tag
def get_user_comment_count(user):
    """Retorna a contagem de comentários de um usuário"""
    return Comment.objects.filter(
        author=user,
        status='approved'
    ).count()

@register.inclusion_tag('comments/comment_list_for_object.html')
def render_comments_for_object(obj, limit=5):
    """Renderiza comentários para um objeto"""
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
        'content_type': content_type
    }
