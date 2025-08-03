from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from .models import Comment, CommentLike, ModerationAction
from .services import CommentService, NotificationService, ModerationService, WebSocketService
from .repositories import (
    DjangoCommentRepository, 
    DjangoNotificationRepository, 
    DjangoModerationRepository
)

User = get_user_model()

# Inicializa serviços (em produção, usar injeção de dependência)
comment_repository = DjangoCommentRepository()
notification_repository = DjangoNotificationRepository()
moderation_repository = DjangoModerationRepository()

comment_service = CommentService(comment_repository, moderation_repository)
notification_service = NotificationService(notification_repository)
moderation_service = ModerationService(moderation_repository, comment_repository)
websocket_service = WebSocketService()

# Injeta WebSocket service no notification service
notification_service.websocket_service = websocket_service


@receiver(post_save, sender=Comment)
def handle_comment_created(sender, instance, created, **kwargs):
    """
    Manipula criação e atualização de comentários
    """
    if created:
        # Comentário criado
        _handle_new_comment(instance)
    else:
        # Comentário atualizado
        _handle_comment_updated(instance)


@receiver(post_save, sender=CommentLike)
def handle_comment_reaction(sender, instance, created, **kwargs):
    """
    Manipula reações em comentários
    """
    if created and instance.reaction == 'like':
        # Nova curtida
        try:
            notification_service.create_like_notification(
                comment=instance.comment,
                liker=instance.user
            )
            
            # Transmite atualização em tempo real
            reaction_data = {
                'action': 'added',
                'reaction': 'like',
                'likes_count': instance.comment.likes_count,
                'dislikes_count': instance.comment.dislikes_count,
            }
            
            websocket_service.broadcast_reaction_update(
                comment=instance.comment,
                reaction_data=reaction_data,
                user=instance.user
            )
            
        except Exception as e:
            print(f'Erro ao processar curtida: {e}')


@receiver(post_delete, sender=CommentLike)
def handle_comment_reaction_removed(sender, instance, **kwargs):
    """
    Manipula remoção de reações
    """
    try:
        # Atualiza contadores
        instance.comment.update_reaction_counts()
        
        # Transmite atualização em tempo real
        reaction_data = {
            'action': 'removed',
            'reaction': instance.reaction,
            'likes_count': instance.comment.likes_count,
            'dislikes_count': instance.comment.dislikes_count,
        }
        
        websocket_service.broadcast_reaction_update(
            comment=instance.comment,
            reaction_data=reaction_data,
            user=instance.user
        )
        
    except Exception as e:
        print(f'Erro ao processar remoção de reação: {e}')


@receiver(post_save, sender=ModerationAction)
def handle_moderation_action(sender, instance, created, **kwargs):
    """
    Manipula ações de moderação
    """
    if created:
        try:
            # Cria notificação de moderação
            notification_service.create_moderation_notification(
                comment=instance.comment,
                action=instance.action,
                moderator=instance.moderator,
                reason=instance.reason
            )
            
            # Transmite atualização em tempo real
            websocket_service.broadcast_moderation_update(
                comment=instance.comment,
                action=instance.action,
                moderator=instance.moderator
            )
            
            # Se foi marcado como spam, aprende padrões
            if instance.action == 'spam':
                _learn_spam_patterns(instance.comment)
            
        except Exception as e:
            print(f'Erro ao processar ação de moderação: {e}')


@receiver(pre_save, sender=Comment)
def handle_comment_pre_save(sender, instance, **kwargs):
    """
    Processa comentário antes de salvar
    """
    # Moderação automática para novos comentários
    if not instance.pk:  # Novo comentário
        try:
            # Executa moderação automática
            auto_action = moderation_service.auto_moderate(instance)
            
            if auto_action:
                print(f'Moderação automática aplicada: {auto_action}')
                
        except Exception as e:
            print(f'Erro na moderação automática: {e}')


