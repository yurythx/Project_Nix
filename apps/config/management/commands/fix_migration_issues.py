from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Corrige problemas de migração em produção'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Apenas verifica problemas sem corrigir',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força correção mesmo se houver riscos',
        )
        parser.add_argument(
            '--specific-migration',
            type=str,
            help='Corrige migração específica (ex: articles.0003_article_image_caption)',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 CORREÇÃO DE PROBLEMAS DE MIGRAÇÃO')
        )
        self.stdout.write('=' * 50)
        
        check_only = options.get('check_only', False)
        force = options.get('force', False)
        specific_migration = options.get('specific_migration')
        
        if check_only:
            self.stdout.write('🔍 Modo de verificação apenas')
            self.check_migration_issues()
            return
        
        if specific_migration:
            self.fix_specific_migration(specific_migration, force)
        else:
            self.fix_all_migration_issues(force)
    
    def check_migration_issues(self):
        """Verifica problemas de migração"""
        self.stdout.write('\n📋 Verificando problemas de migração...')
        
        issues_found = []
        
        # Verificar migrações pendentes
        try:
            from django.core.management import call_command
            from io import StringIO
            
            output = StringIO()
            call_command('showmigrations', '--list', stdout=output)
            migrations_output = output.getvalue()
            
            pending_migrations = []
            for line in migrations_output.split('\n'):
                if '[ ]' in line:
                    pending_migrations.append(line.strip())
            
            if pending_migrations:
                issues_found.append(f"Migrações pendentes: {len(pending_migrations)}")
                for migration in pending_migrations:
                    self.stdout.write(f"   ⚠️  {migration}")
            else:
                self.stdout.write(self.style.SUCCESS('   ✅ Nenhuma migração pendente'))
                
        except Exception as e:
            issues_found.append(f"Erro ao verificar migrações: {e}")
        
        # Verificar problemas específicos conhecidos
        specific_issues = self.check_specific_issues()
        issues_found.extend(specific_issues)
        
        # Resumo
        if issues_found:
            self.stdout.write('\n❌ Problemas encontrados:')
            for issue in issues_found:
                self.stdout.write(f"   - {issue}")
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Nenhum problema encontrado'))
    
    def check_specific_issues(self):
        """Verifica problemas específicos conhecidos"""
        issues = []
        
        # Verificar coluna image_caption
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'articles_article' 
                    AND column_name = 'image_caption'
                """)
                result = cursor.fetchone()
                
            if not result:
                issues.append("Coluna 'image_caption' não existe na tabela articles_article")
            else:
                self.stdout.write('   ✅ Coluna image_caption existe')
                
        except Exception as e:
            issues.append(f"Erro ao verificar coluna image_caption: {e}")
        
        # Verificar outras colunas problemáticas conhecidas
        problematic_columns = [
            ('articles_article', 'featured_image_alt'),
            ('articles_article', 'reading_time'),
        ]
        
        for table, column in problematic_columns:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = '{table}' 
                        AND column_name = '{column}'
                    """)
                    result = cursor.fetchone()
                    
                if not result:
                    issues.append(f"Coluna '{column}' não existe na tabela {table}")
                    
            except Exception as e:
                issues.append(f"Erro ao verificar coluna {column}: {e}")
        
        return issues
    
    def fix_specific_migration(self, migration_name, force=False):
        """Corrige migração específica"""
        self.stdout.write(f'\n🔧 Corrigindo migração: {migration_name}')
        
        try:
            app_label, migration_number = migration_name.split('.')
            
            # Verificar se a migração existe
            from django.db.migrations.loader import MigrationLoader
            loader = MigrationLoader(connection)
            
            if (app_label, migration_number) not in loader.disk_migrations:
                self.stdout.write(
                    self.style.ERROR(f'Migração {migration_name} não encontrada')
                )
                return
            
            # Aplicar migração específica
            call_command('migrate', app_label, migration_number, verbosity=0)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Migração {migration_name} aplicada com sucesso')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao aplicar migração {migration_name}: {e}')
            )
            
            if force:
                self.stdout.write('🔄 Tentando correção manual...')
                self.fix_migration_manually(migration_name)
    
    def fix_migration_manually(self, migration_name):
        """Corrige migração manualmente"""
        app_label, migration_number = migration_name.split('.')
        
        # Correções específicas conhecidas
        if migration_name == 'articles.0003_article_image_caption':
            self.fix_image_caption_column()
        else:
            self.stdout.write(
                self.style.WARNING(f'Correção manual não implementada para {migration_name}')
            )
    
    def fix_image_caption_column(self):
        """Corrige especificamente a coluna image_caption"""
        self.stdout.write('🔧 Corrigindo coluna image_caption...')
        
        try:
            # Criar coluna se não existir
            with connection.cursor() as cursor:
                cursor.execute("""
                    ALTER TABLE articles_article 
                    ADD COLUMN image_caption VARCHAR(255) DEFAULT '' 
                    NOT NULL
                """)
            
            # Marcar migração como aplicada
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied) 
                    VALUES ('articles', '0003_article_image_caption', NOW())
                    ON CONFLICT (app, name) DO NOTHING
                """)
            
            self.stdout.write(
                self.style.SUCCESS('✅ Coluna image_caption corrigida manualmente')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro na correção manual: {e}')
            )
    
    def fix_all_migration_issues(self, force=False):
        """Corrige todos os problemas de migração"""
        self.stdout.write('\n🔧 Corrigindo todos os problemas de migração...')
        
        # Verificar problemas primeiro
        issues = self.check_specific_issues()
        
        if not issues:
            self.stdout.write(self.style.SUCCESS('✅ Nenhum problema encontrado'))
            return
        
        if not force:
            self.stdout.write('\n⚠️  Problemas encontrados:')
            for issue in issues:
                self.stdout.write(f"   - {issue}")
            
            response = input('\nDeseja corrigir automaticamente? (y/N): ')
            if response.lower() != 'y':
                self.stdout.write('❌ Correção cancelada')
                return
        
        # Aplicar correções
        self.stdout.write('\n🚀 Aplicando correções...')
        
        # Backup do banco
        self.create_backup()
        
        # Aplicar migrações pendentes
        try:
            call_command('migrate', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✅ Migrações aplicadas'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao aplicar migrações: {e}')
            )
            
            if force:
                self.stdout.write('🔄 Tentando correções manuais...')
                self.apply_manual_fixes()
        
        # Verificar se os problemas foram resolvidos
        self.stdout.write('\n🔍 Verificando correções...')
        remaining_issues = self.check_specific_issues()
        
        if remaining_issues:
            self.stdout.write(self.style.WARNING('⚠️  Alguns problemas persistem:'))
            for issue in remaining_issues:
                self.stdout.write(f"   - {issue}")
        else:
            self.stdout.write(self.style.SUCCESS('✅ Todos os problemas foram resolvidos'))
    
    def apply_manual_fixes(self):
        """Aplica correções manuais para problemas conhecidos"""
        self.stdout.write('🔧 Aplicando correções manuais...')
        
        # Correção para image_caption
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'articles_article' 
                    AND column_name = 'image_caption'
                """)
                result = cursor.fetchone()
                
            if not result:
                self.fix_image_caption_column()
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro na correção manual: {e}')
            )
    
    def create_backup(self):
        """Cria backup do banco de dados"""
        try:
            from django.conf import settings
            import shutil
            from datetime import datetime
            
            db_path = settings.DATABASES['default']['NAME']
            backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            shutil.copy2(db_path, backup_path)
            self.stdout.write(f'💾 Backup criado: {backup_path}')
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Não foi possível criar backup: {e}')
            ) 