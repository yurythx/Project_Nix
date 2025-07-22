from django.shortcuts import render
from django.views import View
from django.conf import settings
from django.db import connection
import platform
import psutil
from datetime import datetime
from apps.config.mixins import ConfigPermissionMixin, PermissionHelperMixin
from apps.config.models.user_activity_log import UserActivityLog
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
import csv
from django.http import HttpResponse


class SystemConfigView(ConfigPermissionMixin, PermissionHelperMixin, View):
    """View principal para configurações do sistema"""
    template_name = 'config/system_config.html'

    def get(self, request):
        """Exibe página de configurações do sistema"""
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def get_context_data(self):
        """Prepara dados do contexto"""
        # Informações do sistema
        system_info = self.get_system_info()

        # Informações do Django
        django_info = self.get_django_info()

        # Informações do banco de dados
        database_info = self.get_database_info()

        # Estatísticas
        stats = self.get_system_stats()

        return {
            'system_info': system_info,
            'django_info': django_info,
            'database_info': database_info,
            'stats': stats,
        }

    def get_system_info(self):
        """Obtém informações do sistema operacional"""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'architecture': platform.architecture()[0],
                'processor': platform.processor() or 'N/A',
                'hostname': platform.node(),
                'cpu_count': psutil.cpu_count(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_total': self.format_bytes(memory.total),
                'memory_used': self.format_bytes(memory.used),
                'memory_percent': memory.percent,
                'disk_total': self.format_bytes(disk.total),
                'disk_used': self.format_bytes(disk.used),
                'disk_percent': (disk.used / disk.total) * 100,
                'uptime': datetime.now() - datetime.fromtimestamp(psutil.boot_time()),
            }
        except Exception as e:
            return {'error': str(e)}

    def get_django_info(self):
        """Obtém informações do Django"""
        return {
            'version': getattr(settings, 'DJANGO_VERSION', 'N/A'),
            'debug': settings.DEBUG,
            'secret_key_set': bool(getattr(settings, 'SECRET_KEY', None)),
            'allowed_hosts': settings.ALLOWED_HOSTS,
            'installed_apps_count': len(settings.INSTALLED_APPS),
            'middleware_count': len(settings.MIDDLEWARE),
            'time_zone': settings.TIME_ZONE,
            'language_code': settings.LANGUAGE_CODE,
            'use_i18n': settings.USE_I18N,
            'use_l10n': getattr(settings, 'USE_L10N', False),
            'use_tz': settings.USE_TZ,
            'static_url': settings.STATIC_URL,
            'media_url': getattr(settings, 'MEDIA_URL', 'N/A'),
        }

    def get_database_info(self):
        """Obtém informações do banco de dados"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                db_version = cursor.fetchone()[0] if cursor.rowcount > 0 else 'N/A'
                
                # Estatísticas das tabelas
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        n_tup_ins as inserts,
                        n_tup_upd as updates,
                        n_tup_del as deletes
                    FROM pg_stat_user_tables 
                    ORDER BY n_tup_ins + n_tup_upd + n_tup_del DESC 
                    LIMIT 10
                """)
                table_stats = cursor.fetchall()
                
            return {
                'engine': connection.vendor,
                'version': db_version,
                'name': connection.settings_dict['NAME'],
                'host': connection.settings_dict.get('HOST', 'localhost'),
                'port': connection.settings_dict.get('PORT', 'default'),
                'table_stats': table_stats,
            }
        except Exception as e:
            return {
                'engine': connection.vendor,
                'error': str(e)
            }

# Método categorize_configs removido - não mais necessário

    def get_system_stats(self):
        """Obtém estatísticas do sistema"""
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group

        User = get_user_model()

        stats = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'staff_users': User.objects.filter(is_staff=True).count(),
            'superusers': User.objects.filter(is_superuser=True).count(),
            'total_groups': Group.objects.count(),
        }

        # Configurações avançadas disponíveis
        stats['advanced_configs'] = 3  # Banco, Email, Variáveis

        # Logs de atividade (pode não existir ainda)
        try:
            stats['total_logs'] = UserActivityLog.objects.count()
            stats['recent_logs'] = UserActivityLog.objects.filter(
                created_at__gte=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count()
        except:
            stats['total_logs'] = 0
            stats['recent_logs'] = 0

        return stats

    def format_bytes(self, bytes_value):
        """Formata bytes em unidades legíveis"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"


# Views do CRUD de configurações removidas - mantendo apenas configurações avançadas específicas

class SystemLogListView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'config/system_logs.html'
    paginate_by = 25

    def test_func(self):
        return self.request.user.is_staff

    def get(self, request):
        logs = UserActivityLog.objects.select_related('user', 'target_user').order_by('-created_at')
        # Filtros
        user_email = request.GET.get('user')
        action = request.GET.get('action')
        date = request.GET.get('date')
        if user_email:
            logs = logs.filter(user__email__icontains=user_email)
        if action:
            logs = logs.filter(action=action)
        if date:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                logs = logs.filter(created_at__date=date_obj.date())
            except Exception:
                pass
        # Exportação CSV
        if request.GET.get('export') == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="logs.csv"'
            writer = csv.writer(response)
            writer.writerow(['Data/Hora', 'Usuário', 'Ação', 'Alvo', 'Descrição', 'IP'])
            for log in logs:
                writer.writerow([
                    log.created_at.strftime('%d/%m/%Y %H:%M:%S'),
                    log.user.email,
                    log.get_action_display(),
                    log.target_user.email if log.target_user else '-',
                    log.description,
                    log.ip_address or '-',
                ])
            return response
        paginator = Paginator(logs, self.paginate_by)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        # Opções de filtro
        actions = UserActivityLog.ACTION_CHOICES
        users = UserActivityLog.objects.values_list('user__email', flat=True).distinct()
        context = {
            'logs': page_obj.object_list,
            'page_obj': page_obj,
            'filter_user': user_email or '',
            'filter_action': action or '',
            'filter_date': date or '',
            'actions': actions,
            'users': users,
        }
        return render(request, self.template_name, context)
