from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class Command(BaseCommand):
    help = 'Ativa e verifica um superusuário existente'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email do superusuário para ativar',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Username do superusuário para ativar',
        )
        parser.add_argument(
            '--reset-password',
            type=str,
            help='Nova senha para o superusuário',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Lista todos os superusuários',
        )

    def handle(self, *args, **options):
        if options['list']:
            self.list_superusers()
            return

        # Buscar usuário por email ou username
        user = None
        if options['email']:
            try:
                user = User.objects.get(email=options['email'])
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Usuário com email {options["email"]} não encontrado!')
                )
                return
        elif options['username']:
            try:
                user = User.objects.get(username=options['username'])
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Usuário com username {options["username"]} não encontrado!')
                )
                return
        else:
            self.stdout.write(
                self.style.ERROR('Você deve fornecer --email ou --username')
            )
            return

        # Ativar e verificar usuário
        try:
            changes_made = []
            
            if not user.is_active:
                user.is_active = True
                changes_made.append('is_active = True')
            
            if not user.is_verified:
                user.is_verified = True
                changes_made.append('is_verified = True')
            
            if not user.is_superuser:
                user.is_superuser = True
                changes_made.append('is_superuser = True')
            
            if not user.is_staff:
                user.is_staff = True
                changes_made.append('is_staff = True')
            
            # Redefinir senha se solicitado
            if options['reset_password']:
                user.set_password(options['reset_password'])
                changes_made.append('senha redefinida')
            
            if changes_made:
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Usuário {user.email} atualizado com sucesso!\n'
                        f'Alterações: {", ".join(changes_made)}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Usuário {user.email} já está ativo e configurado corretamente.'
                    )
                )
            
            # Mostrar status atual
            self.show_user_status(user)

        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(f'Erro de validação: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao ativar usuário: {e}')
            )

    def list_superusers(self):
        """Lista todos os superusuários"""
        superusers = User.objects.filter(is_superuser=True)
        
        if not superusers.exists():
            self.stdout.write(
                self.style.WARNING('Nenhum superusuário encontrado.')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'Encontrados {superusers.count()} superusuário(s):')
        )
        
        for user in superusers:
            status_parts = []
            if user.is_active:
                status_parts.append(self.style.SUCCESS('ATIVO'))
            else:
                status_parts.append(self.style.ERROR('INATIVO'))
            
            if user.is_verified:
                status_parts.append(self.style.SUCCESS('VERIFICADO'))
            else:
                status_parts.append(self.style.WARNING('NÃO VERIFICADO'))
            
            self.stdout.write(
                f'  • {user.email} ({user.username}) - {" | ".join(status_parts)}'
            )

    def show_user_status(self, user):
        """Mostra o status detalhado do usuário"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'STATUS DO USUÁRIO: {user.email}')
        self.stdout.write('='*50)
        self.stdout.write(f'Username: {user.username}')
        self.stdout.write(f'Email: {user.email}')
        self.stdout.write(f'Nome: {user.get_full_name() or "Não informado"}')
        self.stdout.write(f'is_active: {self.style.SUCCESS("✓") if user.is_active else self.style.ERROR("✗")}')
        self.stdout.write(f'is_verified: {self.style.SUCCESS("✓") if user.is_verified else self.style.ERROR("✗")}')
        self.stdout.write(f'is_superuser: {self.style.SUCCESS("✓") if user.is_superuser else self.style.ERROR("✗")}')
        self.stdout.write(f'is_staff: {self.style.SUCCESS("✓") if user.is_staff else self.style.ERROR("✗")}')
        self.stdout.write(f'Data de criação: {user.date_joined}')
        self.stdout.write(f'Último login: {user.last_login or "Nunca"}')
        self.stdout.write('='*50)
