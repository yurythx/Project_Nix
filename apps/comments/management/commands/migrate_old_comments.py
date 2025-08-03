from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import uuid


class Command(BaseCommand):
    help = 'Migra comentários do sistema antigo (articles) para o novo sistema global (comments)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa uma simulação sem fazer alterações no banco',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Número de comentários a processar por lote',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO SIMULAÇÃO - Nenhuma alteração será feita no banco')
            )
        
        # Importações locais para evitar problemas de inicialização
        try:
            from apps.articles.models import Comment as ArticleComment
            from apps.comments.models import Comment as GlobalComment, CommentModeration
            from apps.articles.models import Article
        except ImportError as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao importar modelos: {str(e)}')
            )
            return
        
        # Estatísticas
        total_comments = ArticleComment.objects.count()
        migrated_count = 0
        error_count = 0
        
        self.stdout.write(f'Iniciando migração de {total_comments} comentários...')
        
        # Cria configuração de moderação para artigos se não existir
        if not dry_run:
            self._create_moderation_config()
        
        # Processa comentários em lotes
        for offset in range(0, total_comments, batch_size):
            comments_batch = ArticleComment.objects.select_related(
                'article', 'user', 'parent'
            ).order_by('id')[offset:offset + batch_size]
            
            self.stdout.write(f'Processando lote {offset//batch_size + 1}...')
            
            for old_comment in comments_batch:
                try:
                    if not dry_run:
                        with transaction.atomic():
                            self._migrate_comment(old_comment)
                    else:
                        self._simulate_migration(old_comment)
                    
                    migrated_count += 1
                    
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'Erro ao migrar comentário {old_comment.id}: {str(e)}'
                        )
                    )
        
        # Relatório final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'RELATÓRIO DE MIGRAÇÃO')
        self.stdout.write('='*50)
        self.stdout.write(f'Total de comentários: {total_comments}')
        self.stdout.write(f'Migrados com sucesso: {migrated_count}')
        self.stdout.write(f'Erros: {error_count}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nEsta foi uma simulação. Execute sem --dry-run para aplicar as mudanças.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\nMigração concluída com sucesso!')
            )
    
    def _create_moderation_config(self):
        """Cria configuração de moderação para artigos"""
        from apps.comments.models import CommentModeration
        
        config, created = CommentModeration.objects.get_or_create(
            app_label='articles',
            model_name='article',
            defaults={
                'moderation_type': 'manual_review',
                'auto_approve_trusted_users': True,
                'require_email_verification': False,
                'max_comment_length': 2000,
                'min_comment_length': 3,
                'enable_spam_filter': True,
                'max_comments_per_hour': 10,
                'max_comments_per_day': 50,
                'notify_moderators': True,
                'notify_authors': True,
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Configuração de moderação criada para artigos')
            )
    
    def _migrate_comment(self, old_comment):
        """Migra um comentário individual"""
        from apps.articles.models import Article
        from apps.comments.models import Comment as GlobalComment
        
        # Verifica se já foi migrado
        article_content_type = ContentType.objects.get_for_model(Article)
        existing = GlobalComment.objects.filter(
            content_type=article_content_type,
            object_id=old_comment.article.id,
            author=old_comment.user,
            content=old_comment.content,
            created_at=old_comment.created_at
        ).first()
        
        if existing:
            self.stdout.write(
                self.style.WARNING(f'Comentário {old_comment.id} já foi migrado')
            )
            return existing
        
        # Determina status baseado no sistema antigo
        if old_comment.is_spam:
            status = 'spam'
        elif old_comment.is_approved:
            status = 'approved'
        else:
            status = 'pending'
        
        # Cria novo comentário
        new_comment = GlobalComment.objects.create(
            uuid=uuid.uuid4(),
            content=old_comment.content,
            author=old_comment.user,
            content_type=article_content_type,
            object_id=old_comment.article.id,
            parent=self._get_migrated_parent(old_comment.parent) if old_comment.parent else None,
            status=status,
            ip_address=old_comment.ip_address,
            user_agent=old_comment.user_agent,
            created_at=old_comment.created_at,
            updated_at=old_comment.updated_at,
            moderated_at=old_comment.approved_at if old_comment.is_approved else None,
        )
        
        return new_comment
    
    def _get_migrated_parent(self, old_parent):
        """Busca o comentário pai já migrado"""
        if not old_parent:
            return None
        
        from apps.articles.models import Article
        from apps.comments.models import Comment as GlobalComment
        
        article_content_type = ContentType.objects.get_for_model(Article)
        return GlobalComment.objects.filter(
            content_type=article_content_type,
            object_id=old_parent.article.id,
            author=old_parent.user,
            content=old_parent.content,
            created_at=old_parent.created_at
        ).first()
    
    def _simulate_migration(self, old_comment):
        """Simula a migração de um comentário"""
        status = 'spam' if old_comment.is_spam else ('approved' if old_comment.is_approved else 'pending')
        
        self.stdout.write(
            f'  Comentário {old_comment.id}: {old_comment.author_name} -> Status: {status}'
        )