from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Configura permissões e grupos padrão do sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Remove grupos existentes antes de criar novos',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Removendo grupos existentes...')
            Group.objects.filter(name__in=[
                'Administradores',
                'Gerentes',
                'Operadores',
                'Usuários'
            ]).delete()

        # Cria grupos padrão
        self.create_groups()
        
        # Atribui permissões aos grupos
        self.assign_permissions()
        
        self.stdout.write(
            self.style.SUCCESS('Permissões e grupos configurados com sucesso!')
        )

    def create_groups(self):
        """Cria grupos padrão"""
        groups_data = [
            {
                'name': 'Administradores',
                'description': 'Acesso total ao sistema'
            },
            {
                'name': 'Gerentes',
                'description': 'Gerenciamento de usuários e configurações'
            },
            {
                'name': 'Operadores',
                'description': 'Operações básicas do sistema'
            },
            {
                'name': 'Usuários',
                'description': 'Acesso básico ao sistema'
            },
            {
                'name': 'Editor',
                'description': 'Pode criar, editar e deletar artigos, mas não acessar configurações'
            }
        ]

        for group_data in groups_data:
            group, created = Group.objects.get_or_create(
                name=group_data['name']
            )
            if created:
                self.stdout.write(f'Grupo criado: {group.name}')
            else:
                self.stdout.write(f'Grupo já existe: {group.name}')

    def assign_permissions(self):
        """Atribui permissões aos grupos"""
        
        # Obtém content types
        user_ct = ContentType.objects.get_for_model(User)
        group_ct = ContentType.objects.get_for_model(Group)
        # Artigos
        from apps.articles.models.article import Article
        article_ct = ContentType.objects.get_for_model(Article)
        
        # Obtém grupos
        admin_group = Group.objects.get(name='Administradores')
        manager_group = Group.objects.get(name='Gerentes')
        operator_group = Group.objects.get(name='Operadores')
        user_group = Group.objects.get(name='Usuários')
        editor_group = Group.objects.get(name='Editor')

        # Permissões para Administradores (todas)
        admin_permissions = Permission.objects.all()
        admin_group.permissions.set(admin_permissions)
        self.stdout.write(f'Atribuídas {admin_permissions.count()} permissões para Administradores')

        # Permissões para Gerentes
        manager_permissions = Permission.objects.filter(
            content_type__in=[user_ct, group_ct]
        )
        manager_group.permissions.set(manager_permissions)
        self.stdout.write(f'Atribuídas {manager_permissions.count()} permissões para Gerentes')

        # Permissões para Operadores
        operator_permissions = Permission.objects.filter(
            content_type=user_ct,
            codename__in=['view_user', 'change_user']
        )
        operator_group.permissions.set(operator_permissions)
        self.stdout.write(f'Atribuídas {operator_permissions.count()} permissões para Operadores')

        # Permissões para Usuários (apenas visualização própria)
        user_permissions = Permission.objects.filter(
            content_type=user_ct,
            codename='view_user'
        )
        user_group.permissions.set(user_permissions)
        self.stdout.write(f'Atribuídas {user_permissions.count()} permissões para Usuários')

        # Permissões para Editor (artigos)
        editor_permissions = Permission.objects.filter(
            content_type=article_ct,
            codename__in=['add_article', 'change_article', 'delete_article', 'view_article']
        )
        editor_group.permissions.set(editor_permissions)
        self.stdout.write(f'Atribuídas {editor_permissions.count()} permissões para Editor')

    def create_custom_permissions(self):
        """Cria permissões customizadas se necessário"""
        custom_permissions = [
            {
                'codename': 'can_manage_system_config',
                'name': 'Can manage system configuration',
                'content_type': ContentType.objects.get_for_model(User)
            },
            {
                'codename': 'can_view_audit_logs',
                'name': 'Can view audit logs',
                'content_type': ContentType.objects.get_for_model(User)
            },
            {
                'codename': 'can_export_data',
                'name': 'Can export system data',
                'content_type': ContentType.objects.get_for_model(User)
            }
        ]

        for perm_data in custom_permissions:
            permission, created = Permission.objects.get_or_create(
                codename=perm_data['codename'],
                content_type=perm_data['content_type'],
                defaults={'name': perm_data['name']}
            )
            if created:
                self.stdout.write(f'Permissão customizada criada: {permission.name}')
            else:
                self.stdout.write(f'Permissão customizada já existe: {permission.name}')
