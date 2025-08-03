from typing import List, Optional, Dict, Any, Tuple
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from django.db import transaction
from django.conf import settings
import re
import hashlib

from ..interfaces.services import IModerationService
from ..interfaces.repositories import IModerationRepository, ICommentRepository
from ..models import Comment, CommentModeration, ModerationAction, ModerationQueue

User = get_user_model()


class ModerationService(IModerationService):
    """
    Serviço de moderação de comentários
    
    Implementa IModerationService seguindo os princípios SOLID:
    - Single Responsibility: Apenas lógica de moderação
    - Open/Closed: Extensível via herança
    - Liskov Substitution: Pode substituir IModerationService
    - Interface Segregation: Interface específica para moderação
    - Dependency Inversion: Depende de abstrações (interfaces)
    """
    
    def __init__(self, moderation_repository: IModerationRepository, comment_repository: ICommentRepository):
        self.moderation_repository = moderation_repository
        self.comment_repository = comment_repository
    
    @transaction.atomic
    def approve_comment(self, comment: Comment, moderator: User, reason: str = '') -> ModerationAction:
        """Aprova comentário"""
        if not self.can_user_moderate(moderator):
            raise PermissionDenied('Você não tem permissão para moderar comentários')
        
        if comment.status == 'approved':
            raise ValidationError('Comentário já está aprovado')
        
        # Atualiza status do comentário
        self.comment_repository.update(comment, status='approved')
        
        # Remove da fila de moderação
        self.moderation_repository.remove_from_queue(comment)
        
        # Registra ação
        action = self.moderation_repository.create_moderation_action(
            comment=comment,
            moderator=moderator,
            action='approve',
            reason=reason
        )
        
        return action
    
    @transaction.atomic
    def reject_comment(self, comment: Comment, moderator: User, reason: str = '') -> ModerationAction:
        """Rejeita comentário"""
        if not self.can_user_moderate(moderator):
            raise PermissionDenied('Você não tem permissão para moderar comentários')
        
        if comment.status == 'rejected':
            raise ValidationError('Comentário já está rejeitado')
        
        # Atualiza status do comentário
        self.comment_repository.update(comment, status='rejected')
        
        # Remove da fila de moderação
        self.moderation_repository.remove_from_queue(comment)
        
        # Registra ação
        action = self.moderation_repository.create_moderation_action(
            comment=comment,
            moderator=moderator,
            action='reject',
            reason=reason
        )
        
        return action
    
    @transaction.atomic
    def mark_as_spam(self, comment: Comment, moderator: User, reason: str = '') -> ModerationAction:
        """Marca comentário como spam"""
        if not self.can_user_moderate(moderator):
            raise PermissionDenied('Você não tem permissão para moderar comentários')
        
        # Atualiza status do comentário
        self.comment_repository.update(comment, status='spam')
        
        # Remove da fila de moderação
        self.moderation_repository.remove_from_queue(comment)
        
        # Registra ação
        action = self.moderation_repository.create_moderation_action(
            comment=comment,
            moderator=moderator,
            action='spam',
            reason=reason
        )
        
        # Adiciona padrões de spam para detecção futura
        self._learn_spam_patterns(comment)
        
        return action
    
    @transaction.atomic
    def report_comment(self, comment: Comment, reporter: User, reason: str) -> bool:
        """Reporta comentário"""
        if not reporter.is_authenticated:
            raise PermissionDenied('Você precisa estar logado para reportar')
        
        if not reason.strip():
            raise ValidationError('Motivo do report é obrigatório')
        
        # Verifica se já reportou
        existing_report = self.moderation_repository.get_user_report(comment, reporter)
        if existing_report:
            raise ValidationError('Você já reportou este comentário')
        
        # Adiciona à fila de moderação com prioridade alta
        queue_item = self.moderation_repository.add_to_queue(
            comment,
            priority='high',
            reported_by=reporter,
            report_reason=reason
        )
        
        # Se muitos reports, marca automaticamente para revisão urgente
        report_count = self.moderation_repository.get_report_count(comment)
        if report_count >= getattr(settings, 'COMMENTS_AUTO_HIDE_THRESHOLD', 3):
            self.comment_repository.update(comment, status='pending')
            queue_item.priority = 'urgent'
            queue_item.save()
        
        return True
    
    def get_moderation_queue(self, moderator: User, status: str = 'pending', 
                           priority: Optional[str] = None) -> QuerySet:
        """Busca fila de moderação"""
        if not self.can_user_moderate(moderator):
            raise PermissionDenied('Você não tem permissão para acessar a fila de moderação')
        
        return self.moderation_repository.get_queue(
            status=status,
            priority=priority,
            assigned_to=moderator if not moderator.is_superuser else None
        )
    
    @transaction.atomic
    def assign_to_moderator(self, comment: Comment, moderator: User, assigned_by: User) -> bool:
        """Atribui comentário a moderador"""
        if not self.can_user_moderate(assigned_by):
            raise PermissionDenied('Você não tem permissão para atribuir moderação')
        
        if not self.can_user_moderate(moderator):
            raise ValidationError('Usuário não é um moderador válido')
        
        return self.moderation_repository.assign_to_moderator(comment, moderator)
    
    @transaction.atomic
    def bulk_moderate(self, comment_ids: List[int], action: str, moderator: User, reason: str = '') -> int:
        """Modera múltiplos comentários"""
        if not self.can_user_moderate(moderator):
            raise PermissionDenied('Você não tem permissão para moderar comentários')
        
        if action not in ['approve', 'reject', 'spam']:
            raise ValidationError('Ação inválida')
        
        if len(comment_ids) > 100:
            raise ValidationError('Máximo de 100 comentários por vez')
        
        comments = self.comment_repository.get_by_ids(comment_ids)
        moderated_count = 0
        
        for comment in comments:
            try:
                if action == 'approve':
                    self.approve_comment(comment, moderator, reason)
                elif action == 'reject':
                    self.reject_comment(comment, moderator, reason)
                elif action == 'spam':
                    self.mark_as_spam(comment, moderator, reason)
                
                moderated_count += 1
            except (ValidationError, PermissionDenied):
                # Continua com os próximos comentários
                continue
        
        return moderated_count
    
    def get_moderation_history(self, comment: Comment) -> QuerySet:
        """Busca histórico de moderação"""
        return self.moderation_repository.get_moderation_history(comment)
    
    def get_moderator_stats(self, moderator: User, days: int = 30) -> Dict[str, Any]:
        """Busca estatísticas do moderador"""
        if not self.can_user_moderate(moderator):
            raise PermissionDenied('Você não tem permissão para ver estatísticas')
        
        return self.moderation_repository.get_moderator_stats(moderator, days)
    
    def get_moderation_stats(self, days: int = 30) -> Dict[str, Any]:
        """Busca estatísticas gerais de moderação"""
        return self.moderation_repository.get_moderation_stats(days)
    
    def can_user_moderate(self, user: User) -> bool:
        """Verifica se usuário pode moderar"""
        return user.is_authenticated and (user.is_staff or user.has_perm('comments.moderate_comment'))
    
    def detect_spam(self, content: str, author: User, ip_address: str = '') -> Tuple[bool, float, List[str]]:
        """Detecta se conteúdo é spam"""
        spam_indicators = []
        spam_score = 0.0
        
        # Verifica padrões conhecidos de spam
        spam_patterns = self._get_spam_patterns()
        for pattern in spam_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                spam_indicators.append(f'Padrão de spam detectado: {pattern}')
                spam_score += 0.3
        
        # Verifica links suspeitos
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, content)
        if len(urls) > 2:
            spam_indicators.append('Muitos links no comentário')
            spam_score += 0.4
        
        # Verifica repetição excessiva
        words = content.lower().split()
        if len(words) > 0:
            unique_words = set(words)
            repetition_ratio = 1 - (len(unique_words) / len(words))
            if repetition_ratio > 0.7:
                spam_indicators.append('Repetição excessiva de palavras')
                spam_score += 0.3
        
        # Verifica caracteres especiais excessivos
        special_chars = sum(1 for c in content if not c.isalnum() and not c.isspace())
        if special_chars > len(content) * 0.3:
            spam_indicators.append('Muitos caracteres especiais')
            spam_score += 0.2
        
        # Verifica histórico do usuário
        if not author.is_authenticated:
            spam_score += 0.1
        else:
            user_spam_count = self.comment_repository.get_by_author(author, status='spam').count()
            if user_spam_count > 0:
                spam_indicators.append('Usuário com histórico de spam')
                spam_score += min(user_spam_count * 0.1, 0.5)
        
        # Verifica IP suspeito
        if ip_address:
            ip_spam_count = self.moderation_repository.get_ip_spam_count(ip_address)
            if ip_spam_count > 0:
                spam_indicators.append('IP com histórico de spam')
                spam_score += min(ip_spam_count * 0.1, 0.3)
        
        is_spam = spam_score >= 0.7
        return is_spam, spam_score, spam_indicators
    
    def auto_moderate(self, comment: Comment) -> Optional[str]:
        """Moderação automática baseada em regras"""
        content_type = ContentType.objects.get_for_model(comment.content_object)
        config = self.moderation_repository.get_moderation_config(
            content_type.app_label,
            content_type.model
        )
        
        if not config or not config.enable_auto_moderation:
            return None
        
        # Detecta spam
        is_spam, spam_score, indicators = self.detect_spam(
            comment.content,
            comment.author,
            comment.ip_address or ''
        )
        
        if is_spam:
            self.comment_repository.update(comment, status='spam')
            self.moderation_repository.create_moderation_action(
                comment=comment,
                moderator=None,  # Ação automática
                action='spam',
                reason=f'Detecção automática de spam (score: {spam_score:.2f})'
            )
            return 'spam'
        
        # Verifica palavras proibidas
        if config.blocked_words:
            blocked_words = [word.strip().lower() for word in config.blocked_words.split(',')]
            content_lower = comment.content.lower()
            
            for word in blocked_words:
                if word in content_lower:
                    self.comment_repository.update(comment, status='rejected')
                    self.moderation_repository.create_moderation_action(
                        comment=comment,
                        moderator=None,
                        action='reject',
                        reason=f'Palavra proibida detectada: {word}'
                    )
                    return 'rejected'
        
        # Verifica rate limiting
        if not config.check_rate_limit(comment.author):
            self.comment_repository.update(comment, status='rejected')
            self.moderation_repository.create_moderation_action(
                comment=comment,
                moderator=None,
                action='reject',
                reason='Limite de comentários excedido'
            )
            return 'rejected'
        
        return None
    
    def create_moderation_config(self, app_label: str, model_name: str, **config) -> CommentModeration:
        """Cria configuração de moderação"""
        content_type = ContentType.objects.get(app_label=app_label, model=model_name)
        
        moderation_config, created = CommentModeration.objects.get_or_create(
            content_type=content_type,
            defaults=config
        )
        
        if not created:
            for key, value in config.items():
                setattr(moderation_config, key, value)
            moderation_config.save()
        
        return moderation_config
    
    def get_pending_reports(self, moderator: User) -> QuerySet:
        """Busca comentários reportados pendentes"""
        if not self.can_user_moderate(moderator):
            raise PermissionDenied('Você não tem permissão para ver reports')
        
        return self.moderation_repository.get_reported_comments()
    
    def get_spam_suspects(self, moderator: User, threshold: float = 0.5) -> QuerySet:
        """Busca comentários suspeitos de spam"""
        if not self.can_user_moderate(moderator):
            raise PermissionDenied('Você não tem permissão para ver suspeitos de spam')
        
        return self.moderation_repository.get_spam_suspects(threshold)
    
    def cleanup_old_data(self, days: int = 90) -> Dict[str, int]:
        """Remove dados antigos de moderação"""
        return self.moderation_repository.cleanup_old_data(days)
    
    def _get_spam_patterns(self) -> List[str]:
        """Retorna padrões conhecidos de spam"""
        return [
            r'\b(viagra|cialis|casino|poker|lottery|winner)\b',
            r'\b(click here|visit now|buy now|limited time)\b',
            r'\b(free money|easy money|make money fast)\b',
            r'\b(weight loss|lose weight|diet pills)\b',
            r'\$\d+.*\b(per day|per hour|per week)\b',
            r'\b(work from home|earn from home)\b',
        ]
    
    def _learn_spam_patterns(self, comment: Comment) -> None:
        """Aprende novos padrões de spam (implementação básica)"""
        # Implementação básica - em produção, usaria ML
        content_hash = hashlib.md5(comment.content.encode()).hexdigest()
        
        # Salva hash para detecção futura de conteúdo similar
        # Em implementação real, salvaria em cache ou banco
        pass
    
    def get_moderation_workload(self, moderator: User) -> Dict[str, Any]:
        """Retorna carga de trabalho do moderador"""
        if not self.can_user_moderate(moderator):
            raise PermissionDenied('Você não tem permissão para ver carga de trabalho')
        
        return self.moderation_repository.get_moderator_workload(moderator)
    
    def escalate_to_admin(self, comment: Comment, moderator: User, reason: str) -> bool:
        """Escala comentário para administrador"""
        if not self.can_user_moderate(moderator):
            raise PermissionDenied('Você não tem permissão para escalar')
        
        # Atualiza prioridade na fila
        queue_item = self.moderation_repository.get_queue_item(comment)
        if queue_item:
            queue_item.priority = 'urgent'
            queue_item.escalated_by = moderator
            queue_item.escalation_reason = reason
            queue_item.escalated_at = timezone.now()
            queue_item.save()
            return True
        
        return False