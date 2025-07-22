"""
Views para informações de banco de dados (somente leitura)
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
import os
from pathlib import Path
from django.views.generic import TemplateView, View
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt


def is_admin_user(user):
    """Verifica se o usuário é admin"""
    return user.is_authenticated and user.is_staff


class DatabaseInfoView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'config/database/info.html'

    def test_func(self):
        return is_admin_user(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Informações do Banco de Dados',
            'page_description': 'Status e configurações atuais do banco de dados',
            'db_info': get_database_info(),
            'env_info': get_env_database_info(),
            'connection_status': test_database_connection(),
            'breadcrumbs': [
                {'name': 'Configurações', 'url': '/config/'},
                {'name': 'Banco de Dados', 'url': None}
            ]
        })
        return context


@method_decorator(csrf_exempt, name='dispatch')
class DatabaseConnectionTestAjaxView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return is_admin_user(self.request.user)

    def post(self, request, *args, **kwargs):
        status = test_database_connection()
        return JsonResponse(status)

    def get(self, request, *args, **kwargs):
        return JsonResponse({'error': 'Método não permitido'}, status=405)


def get_database_info():
    """Obtém informações do banco de dados atual"""
    try:
        db_settings = settings.DATABASES['default']
        
        info = {
            'engine': db_settings.get('ENGINE', ''),
            'name': db_settings.get('NAME', ''),
            'host': db_settings.get('HOST', ''),
            'port': db_settings.get('PORT', ''),
            'user': db_settings.get('USER', ''),
            'is_sqlite': 'sqlite' in db_settings.get('ENGINE', '').lower(),
            'is_postgresql': 'postgresql' in db_settings.get('ENGINE', '').lower(),
            'is_mysql': 'mysql' in db_settings.get('ENGINE', '').lower(),
        }
        
        # Determinar tipo de banco
        if info['is_sqlite']:
            info['type'] = 'SQLite'
            info['file_path'] = info['name']
        elif info['is_postgresql']:
            info['type'] = 'PostgreSQL'
        elif info['is_mysql']:
            info['type'] = 'MySQL'
        else:
            info['type'] = 'Desconhecido'
            
        return info
        
    except Exception as e:
        return {
            'error': f'Erro ao obter informações do banco: {str(e)}',
            'type': 'Erro'
        }


def get_env_database_info():
    """Obtém informações do banco no arquivo .env"""
    try:
        env_file = Path(settings.BASE_DIR) / '.env'
        
        if not env_file.exists():
            return {'exists': False, 'message': 'Arquivo .env não encontrado'}
        
        env_content = env_file.read_text(encoding='utf-8')
        lines = env_content.split('\n')
        
        db_vars = {}
        for line in lines:
            if '=' in line and any(var in line for var in ['DB_', 'DATABASE_']):
                key, value = line.split('=', 1)
                db_vars[key.strip()] = value.strip()
        
        return {
            'exists': True,
            'variables': db_vars,
            'has_database_url': 'DATABASE_URL' in db_vars,
            'has_db_engine': 'DB_ENGINE' in db_vars,
        }
        
    except Exception as e:
        return {
            'exists': False,
            'error': f'Erro ao ler arquivo .env: {str(e)}'
        }


def test_database_connection():
    """Testa a conexão com o banco de dados"""
    try:
        # Testar conexão
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        # Obter informações adicionais
        db_info = {}
        
        if 'sqlite' in settings.DATABASES['default']['ENGINE'].lower():
            # Para SQLite, verificar se o arquivo existe
            db_file = settings.DATABASES['default']['NAME']
            db_info['file_exists'] = os.path.exists(db_file)
            db_info['file_size'] = os.path.getsize(db_file) if db_info['file_exists'] else 0
            
        elif 'postgresql' in settings.DATABASES['default']['ENGINE'].lower():
            # Para PostgreSQL, obter versão
            with connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                db_info['version'] = version
                
        elif 'mysql' in settings.DATABASES['default']['ENGINE'].lower():
            # Para MySQL, obter versão
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                db_info['version'] = version
        
        return {
            'status': 'success',
            'message': 'Conexão bem-sucedida',
            'details': db_info
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Erro na conexão: {str(e)}',
            'details': {}
        } 