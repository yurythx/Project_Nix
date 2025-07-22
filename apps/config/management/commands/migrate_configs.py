from django.core.management.base import BaseCommand
from django.conf import settings
from apps.config.models import EmailConfiguration, DatabaseConfiguration
from apps.config.services.system_config_service import SystemConfigService
from apps.config.repositories.config_repository import DjangoSystemConfigRepository


class Command(BaseCommand):
    help = 'Migra configurações antigas para o novo sistema de múltiplas configurações'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a migração mesmo se já existirem configurações',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== MIGRAÇÃO DE CONFIGURAÇÕES ===\n'))
        
        force = options.get('force', False)
        
        # Migrar configurações de email
        self.migrate_email_configs(force)
        
        # Migrar configurações de banco (se necessário)
        self.migrate_database_configs(force)
        
        self.stdout.write(self.style.SUCCESS('\n✅ Migração concluída!'))

    def migrate_email_configs(self, force=False):
        """Migra configurações de email"""
        self.stdout.write('📧 Migrando configurações de email...')
        
        # Verificar se já existem configurações
        existing_configs = EmailConfiguration.objects.count()
        if existing_configs > 0 and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'   ⚠️  Já existem {existing_configs} configurações de email. '
                    'Use --force para sobrescrever.'
                )
            )
            return
        
        # Tentar carregar configuração do sistema antigo
        try:
            config_service = SystemConfigService(
                DjangoSystemConfigRepository(),
                None
            )
            
            old_config = config_service.get_config('email_settings')
            
            if old_config and isinstance(old_config, dict):
                self.stdout.write('   📋 Configuração antiga encontrada no banco')
                
                # Criar nova configuração baseada na antiga
                email_config = EmailConfiguration(
                    name='Configuração Migrada',
                    description='Configuração migrada do sistema antigo',
                    email_backend=old_config.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend'),
                    email_host=old_config.get('EMAIL_HOST', ''),
                    email_port=old_config.get('EMAIL_PORT', 587),
                    email_host_user=old_config.get('EMAIL_HOST_USER', ''),
                    email_host_password=old_config.get('EMAIL_HOST_PASSWORD', ''),
                    email_use_tls=old_config.get('EMAIL_USE_TLS', True),
                    email_use_ssl=old_config.get('EMAIL_USE_SSL', False),
                    default_from_email=old_config.get('DEFAULT_FROM_EMAIL', 'noreply@havoc.com'),
                    email_timeout=old_config.get('EMAIL_TIMEOUT', 30),
                    is_active=True,
                    is_default=True
                )
                
                email_config.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'   ✅ Configuração "{email_config.name}" criada como padrão'
                    )
                )
                
            else:
                # Criar configuração baseada no settings.py
                self.stdout.write('   📋 Usando configurações do settings.py')
                
                # Verificar se há configurações válidas no settings
                email_host = getattr(settings, 'EMAIL_HOST', '')
                email_user = getattr(settings, 'EMAIL_HOST_USER', '')

                if not email_host or not email_user:
                    # Criar configuração de console se não há SMTP configurado
                    email_config = EmailConfiguration(
                        name='Console (Desenvolvimento)',
                        description='Backend de console para desenvolvimento - emails aparecem no terminal',
                        email_backend='django.core.mail.backends.console.EmailBackend',
                        email_host='localhost',
                        email_port=587,
                        email_host_user='console@localhost',
                        email_host_password='console',
                        email_use_tls=False,
                        email_use_ssl=False,
                        default_from_email='noreply@havoc.com',
                        email_timeout=30,
                        is_active=True,
                        is_default=True
                    )
                else:
                    # Usar configurações do settings
                    email_config = EmailConfiguration(
                        name='Configuração do Settings',
                        description='Configuração baseada no arquivo settings.py',
                        email_backend=getattr(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend'),
                        email_host=email_host,
                        email_port=getattr(settings, 'EMAIL_PORT', 587),
                        email_host_user=email_user,
                        email_host_password=getattr(settings, 'EMAIL_HOST_PASSWORD', ''),
                        email_use_tls=getattr(settings, 'EMAIL_USE_TLS', True),
                        email_use_ssl=getattr(settings, 'EMAIL_USE_SSL', False),
                        default_from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@havoc.com'),
                        email_timeout=getattr(settings, 'EMAIL_TIMEOUT', 30),
                        is_active=True,
                        is_default=True
                    )
                
                # Definir usuário criador como None (será tratado pelo modelo)
                email_config.created_by = None
                email_config.updated_by = None
                email_config.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'   ✅ Configuração "{email_config.name}" criada como padrão'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Erro na migração de email: {e}')
            )

    def migrate_database_configs(self, force=False):
        """Migra configurações de banco de dados"""
        self.stdout.write('\n🗄️  Migrando configurações de banco...')
        
        # Verificar se já existem configurações
        existing_configs = DatabaseConfiguration.objects.count()
        if existing_configs > 0 and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'   ⚠️  Já existem {existing_configs} configurações de banco. '
                    'Use --force para sobrescrever.'
                )
            )
            return
        
        try:
            # Usar configuração padrão do Django
            default_db = settings.DATABASES.get('default', {})
            
            if default_db:
                db_config = DatabaseConfiguration(
                    name='Banco Principal',
                    description='Configuração principal do banco de dados',
                    engine=default_db.get('ENGINE', 'django.db.backends.sqlite3'),
                    name_db=default_db.get('NAME', 'db.sqlite3'),
                    user=default_db.get('USER', ''),
                    password=default_db.get('PASSWORD', ''),
                    host=default_db.get('HOST', ''),
                    port=default_db.get('PORT', ''),
                    options=default_db.get('OPTIONS', {}),
                    is_active=True,
                    is_default=True
                )
                
                db_config.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'   ✅ Configuração "{db_config.name}" criada como padrão'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING('   ⚠️  Nenhuma configuração de banco encontrada')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Erro na migração de banco: {e}')
            )

    def create_sample_configs(self):
        """Cria configurações de exemplo"""
        self.stdout.write('\n🎯 Criando configurações de exemplo...')
        
        # Configurações de email de exemplo
        sample_email_configs = [
            {
                'name': 'Gmail Exemplo',
                'description': 'Configuração de exemplo para Gmail',
                'email_host': 'smtp.gmail.com',
                'email_port': 587,
                'email_host_user': 'seu-email@gmail.com',
                'email_host_password': 'sua-senha-de-app',
                'email_use_tls': True,
                'default_from_email': 'seu-email@gmail.com',
                'is_active': False,
            },
            {
                'name': 'Outlook Exemplo',
                'description': 'Configuração de exemplo para Outlook',
                'email_host': 'smtp-mail.outlook.com',
                'email_port': 587,
                'email_host_user': 'seu-email@outlook.com',
                'email_host_password': 'sua-senha',
                'email_use_tls': True,
                'default_from_email': 'seu-email@outlook.com',
                'is_active': False,
            }
        ]
        
        for config_data in sample_email_configs:
            if not EmailConfiguration.objects.filter(name=config_data['name']).exists():
                config = EmailConfiguration(**config_data)
                config.save()
                self.stdout.write(f'   ✅ Exemplo "{config.name}" criado')
        
        # Configurações de banco de exemplo
        sample_db_configs = [
            {
                'name': 'PostgreSQL Exemplo',
                'description': 'Configuração de exemplo para PostgreSQL',
                'engine': 'django.db.backends.postgresql',
                'name_db': 'meu_banco',
                'user': 'usuario',
                'password': 'senha',
                'host': 'localhost',
                'port': '5432',
                'is_active': False,
            },
            {
                'name': 'MySQL Exemplo',
                'description': 'Configuração de exemplo para MySQL',
                'engine': 'django.db.backends.mysql',
                'name_db': 'meu_banco',
                'user': 'usuario',
                'password': 'senha',
                'host': 'localhost',
                'port': '3306',
                'is_active': False,
            }
        ]
        
        for config_data in sample_db_configs:
            if not DatabaseConfiguration.objects.filter(name=config_data['name']).exists():
                config = DatabaseConfiguration(**config_data)
                config.save()
                self.stdout.write(f'   ✅ Exemplo "{config.name}" criado')

    def show_status(self):
        """Mostra status atual das configurações"""
        self.stdout.write('\n📊 Status atual:')
        
        # Email
        email_configs = EmailConfiguration.objects.all()
        default_email = EmailConfiguration.get_default()
        
        self.stdout.write(f'   📧 Email: {email_configs.count()} configurações')
        if default_email:
            self.stdout.write(f'      🌟 Padrão: {default_email.name}')
        
        # Banco
        db_configs = DatabaseConfiguration.objects.all()
        default_db = DatabaseConfiguration.get_default()
        
        self.stdout.write(f'   🗄️  Banco: {db_configs.count()} configurações')
        if default_db:
            self.stdout.write(f'      🌟 Padrão: {default_db.name}')
        
        self.stdout.write('\n💡 Para gerenciar configurações:')
        self.stdout.write('   • Email: /config/emails/')
        self.stdout.write('   • Banco: /config/bancos/')
        self.stdout.write('   • Diagnóstico: /accounts/email/diagnostico/')
