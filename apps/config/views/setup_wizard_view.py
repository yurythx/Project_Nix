"""
Setup Wizard View - FireFlies
View principal que usa o orchestrator SOLID
"""

from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pathlib import Path
import json
from .setup_wizard import orchestrator
from django.core.cache import cache
import logging
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from apps.config.views.setup_wizard.orchestrator import SetupWizardOrchestrator
from apps.config.views.setup_wizard import wizard_steps

@method_decorator(never_cache, name='dispatch')
class SetupWizardView(View):
    """
    View principal do wizard de configuração
    Usa o orchestrator SOLID para processar os passos
    """
    template_name = 'config/setup_wizard_loader.html'

    def get(self, request):
        """Renderiza a tela do wizard"""
        return render(request, self.template_name)
    
    def post(self, request):
        """Processa os passos do wizard via orchestrator"""
        step = request.POST.get('step', 'database')
        try:
            return orchestrator.process_step(step, request)
        except Exception as e:
            messages.error(request, f"Erro durante a configuração: {str(e)}")
            return redirect('config:setup_wizard')


@method_decorator(csrf_exempt, name='dispatch')
class SetupAPIView(View):
    """
    API para o wizard de configuração
    Processa requisições AJAX do frontend
    """
    
    def get(self, request):
        """Handle GET requests for database step data"""
        print(f"SetupAPIView.get called with path: {request.path}")
        path = request.path
        if 'database-step' in path:
            return self.get_database_step_data(request)
        else:
            return JsonResponse({'error': 'Endpoint não encontrado'}, status=404)
    
    def post(self, request):
        """Processa requisições da API"""
        print(f"SetupAPIView.post called with path: {request.path}")
        logger = logging.getLogger(__name__)
        logger.info(f"SetupAPIView.post called with path: {request.path}")
        
        path = request.path
        
        # Handle finalize endpoint
        if 'finalize' in path:
            print("Calling finalize_setup")
            logger.info("Calling finalize_setup")
            return self.finalize_setup(request)
        
        # Handle other actions
        action = request.POST.get('action')

        if action == 'get_wizard_content':
            return self.get_wizard_content(request)
        elif action == 'test_connection':
            return self.test_database_connection(request)
        elif action == 'save_config':
            return self.save_configuration(request)
        else:
            return JsonResponse({'error': 'Ação inválida'}, status=400)
    
    def get_database_step_data(self, request):
        """Retorna dados para o passo do banco de dados"""
        try:
            # Simular dados de detecção de banco
            data = {
                'statistics': {
                    'total_databases': 3,
                    'django_databases': 1,
                    'sqlite_count': 2,
                    'postgresql_count': 1,
                    'mysql_count': 0
                },
                'recommended_databases': [
                    {
                        'type': 'sqlite',
                        'name': 'db.sqlite3',
                        'display_name': 'SQLite Local',
                        'description': 'Banco local para desenvolvimento',
                        'tables_count': 0,
                        'size': '0 MB',
                        'host': 'localhost',
                        'port': '',
                        'user': ''
                    }
                ],
                'other_databases': []
            }
            
            return JsonResponse(data)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def get_wizard_content(self, request):
        """Renderiza o conteúdo do wizard e retorna como HTML para carregamento assíncrono."""
        try:
            from django.template.loader import render_to_string
            
            current_step_str = request.POST.get('step', '1')
            
            try:
                current_step = int(current_step_str)
            except (ValueError, TypeError):
                current_step = 1

            context = {
                'request': request,
                'step': current_step_str,
                'current_step': current_step,
                'total_steps': 6,
            }
            
            # Use the main wizard template
            html_content = render_to_string('config/setup_wizard_loader.html', context)
            
            return JsonResponse({
                'success': True, 
                'html': html_content,
                'current_step': current_step
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    def test_database_connection(self, request):
        """Testa conexão com banco de dados via API"""
        try:
            database_type = request.POST.get('database_type')
            
            # Construir configuração baseada no tipo de banco
            config = {'type': database_type}
            
            if database_type == 'sqlite':
                config['NAME'] = request.POST.get('sqlite_name', 'db.sqlite3')
            elif database_type == 'postgresql':
                config.update({
                    'HOST': request.POST.get('pg_host', 'localhost'),
                    'PORT': request.POST.get('pg_port', '5432'),
                    'USER': request.POST.get('pg_user', 'postgres'),
                    'PASSWORD': request.POST.get('pg_password', ''),
                    'NAME': request.POST.get('pg_name', 'fireflies'),
                })
            elif database_type == 'mysql':
                config.update({
                    'HOST': request.POST.get('mysql_host', 'localhost'),
                    'PORT': request.POST.get('mysql_port', '3306'),
                    'USER': request.POST.get('mysql_user', 'root'),
                    'PASSWORD': request.POST.get('mysql_password', ''),
                    'NAME': request.POST.get('mysql_name', 'fireflies'),
                })
            
            success = orchestrator.test_database_connection(config)
            
            return JsonResponse({
                'success': success,
                'message': 'Conexão bem-sucedida' if success else 'Falha na conexão'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def save_configuration(self, request):
        """Salva configuração via API"""
        try:
            step = request.POST.get('step')
            
            # Processar dados do formulário baseado no passo
            config = {}
            
            if step == '1':  # Banco de dados
                config = {
                    'database_type': request.POST.get('database_type'),
                    'sqlite_name': request.POST.get('sqlite_name'),
                    'sqlite_existing': request.POST.get('sqlite_existing'),
                    'pg_host': request.POST.get('pg_host'),
                    'pg_port': request.POST.get('pg_port'),
                    'pg_user': request.POST.get('pg_user'),
                    'pg_password': request.POST.get('pg_password'),
                    'pg_name': request.POST.get('pg_name'),
                    'pg_existing': request.POST.get('pg_existing'),
                    'mysql_host': request.POST.get('mysql_host'),
                    'mysql_port': request.POST.get('mysql_port'),
                    'mysql_user': request.POST.get('mysql_user'),
                    'mysql_password': request.POST.get('mysql_password'),
                    'mysql_name': request.POST.get('mysql_name'),
                    'mysql_existing': request.POST.get('mysql_existing'),
                }
            elif step == '2':  # Administrador
                config = {
                    'username': request.POST.get('username'),
                    'email': request.POST.get('email'),
                    'password': request.POST.get('password'),
                    'password_confirm': request.POST.get('password_confirm'),
                }
            elif step == '3':  # Email
                config = {
                    'email_host': request.POST.get('email_host'),
                    'email_port': request.POST.get('email_port'),
                    'email_user': request.POST.get('email_user'),
                    'email_password': request.POST.get('email_password'),
                    'email_use_tls': request.POST.get('email_use_tls', 'True'),
                }
            elif step == '4':  # Segurança
                config = {
                    'secret_key': request.POST.get('secret_key'),
                    'debug_mode': request.POST.get('debug_mode', 'True'),
                }
            
            # Salvar no cache
            cache_key = f'setup_wizard_step_{step}'
            cache.set(cache_key, config, timeout=3600)
            
            return JsonResponse({
                'success': True,
                'message': f'Configuração do passo {step} salva com sucesso'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def finalize_setup(self, request):
        """Finaliza configuração via API"""
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"Finalize setup called with method: {request.method}")
            logger.info(f"Request path: {request.path}")
            logger.info(f"Request headers: {dict(request.headers)}")
            
            # Parse JSON data from frontend
            import json
            data = json.loads(request.body)
            logger.info(f"Received data: {data}")
            
            # Extract configuration data
            database_config = data.get('database', {})
            admin_config = data.get('admin', {})
            email_config = data.get('email', {})
            security_config = data.get('security', {})
            
            # Use orchestrator to apply configurations
            success = orchestrator.apply_all_configurations(
                database_config=database_config,
                admin_config=admin_config,
                email_config=email_config,
                security_config=security_config
            )
            
            if success:
                # Remove .first_install file
                first_install_file = Path(settings.BASE_DIR) / '.first_install'
                if first_install_file.exists():
                    first_install_file.unlink()
                
                logger.info("Setup finalized successfully")
                return JsonResponse({
                    'success': True,
                    'message': 'Configuração finalizada com sucesso!'
                })
            else:
                logger.error("Failed to apply configurations")
                return JsonResponse({
                    'success': False,
                    'error': 'Erro ao aplicar configurações'
                }, status=500)
                
        except Exception as e:
            logger.error(f"Error in finalize_setup: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@never_cache
def setup_redirect(request):
    """Redireciona para o wizard se necessário"""
    first_install_file = Path(settings.BASE_DIR) / '.first_install'
    
    if first_install_file.exists():
        return redirect('config:setup_wizard')
    else:
        return redirect('pages:home')

@csrf_exempt
def test_db_connection_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            orchestrator = SetupWizardOrchestrator(wizard_steps)
            result = orchestrator.test_database_connection(data)
            if result:
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Falha na conexão com o banco de dados.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método não permitido.'}, status=405) 