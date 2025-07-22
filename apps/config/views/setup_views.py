"""
Views para configuração pós-deploy do FireFlies
Similar ao Zabbix e GLPI, permite configurar banco de dados após primeira instalação
"""

import os
import json
import shutil
from pathlib import Path
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.conf import settings
from django.db import connections, connection
from django.core.exceptions import ImproperlyConfigured
from django.utils.decorators import method_decorator
from django.views import View
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache
from django.core.management import call_command
from django.core.management.base import CommandError
import psycopg2

# Importação condicional do MySQL
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    MySQLError = Exception


@method_decorator(csrf_exempt, name='dispatch')
class SetupAPIView(View):
    """
    API para configuração pós-deploy
    """
    
    def post(self, request):
        """API para testar conexões e salvar configurações"""
        try:
            action = request.POST.get('action')
            
            if action == 'test_database':
                return self.test_database_connection(request)
            elif action == 'save_config':
                return self.save_configuration(request)
            elif action == 'finalize':
                return self.finalize_setup(request)
            else:
                return JsonResponse({'error': 'Ação inválida'}, status=400)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def test_database_connection(self, request):
        """Testa conexão com banco de dados"""
        db_type = request.POST.get('db_type')
        
        try:
            if db_type == 'postgresql':
                conn = psycopg2.connect(
                    host=request.POST.get('db_host'),
                    port=request.POST.get('db_port', '5432'),
                    database=request.POST.get('db_name'),
                    user=request.POST.get('db_user'),
                    password=request.POST.get('db_password'),
                    connect_timeout=10
                )
                conn.close()
                
            elif db_type == 'mysql':
                if not MYSQL_AVAILABLE:
                    return JsonResponse({'error': 'MySQL não está disponível. Instale mysql-connector-python para usar MySQL.'}, status=400)
                
                conn = mysql.connector.connect(
                    host=request.POST.get('db_host'),
                    port=request.POST.get('db_port', '3306'),
                    database=request.POST.get('db_name'),
                    user=request.POST.get('db_user'),
                    password=request.POST.get('db_password'),
                    connection_timeout=10
                )
                conn.close()
                
            return JsonResponse({'success': True, 'message': 'Conexão bem-sucedida!'})
            
        except Exception as e:
            return JsonResponse({'error': f'Falha na conexão: {str(e)}'}, status=400)
    
    def save_configuration(self, request):
        """Salva configuração temporária"""
        config_type = request.POST.get('config_type')
        
        try:
            if config_type == 'database':
                config = {
                    'ENGINE': request.POST.get('db_engine'),
                    'NAME': request.POST.get('db_name'),
                    'USER': request.POST.get('db_user'),
                    'PASSWORD': request.POST.get('db_password'),
                    'HOST': request.POST.get('db_host'),
                    'PORT': request.POST.get('db_port'),
                }
                
                temp_file = Path(settings.BASE_DIR) / '.temp_db_config.json'
                with open(temp_file, 'w') as f:
                    json.dump(config, f, indent=2)
                    
            return JsonResponse({'success': True, 'message': 'Configuração salva!'})
            
        except Exception as e:
            return JsonResponse({'error': f'Erro ao salvar: {str(e)}'}, status=500)
    
    def finalize_setup(self, request):
        """Finaliza a configuração"""
        try:
            # Usar o orchestrator para aplicar configurações
            from .setup_wizard import orchestrator
            success = orchestrator.apply_all_configurations()
            
            if success:
                # Remover arquivo de primeira instalação
                first_install_file = Path(settings.BASE_DIR) / '.first_install'
                if first_install_file.exists():
                    first_install_file.unlink()
            
            return JsonResponse({'success': success, 'message': 'Configuração finalizada!' if success else 'Erro na finalização'})
            
        except Exception as e:
            return JsonResponse({'error': f'Erro ao finalizar: {str(e)}'}, status=500)


@never_cache
def setup_redirect(request):
    """
    Redireciona para setup se for primeira instalação
    """
    first_install_file = Path(settings.BASE_DIR) / '.first_install'
    
    if first_install_file.exists():
        return redirect('config:setup_wizard')
    else:
        return redirect('pages:home')  # Redireciona para a página inicial do app pages 