"""
Comando para marcar o sistema como primeira instalação
"""

from django.core.management.base import BaseCommand
from pathlib import Path
from django.conf import settings


class Command(BaseCommand):
    help = 'Marca o sistema como primeira instalação para ativar o wizard de configuração'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a criação mesmo se já existir',
        )
        parser.add_argument(
            '--remove',
            action='store_true',
            help='Remove o arquivo de primeira instalação',
        )

    def handle(self, *args, **options):
        first_install_file = Path(settings.BASE_DIR) / '.first_install'
        
        if options['remove']:
            if first_install_file.exists():
                first_install_file.unlink()
                self.stdout.write(
                    self.style.SUCCESS('✅ Arquivo de primeira instalação removido')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️ Arquivo de primeira instalação não existe')
                )
            return
        
        if first_install_file.exists() and not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️ Arquivo de primeira instalação já existe. '
                    'Use --force para sobrescrever.'
                )
            )
            return
        
        # Criar arquivo de primeira instalação
        first_install_file.touch()
        
        self.stdout.write(
            self.style.SUCCESS(
                '✅ Sistema marcado como primeira instalação!\n'
                '🔧 Acesse /config/setup/ para configurar o sistema.'
            )
        )
        
        # Mostrar informações adicionais
        self.stdout.write('\n📋 Próximos passos:')
        self.stdout.write('1. Acesse http://localhost:8000/')
        self.stdout.write('2. Configure o banco de dados')
        self.stdout.write('3. Crie o usuário administrador')
        self.stdout.write('4. Configure o sistema de email')
        self.stdout.write('5. Finalize a configuração')
        
        self.stdout.write('\n💡 Para remover o modo primeira instalação:')
        self.stdout.write('   python manage.py create_first_install --remove') 