def _handle_new_comment(comment):
    """
    Processa novo comentário
    """
    try:
        # Notificação de resposta
        if comment.parent:
            notification_service.create_reply_notification(
                comment=comment,
                parent_comment=comment.parent
            )
            
            # Atualiza contador de respostas do pai
            comment.parent.update_replies_count()
            
            # Transmite atualização da thread
            websocket_service.send_comment_thread_update(
                root_comment=comment.get_thread_root(),
                action='reply_added',
                affected_comment=comment
            )
        
        # Notificações de menção
        mentioned_users = comment_service.get_mentioned_users(comment.content)
        for mentioned_user in mentioned_users:
            notification_service.create_mention_notification(
                comment=comment,
                mentioned_user=mentioned_user
            )
        
        # Transmite novo comentário
        websocket_service.broadcast_comment_update(
            comment=comment,
            action='created',
            user=comment.author
        )
        
        # Detecta spam em tempo real
        if comment.status == 'pending':
            is_spam, spam_score, indicators = moderation_service.detect_spam(
                content=comment.content,
                author=comment.author,
                ip_address=comment.ip_address or ''
            )
            
            if is_spam:
                websocket_service.send_spam_detection_alert(
                    comment=comment,
                    spam_score=spam_score,
                    indicators=indicators
                )
        
    except Exception as e:
        print(f'Erro ao processar novo comentário: {e}')


def _handle_comment_updated(comment):
    """
    Processa atualização de comentário
    """
    try:
        # Verifica se status mudou
        if hasattr(comment, '_original_status'):
            old_status = comment._original_status
            new_status = comment.status
            
            if old_status != new_status:
                # Status mudou - transmite atualização
                websocket_service.broadcast_comment_update(
                    comment=comment,
                    action='status_changed',
                    user=None
                )
        
        # Se foi editado, transmite atualização
        if comment.is_edited:
            websocket_service.broadcast_comment_update(
                comment=comment,
                action='edited',
                user=comment.author
            )
            
            # Verifica novas menções
            mentioned_users = comment_service.get_mentioned_users(comment.content)
            for mentioned_user in mentioned_users:
                # Verifica se já foi notificado antes
                existing_notification = notification_repository.get_by_recipient(
                    mentioned_user
                ).filter(
                    comment=comment,
                    notification_type='mention'
                ).first()
                
                if not existing_notification:
                    notification_service.create_mention_notification(
                        comment=comment,
                        mentioned_user=mentioned_user
                    )
        
    except Exception as e:
        print(f'Erro ao processar atualização de comentário: {e}')


def _learn_spam_patterns(comment):
    """
    Aprende padrões de spam (implementação básica)
    """
    try:
        # Em implementação real, usaria machine learning
        # Por enquanto, apenas registra para análise futura
        
        # Extrai características do spam
        characteristics = {
            'length': len(comment.content),
            'word_count': len(comment.content.split()),
            'has_urls': 'http' in comment.content.lower(),
            'special_chars_ratio': sum(1 for c in comment.content if not c.isalnum() and not c.isspace()) / len(comment.content),
            'author_id': comment.author.id if comment.author else None,
            'ip_address': comment.ip_address,
        }
        
        # Em produção, salvaria essas características para treinar modelo
        print(f'Características de spam registradas: {characteristics}')
        
    except Exception as e:
        print(f'Erro ao aprender padrões de spam: {e}')


# Sinal personalizado para limpeza de dados antigos
from django.core.management.base import BaseCommand

def cleanup_old_data():
    """
    Limpa dados antigos (executado por comando de management)
    """
    try:
        # Remove notificações antigas
        deleted_notifications = notification_service.cleanup_old_notifications(days=90)
        
        # Remove dados de moderação antigos
        deleted_moderation = moderation_service.cleanup_old_data(days=180)
        
        print(f'Limpeza concluída: {deleted_notifications} notificações, {deleted_moderation["actions"]} ações de moderação')
        
    except Exception as e:
        print(f'Erro na limpeza de dados: {e}')


# Sinal para atualizar contadores quando comentário é deletado
@receiver(post_delete, sender=Comment)
def handle_comment_deleted(sender, instance, **kwargs):
    """
    Manipula deleção de comentários
    """
    try:
        # Atualiza contador do pai se era uma resposta
        if instance.parent:
            instance.parent.update_replies_count()
            
            # Transmite atualização da thread
            websocket_service.send_comment_thread_update(
                root_comment=instance.parent.get_thread_root(),
                action='reply_deleted',
                affected_comment=instance
            )
        
        # Transmite remoção do comentário
        websocket_service.broadcast_comment_update(
            comment=instance,
            action='deleted',
            user=None
        )
        
    except Exception as e:
        print(f'Erro ao processar deleção de comentário: {e}')


# Função para registrar status original antes de salvar
@receiver(pre_save, sender=Comment)
def store_original_status(sender, instance, **kwargs):
    """
    Armazena status original para detectar mudanças
    """
    if instance.pk:
        try:
            original = Comment.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except Comment.DoesNotExist:
            instance._original_status = None
    else:
        instance._original_status = None