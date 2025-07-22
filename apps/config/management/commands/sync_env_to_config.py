from django.core.management.base import BaseCommand
from django.conf import settings
from apps.config.models import EmailConfiguration, DatabaseConfiguration
import os


class Command(BaseCommand):
    help = 'Sincroniza configurações do arquivo .env com o app config'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a criação mesmo se já existirem configurações',
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Atualiza configurações existentes em vez de criar novas',
        )
    
    def handle(self, *args, **options):
        self.stdout.write('🔄 Sincronizando configurações do .env com o app config...')
        
        force = options.get('force', False)
        update = options.get('update', False)
        
        # Verificar se já existem configurações
        email_exists = EmailConfiguration.objects.exists()
        db_exists = DatabaseConfiguration.objects.exists()
        
        if (email_exists or db_exists) and not force and not update:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  Já existem configurações no banco. Use --force para recriar ou --update para atualizar.'
                )
            )
            return
        
        # Sincronizar email
        email_success = self.sync_email_config(force, update)
        
        # Sincronizar banco de dados
        db_success = self.sync_database_config(force, update)
        
        # Mostrar resultado
        if email_success and db_success:
            self.stdout.write(
                self.style.SUCCESS('\n🎉 Sincronização concluída com sucesso!')
            )
            self.stdout.write('\n📝 Próximos passos:')
            self.stdout.write('1. Acesse /config/email/ para gerenciar configurações de email')
            self.stdout.write('2. Acesse /config/database/ para gerenciar configurações de banco')
            self.stdout.write('3. Use os comandos de sincronização quando necessário')
        else:
            self.stdout.write(
                self.style.ERROR('\n❌ Sincronização falhou parcialmente')
            )
    
    def sync_email_config(self, force=False, update=False):
        """Sincroniza configurações de email"""
        self.stdout.write('\n📧 Sincronizando configurações de EMAIL...')
        
        try:
            # Verificar se já existe
            existing = EmailConfiguration.objects.filter(name="Configuração do .env").first()
            
            if existing and update:
                self.stdout.write('⚠️  Atualizando configuração existente...')
                config = existing
            elif existing and not force:
                self.stdout.write('ℹ️  Configuração já existe. Use --force ou --update.')
                return True
            else:
                if existing and force:
                    existing.delete()
                    self.stdout.write('🗑️  Configuração anterior removida.')
                
                self.stdout.write('✨ Criando nova configuração de email...')
                config = EmailConfiguration()
                config.name = "Configuração do .env"
                config.description = "Configuração sincronizada automaticamente do arquivo .env"
            
            # Mapear variáveis do .env
            backend = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
            config.email_backend = backend

            # Para console backend, não precisamos de host
            if 'console' in backend:
                config.email_host = 'localhost'  # Valor padrão para evitar validação
                config.email_port = 587
                config.email_host_user = ''
                config.email_host_password = ''
                config.email_use_tls = False
                config.email_use_ssl = False
            else:
                config.email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
                config.email_port = int(os.environ.get('EMAIL_PORT', '587'))
                config.email_host_user = os.environ.get('EMAIL_HOST_USER', '')
                config.email_host_password = os.environ.get('EMAIL_HOST_PASSWORD', '')
                config.email_use_tls = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
                config.email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'False').lower() == 'true'

            config.default_from_email = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@havoc.local')
            config.email_timeout = int(os.environ.get('EMAIL_TIMEOUT', '30'))
            
            # Definir como ativa e padrão se for a primeira
            if not EmailConfiguration.objects.exclude(pk=config.pk if config.pk else None).exists():
                config.is_active = True
                config.is_default = True
            else:
                config.is_active = True
                config.is_default = False
            
            config.save()
            
            self.stdout.write(f'✅ Configuração de email salva: {config.name}')
            self.stdout.write(f'   Backend: {config.email_backend}')
            self.stdout.write(f'   Host: {config.email_host or "Não configurado"}')
            self.stdout.write(f'   Usuário: {config.email_host_user or "Não configurado"}')
            
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao sincronizar email: {e}')
            )
            return False
    
    def sync_database_config(self, force=False, update=False):
        """Sincroniza configurações de banco de dados"""
        self.stdout.write('\n🗄️ Sincronizando configurações de BANCO DE DADOS...')
        
        try:
            # Verificar se já existe
            existing = DatabaseConfiguration.objects.filter(name="Configuração do .env").first()
            
            if existing and update:
                self.stdout.write('⚠️  Atualizando configuração existente...')
                config = existing
            elif existing and not force:
                self.stdout.write('ℹ️  Configuração já existe. Use --force ou --update.')
                return True
            else:
                if existing and force:
                    existing.delete()
                    self.stdout.write('🗑️  Configuração anterior removida.')
                
                self.stdout.write('✨ Criando nova configuração de banco...')
                config = DatabaseConfiguration()
                config.name = "Configuração do .env"
                config.description = "Configuração sincronizada automaticamente do arquivo .env"
            
            # Mapear variáveis do .env
            engine = os.environ.get('DATABASE_ENGINE', 'sqlite').lower()
            
            if engine == 'sqlite':
                config.engine = 'django.db.backends.sqlite3'
                config.name_db = os.environ.get('DATABASE_NAME', 'db.sqlite3')
                config.host = ''
                config.port = ''
                config.user = ''
                config.password = ''
            elif engine == 'postgresql':
                config.engine = 'django.db.backends.postgresql'
                config.name_db = os.environ.get('DATABASE_NAME', 'havoc')
                config.host = os.environ.get('DATABASE_HOST', 'localhost')
                config.port = os.environ.get('DATABASE_PORT', '5432')
                config.user = os.environ.get('DATABASE_USER', 'havoc_user')
                config.password = os.environ.get('DATABASE_PASSWORD', '')
            elif engine == 'mysql':
                config.engine = 'django.db.backends.mysql'
                config.name_db = os.environ.get('DATABASE_NAME', 'havoc')
                config.host = os.environ.get('DATABASE_HOST', 'localhost')
                config.port = os.environ.get('DATABASE_PORT', '3306')
                config.user = os.environ.get('DATABASE_USER', 'havoc_user')
                config.password = os.environ.get('DATABASE_PASSWORD', '')
            
            # Definir como ativa e padrão se for a primeira
            if not DatabaseConfiguration.objects.exclude(pk=config.pk if config.pk else None).exists():
                config.is_active = True
                config.is_default = True
            else:
                config.is_active = True
                config.is_default = False
            
            config.save()
            
            self.stdout.write(f'✅ Configuração de banco salva: {config.name}')
            self.stdout.write(f'   Engine: {config.engine}')
            self.stdout.write(f'   Nome: {config.name_db}')
            self.stdout.write(f'   Host: {config.host or "Local"}')
            
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao sincronizar banco: {e}')
            )
            return False
