from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.views import View
from django.db import connection
from django.conf import settings
from apps.config.services.system_config_service import AuditLogService
from apps.config.repositories.config_repository import DjangoAuditLogRepository
from apps.config.mixins import ConfigPermissionMixin, PermissionHelperMixin
from apps.config.models.app_module_config import AppModuleConfiguration
import psutil
import platform
import sys
import os
import django
from datetime import datetime, timedelta
from django.contrib import messages
from django.urls import reverse

User = get_user_model()

class ConfigDashboardView(ConfigPermissionMixin, PermissionHelperMixin, View):
    """Dashboard principal do módulo de configuração com métricas do sistema"""
    template_name = 'config/dashboard.html'

    def get_system_metrics(self):
        """Coleta métricas do sistema"""
        try:
            # Métricas de CPU e Memória
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Informações do sistema
            system_info = {
                'platform': platform.system(),
                'platform_version': platform.release(),
                'python_version': sys.version.split()[0],
                'django_version': getattr(settings, 'DJANGO_VERSION', 'Unknown'),
            }

            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used': round(memory.used / (1024**3), 2),  # GB
                'memory_total': round(memory.total / (1024**3), 2),  # GB
                'disk_percent': disk.percent,
                'disk_used': round(disk.used / (1024**3), 2),  # GB
                'disk_total': round(disk.total / (1024**3), 2),  # GB
                'system_info': system_info,
            }
        except Exception:
            return None

    def get_database_metrics(self):
        """Coleta métricas do banco de dados"""
        try:
            with connection.cursor() as cursor:
                # Informações básicas do banco
                db_info = {
                    'engine': connection.vendor,
                    'name': connection.settings_dict.get('NAME', 'Unknown'),
                }

                # Contagem de tabelas (específico para cada banco)
                if connection.vendor == 'sqlite':
                    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                    table_count = cursor.fetchone()[0]

                    # Tamanho do banco SQLite
                    db_path = connection.settings_dict.get('NAME')
                    if db_path and os.path.exists(db_path):
                        db_size = round(os.path.getsize(db_path) / (1024**2), 2)  # MB
                    else:
                        db_size = 0

                elif connection.vendor == 'postgresql':
                    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
                    table_count = cursor.fetchone()[0]

                    cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
                    db_size = cursor.fetchone()[0]

                else:
                    table_count = 0
                    db_size = 'Unknown'

                return {
                    'engine': db_info['engine'],
                    'name': db_info['name'],
                    'table_count': table_count,
                    'size': db_size,
                }
        except Exception:
            return None

    def get_email_config_status(self):
        """Verifica status da configuração de email"""
        try:
            email_host = getattr(settings, 'EMAIL_HOST', '')
            email_port = getattr(settings, 'EMAIL_PORT', 587)
            email_use_tls = getattr(settings, 'EMAIL_USE_TLS', False)
            email_use_ssl = getattr(settings, 'EMAIL_USE_SSL', False)
            default_from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '')

            return {
                'email_host': email_host,
                'email_port': email_port,
                'email_use_tls': email_use_tls,
                'email_use_ssl': email_use_ssl,
                'default_from_email': default_from_email,
                'email_configured': bool(email_host and default_from_email),
            }
        except Exception:
            return {
                'email_configured': False,
                'email_host': 'Erro na configuração',
                'email_port': 'N/A',
                'email_use_tls': False,
                'email_use_ssl': False,
                'default_from_email': 'Não configurado',
            }

    def get_articles_count(self):
        """Conta artigos se o app estiver disponível"""
        try:
            from apps.articles.models import Article
            return Article.objects.count()
        except ImportError:
            return 0

    def get_active_modules_count(self):
        """Conta módulos ativos"""
        try:
            return AppModuleConfiguration.objects.filter(is_enabled=True).count()
        except Exception:
            return 0

    def get_emails_sent_count(self):
        """Conta emails enviados (implementação básica)"""
        try:
            # Aqui você pode implementar a contagem real de emails enviados
            # Por enquanto, retornamos 0
            return 0
        except Exception:
            return 0

    def get_recent_modules(self):
        """Obtém módulos recentes para exibição"""
        try:
            return AppModuleConfiguration.objects.all()[:5]
        except Exception:
            return []

    def get(self, request):
        """Exibe o dashboard com métricas do sistema"""
        # Estatísticas de usuários
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        staff_users = User.objects.filter(is_staff=True).count()
        superusers = User.objects.filter(is_superuser=True).count()
        total_groups = Group.objects.count()

        # Usuários recentes (últimos 7 dias)
        week_ago = datetime.now() - timedelta(days=7)
        recent_users = User.objects.filter(date_joined__gte=week_ago).count()

        # Métricas do sistema
        system_metrics = self.get_system_metrics()
        database_metrics = self.get_database_metrics()
        email_config = self.get_email_config_status()

        # Contagem de artigos
        total_articles = self.get_articles_count()
        active_modules = self.get_active_modules_count()
        emails_sent = self.get_emails_sent_count()
        recent_modules = self.get_recent_modules()

        # Organizar estatísticas como o template espera
        stats = {
            'total_users': total_users,
            'active_users': active_users,
            'staff_users': staff_users,
            'superusers': superusers,
            'total_groups': total_groups,
            'recent_users': recent_users,
            'total_articles': total_articles,
            'active_modules': active_modules,
            'emails_sent': emails_sent,
        }

        # Informações do sistema como o template espera
        system_info = {
            'os': system_metrics['system_info']['platform'] if system_metrics and system_metrics.get('system_info') else 'Desconhecido',
            'python_version': system_metrics['system_info']['python_version'] if system_metrics and system_metrics.get('system_info') else 'Desconhecida',
            'database': database_metrics['engine'] if database_metrics else 'Desconhecido',
        }

        # Blocos de status para includes
        status_system_items = [
            {'label': 'Versão Django', 'value': django.get_version()},
            {'label': 'Banco de Dados', 'value': database_metrics['engine'] if database_metrics else 'N/A'},
            {'label': 'Debug Mode', 'value': 'Ativo' if settings.DEBUG else 'Inativo', 'badge_class': 'bg-warning' if settings.DEBUG else 'bg-success'},
            {'label': 'Cache', 'value': 'Funcionando' if system_metrics.get('cache_status', True) else 'Inativo', 'badge_class': 'bg-success' if system_metrics.get('cache_status', True) else 'bg-danger'},
        ]
        status_email_items = [
            {'label': 'Servidor SMTP', 'value': email_config.get('email_host', 'Não configurado')},
            {'label': 'Porta', 'value': email_config.get('email_port', 'N/A')},
            {'label': 'TLS/SSL', 'value': 'TLS Ativo' if email_config.get('email_use_tls') else 'Inativo', 'badge_class': 'bg-success' if email_config.get('email_use_tls') else 'bg-secondary'},
            {'label': 'Status', 'value': 'Configurado' if email_config.get('email_configured') else 'Pendente', 'badge_class': 'bg-success' if email_config.get('email_configured') else 'bg-warning'},
        ]

        context = {
            # Estatísticas organizadas como o template espera
            'stats': stats,
            'system_info': system_info,
            'email_config': email_config.get('email_configured', False),
            'recent_modules': recent_modules,

            # Métricas do sistema (mantidas para compatibilidade)
            'system_metrics': system_metrics,
            'database_metrics': database_metrics,
            'django_version': django.get_version(),
            'debug_mode': settings.DEBUG,
            'cache_status': system_metrics.get('cache_status', True) if system_metrics else True,

            # Configuração de email (mantida para compatibilidade)
            **email_config,
            'status_system_items': status_system_items,
            'status_email_items': status_email_items,
            'quick_user_create_url': reverse('config:user_create'),
            'quick_user_list_url': reverse('config:user_list'),
            'quick_module_list_url': reverse('config:module_list'),
            'quick_system_logs_url': reverse('config:system_logs'),
        }

        return render(request, self.template_name, context)
