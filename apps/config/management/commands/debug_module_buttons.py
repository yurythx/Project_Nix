from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.config.models.app_module_config import AppModuleConfiguration
import json

User = get_user_model()

class Command(BaseCommand):
    help = 'Debug module enable/disable buttons functionality'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Iniciando debug dos botões de módulos...'))
        
        # Criar cliente de teste
        client = Client()
        
        # Obter ou criar usuário admin
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.create_superuser(
                    username='admin_test',
                    email='admin@test.com',
                    password='admin123'
                )
                self.stdout.write(self.style.WARNING('Usuário admin criado para teste'))
                password = 'admin123'
            else:
                # Resetar senha do usuário existente para garantir login
                admin_user.set_password('admin123')
                admin_user.save()
                password = 'admin123'
                self.stdout.write(self.style.WARNING(f'Senha do usuário {admin_user.username} resetada para teste'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao obter usuário admin: {e}'))
            return
        
        # Fazer login
        login_success = client.login(username=admin_user.username, password=password)
        
        if not login_success:
            self.stdout.write(self.style.ERROR(f'Falha no login do usuário admin: {admin_user.username}'))
            return
        
        self.stdout.write(self.style.SUCCESS('✅ Login realizado com sucesso'))
        
        # Testar acesso à página de módulos
        try:
            response = client.get(reverse('config:module_list'))
            self.stdout.write(f'📄 Status da página de módulos: {response.status_code}')
            
            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f'Erro ao acessar página de módulos: {response.status_code}'))
                return
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao acessar página de módulos: {e}'))
            return
        
        # Obter módulos disponíveis
        modules = AppModuleConfiguration.objects.filter(is_core=False)
        self.stdout.write(f'📦 Módulos não-core encontrados: {modules.count()}')
        
        if not modules.exists():
            self.stdout.write(self.style.WARNING('Nenhum módulo não-core encontrado para teste'))
            return
        
        # Testar cada módulo
        for module in modules:
            self.stdout.write(f'\n🔧 Testando módulo: {module.app_name}')
            self.stdout.write(f'   Status atual: {"Ativo" if module.is_enabled else "Inativo"}')
            
            # Testar desativação se estiver ativo
            if module.is_enabled:
                self.test_module_disable(client, module)
            
            # Testar ativação se estiver inativo
            if not module.is_enabled:
                self.test_module_enable(client, module)
        
        self.stdout.write(self.style.SUCCESS('\n✅ Debug concluído!'))
    
    def test_module_disable(self, client, module):
        """Testa a desativação de um módulo"""
        try:
            url = reverse('config:module_disable', args=[module.app_name])
            self.stdout.write(f'   🔴 Testando desativação via: {url}')
            
            response = client.post(url, follow=True)
            self.stdout.write(f'   Status da resposta: {response.status_code}')
            
            # Verificar se o módulo foi desativado
            module.refresh_from_db()
            if not module.is_enabled:
                self.stdout.write(self.style.SUCCESS('   ✅ Módulo desativado com sucesso'))
            else:
                self.stdout.write(self.style.ERROR('   ❌ Falha ao desativar módulo'))
                
            # Verificar mensagens
            messages = list(response.context.get('messages', []))
            for message in messages:
                self.stdout.write(f'   💬 Mensagem: {message}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Erro ao testar desativação: {e}'))
    
    def test_module_enable(self, client, module):
        """Testa a ativação de um módulo"""
        try:
            url = reverse('config:module_enable', args=[module.app_name])
            self.stdout.write(f'   🟢 Testando ativação via: {url}')
            
            response = client.post(url, follow=True)
            self.stdout.write(f'   Status da resposta: {response.status_code}')
            
            # Verificar se o módulo foi ativado
            module.refresh_from_db()
            if module.is_enabled:
                self.stdout.write(self.style.SUCCESS('   ✅ Módulo ativado com sucesso'))
            else:
                self.stdout.write(self.style.ERROR('   ❌ Falha ao ativar módulo'))
                
            # Verificar mensagens
            messages = list(response.context.get('messages', []))
            for message in messages:
                self.stdout.write(f'   💬 Mensagem: {message}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Erro ao testar ativação: {e}'))