"""
Serviço para moderação automática de comentários.
"""

import logging
import re
from typing import List, Dict, Any, Tuple, Optional
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache

from ..models.moderation import ModerationRule, ModerationAction, ModerationQueue
from ..models.comments import ChapterComment
from ..models.notifications import Notification

logger = logging.getLogger(__name__)
User = get_user_model()

class ModerationService:
    """
    Serviço para moderação automática de conteúdo.
    """
    
    def __init__(self):
        self.cache_timeout = 600  # 10 minutos
        self.confidence_threshold = 0.7  # Limiar de confiança para ações automáticas
    
    def moderate_comment(self, comment: ChapterComment) -> List[ModerationAction]:
        """
        Modera um comentário usando todas as regras ativas.
        """
        actions = []
        
        # Obter regras ativas ordenadas por prioridade
        rules = ModerationRule.objects.filter(is_active=True).order_by('-priority')
        
        for rule in rules:
            try:
                violates, confidence, details = rule.evaluate(
                    comment.content, 
                    comment.user,
                    context={'comment': comment}
                )
                
                if violates and confidence >= self.confidence_threshold:
                    action = self._create_moderation_action(rule, comment, confidence, details)
                    actions.append(action)
                    
                    # Executar ação se for automática
                    if rule.action in ['auto_delete', 'warn_user']:
                        action.execute()
                    
                    # Adicionar à fila se necessário
                    if rule.action in ['flag', 'require_approval']:
                        self._add_to_moderation_queue(comment, rule, confidence, details)
                    
                    # Parar se a ação for definitiva
                    if rule.action in ['auto_delete', 'permanent_ban']:
                        break
                        
            except Exception as e:
                logger.error(f"Erro ao avaliar regra {rule.id}: {str(e)}")
                continue
        
        return actions
    
    def moderate_batch(self, comments: List[ChapterComment]) -> Dict[str, Any]:
        """
        Modera um lote de comentários.
        """
        results = {
            'total': len(comments),
            'flagged': 0,
            'deleted': 0,
            'warned': 0,
            'actions': []
        }
        
        for comment in comments:
            actions = self.moderate_comment(comment)
            
            for action in actions:
                results['actions'].append(action)
                
                if action.action_type == 'auto_delete':
                    results['deleted'] += 1
                elif action.action_type == 'warn_user':
                    results['warned'] += 1
                elif action.action_type in ['flag', 'require_approval']:
                    results['flagged'] += 1
        
        return results
    
    def get_moderation_queue(self, status: str = 'pending', moderator: User = None, 
                           limit: int = 50) -> List[ModerationQueue]:
        """
        Obtém itens da fila de moderação.
        """
        queryset = ModerationQueue.objects.filter(status=status)
        
        if moderator:
            queryset = queryset.filter(assigned_to=moderator)
        
        return list(queryset.order_by('-priority', 'created_at')[:limit])
    
    def assign_to_moderator(self, queue_item: ModerationQueue, moderator: User) -> bool:
        """
        Atribui um item da fila a um moderador.
        """
        try:
            queue_item.assign_to_moderator(moderator)
            return True
        except Exception as e:
            logger.error(f"Erro ao atribuir item {queue_item.id} ao moderador {moderator.username}: {str(e)}")
            return False
    
    def resolve_queue_item(self, queue_item: ModerationQueue, action: str, 
                          moderator: User, notes: str = '') -> bool:
        """
        Resolve um item da fila de moderação.
        """
        try:
            queue_item.resolve(action, moderator, notes)
            
            # Executar ação de moderação
            moderation_action = ModerationAction.objects.filter(
                comment=queue_item.comment,
                moderator=moderator
            ).first()
            
            if moderation_action:
                moderation_action.execute()
            
            return True
        except Exception as e:
            logger.error(f"Erro ao resolver item {queue_item.id}: {str(e)}")
            return False
    
    def dismiss_queue_item(self, queue_item: ModerationQueue, moderator: User, 
                          notes: str = '') -> bool:
        """
        Descartar um item da fila de moderação.
        """
        try:
            queue_item.dismiss(moderator, notes)
            return True
        except Exception as e:
            logger.error(f"Erro ao descartar item {queue_item.id}: {str(e)}")
            return False
    
    def get_moderation_stats(self, moderator: User = None, days: int = 30) -> Dict[str, Any]:
        """
        Obtém estatísticas de moderação.
        """
        since = timezone.now() - timezone.timedelta(days=days)
        
        queryset = ModerationAction.objects.filter(created_at__gte=since)
        if moderator:
            queryset = queryset.filter(moderator=moderator)
        
        stats = {
            'total_actions': queryset.count(),
            'automated_actions': queryset.filter(is_automated=True).count(),
            'manual_actions': queryset.filter(is_automated=False).count(),
            'actions_by_type': {},
            'queue_stats': {},
        }
        
        # Estatísticas por tipo de ação
        for action_type, _ in ModerationRule.ACTION_CHOICES:
            count = queryset.filter(action_type=action_type).count()
            stats['actions_by_type'][action_type] = count
        
        # Estatísticas da fila
        queue_queryset = ModerationQueue.objects.filter(created_at__gte=since)
        if moderator:
            queue_queryset = queue_queryset.filter(assigned_to=moderator)
        
        stats['queue_stats'] = {
            'pending': queue_queryset.filter(status='pending').count(),
            'in_review': queue_queryset.filter(status='in_review').count(),
            'resolved': queue_queryset.filter(status='resolved').count(),
            'dismissed': queue_queryset.filter(status='dismissed').count(),
        }
        
        return stats
    
    def create_default_rules(self):
        """
        Cria regras de moderação padrão.
        """
        default_rules = [
            {
                'name': 'Filtro de Palavras Inapropriadas',
                'rule_type': 'keyword_filter',
                'description': 'Filtra comentários com palavras inapropriadas',
                'conditions': {
                    'keywords': [
                        'palavrão1', 'palavrão2', 'palavrão3',
                        'spam', 'scam', 'fraude',
                        'hack', 'crack', 'warez'
                    ]
                },
                'action': 'flag',
                'severity': 'medium',
                'priority': 100
            },
            {
                'name': 'Detecção de Spam Básico',
                'rule_type': 'spam_detection',
                'description': 'Detecta spam básico baseado em padrões',
                'conditions': {
                    'spam_patterns': [
                        'compre agora', 'clique aqui', 'ganhe dinheiro',
                        'emagreça rápido', 'aumente seu pênis'
                    ],
                    'suspicious_domains': [
                        'bit.ly', 'tinyurl.com', 'goo.gl'
                    ]
                },
                'action': 'auto_delete',
                'severity': 'high',
                'priority': 90
            },
            {
                'name': 'Limite de Comprimento',
                'rule_type': 'length_limit',
                'description': 'Limita o comprimento dos comentários',
                'conditions': {
                    'min_length': 2,
                    'max_length': 2000
                },
                'action': 'flag',
                'severity': 'low',
                'priority': 50
            },
            {
                'name': 'Limite de Frequência',
                'rule_type': 'frequency_limit',
                'description': 'Limita a frequência de comentários',
                'conditions': {
                    'max_comments_per_hour': 10,
                    'max_comments_per_day': 50
                },
                'action': 'warn_user',
                'severity': 'medium',
                'priority': 80
            },
            {
                'name': 'Reputação Baixa',
                'rule_type': 'user_reputation',
                'description': 'Aplica regras especiais para usuários com baixa reputação',
                'conditions': {
                    'min_reputation': 50
                },
                'action': 'require_approval',
                'severity': 'medium',
                'priority': 70
            }
        ]
        
        for rule_data in default_rules:
            ModerationRule.objects.get_or_create(
                name=rule_data['name'],
                defaults=rule_data
            )
        
        logger.info("Regras de moderação padrão criadas")
    
    def _create_moderation_action(self, rule: ModerationRule, comment: ChapterComment, 
                                 confidence: float, details: Dict[str, Any]) -> ModerationAction:
        """
        Cria uma ação de moderação.
        """
        reason = f"Violou regra: {rule.name}"
        if details.get('reason'):
            reason += f" - {details['reason']}"
        
        action = ModerationAction.objects.create(
            comment=comment,
            rule=rule,
            action_type=rule.action,
            reason=reason,
            confidence=confidence,
            details=details,
            is_automated=True
        )
        
        logger.info(f"Ação de moderação criada: {action.action_type} para comentário {comment.id}")
        return action
    
    def _add_to_moderation_queue(self, comment: ChapterComment, rule: ModerationRule, 
                                confidence: float, details: Dict[str, Any]):
        """
        Adiciona comentário à fila de moderação.
        """
        # Verificar se já existe na fila
        existing = ModerationQueue.objects.filter(
            comment=comment,
            status__in=['pending', 'in_review']
        ).first()
        
        if existing:
            # Adicionar regra à lista de regras que flaggaram
            existing.flagged_by_rules.add(rule)
            
            # Atualizar prioridade se necessário
            if rule.severity == 'critical' and existing.priority != 'critical':
                existing.priority = 'critical'
                existing.save()
        else:
            # Criar nova entrada na fila
            queue_item = ModerationQueue.objects.create(
                comment=comment,
                priority=rule.severity,
                status='pending'
            )
            queue_item.flagged_by_rules.add(rule)
    
    def _calculate_user_reputation(self, user: User) -> int:
        """
        Calcula reputação do usuário.
        """
        cache_key = f'user_reputation_{user.id}'
        reputation = cache.get(cache_key)
        
        if reputation is None:
            # Base: 100 pontos
            reputation = 100
            
            # Penalizar por reports
            reports_received = ChapterComment.objects.filter(
                user=user,
                reports__isnull=False
            ).count()
            reputation -= reports_received * 10
            
            # Penalizar por comentários deletados
            deleted_comments = ChapterComment.objects.filter(
                user=user,
                is_deleted=True
            ).count()
            reputation -= deleted_comments * 20
            
            # Bonificar por comentários bem recebidos
            positive_reactions = sum(
                comment.reactions.filter(
                    reaction_type__in=['like', 'love', 'laugh']
                ).count()
                for comment in ChapterComment.objects.filter(user=user, is_deleted=False)
            )
            reputation += positive_reactions * 2
            
            reputation = max(0, reputation)
            cache.set(cache_key, reputation, self.cache_timeout)
        
        return reputation
    
    def _detect_toxicity(self, content: str) -> Tuple[bool, float]:
        """
        Detecta toxicidade no conteúdo (implementação básica).
        """
        # Lista de palavras tóxicas (em produção, use APIs especializadas)
        toxic_words = [
            'idiota', 'burro', 'imbecil', 'estúpido', 'retardado',
            'racista', 'homofóbico', 'sexista', 'nazista',
            'morte', 'matar', 'suicídio', 'ódio'
        ]
        
        content_lower = content.lower()
        found_words = [word for word in toxic_words if word in content_lower]
        
        if found_words:
            toxicity_score = min(len(found_words) / len(toxic_words), 1.0)
            return True, toxicity_score
        
        return False, 0.0
    
    def _detect_spam_patterns(self, content: str) -> List[str]:
        """
        Detecta padrões de spam no conteúdo.
        """
        spam_patterns = [
            r'\b(?:compre|compra|venda|oferta|promoção|desconto)\b',
            r'\b(?:clique|clica|acesse|visite)\s+(?:aqui|agora)\b',
            r'\b(?:ganhe|ganhar|dinheiro|fácil|rápido)\b',
            r'\b(?:http|www)\.[^\s]+\b',  # URLs
            r'\b(?:[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',  # Emails
        ]
        
        found_patterns = []
        for pattern in spam_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(pattern)
        
        return found_patterns 