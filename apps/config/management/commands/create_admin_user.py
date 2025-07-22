from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
import getpass

User = get_user_model()

class Command(BaseCommand):
    help = 'Cria um usuário administrador para o sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email do administrador',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Username do administrador',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Senha do administrador (não recomendado usar via linha de comando)',
        )
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Não solicita entrada do usuário',
        )

    def handle(self, *args, **options):
        if options['no_input']:
            if not all([options['email'], options['username'], options['password']]):
                self.stdout.write(
                    self.style.ERROR(
                        'Com --no-input, você deve fornecer --email, --username e --password'
                    )
                )
                return
            
            email = options['email']
            username = options['username']
            password = options['password']
        else:
            # Solicita dados interativamente
            email = self.get_email(options.get('email'))
            username = self.get_username(options.get('username'))
            password = self.get_password(options.get('password'))

        try:
            # Verifica se usuário já existe
            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.ERROR(f'Usuário com email {email} já existe!')
                )
                return

            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.ERROR(f'Usuário com username {username} já existe!')
                )
                return

            # Cria o usuário
            user = User.objects.create_user(
                email=email,
                username=username,
                password=password,
                is_staff=True,
                is_superuser=True,
                is_verified=True,
                first_name='Administrador',
                last_name='Sistema'
            )

            # Adiciona ao grupo de administradores se existir
            try:
                admin_group = Group.objects.get(name='Administradores')
                user.groups.add(admin_group)
                self.stdout.write(f'Usuário adicionado ao grupo Administradores')
            except Group.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        'Grupo Administradores não encontrado. Execute setup_permissions primeiro.'
                    )
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Usuário administrador criado com sucesso!\n'
                    f'Email: {user.email}\n'
                    f'Username: {user.username}\n'
                    f'ID: {user.id}'
                )
            )

        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(f'Erro de validação: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao criar usuário: {e}')
            )

    def get_email(self, default=None):
        """Solicita email do usuário"""
        while True:
            if default:
                email = input(f'Email [{default}]: ').strip() or default
            else:
                email = input('Email: ').strip()
            
            if email:
                # Validação básica de email
                if '@' in email and '.' in email:
                    return email
                else:
                    self.stdout.write(self.style.ERROR('Email inválido!'))
            else:
                self.stdout.write(self.style.ERROR('Email é obrigatório!'))

    def get_username(self, default=None):
        """Solicita username do usuário"""
        while True:
            if default:
                username = input(f'Username [{default}]: ').strip() or default
            else:
                username = input('Username: ').strip()
            
            if username:
                if len(username) >= 3:
                    return username
                else:
                    self.stdout.write(self.style.ERROR('Username deve ter pelo menos 3 caracteres!'))
            else:
                self.stdout.write(self.style.ERROR('Username é obrigatório!'))

    def get_password(self, default=None):
        """Solicita senha do usuário"""
        if default:
            return default
            
        while True:
            password = getpass.getpass('Senha: ')
            if len(password) >= 8:
                password_confirm = getpass.getpass('Confirme a senha: ')
                if password == password_confirm:
                    return password
                else:
                    self.stdout.write(self.style.ERROR('Senhas não coincidem!'))
            else:
                self.stdout.write(self.style.ERROR('Senha deve ter pelo menos 8 caracteres!'))
