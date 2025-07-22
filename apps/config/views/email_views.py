"""
Views para gerenciamento de configurações de email.
"""

import json
import os
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import get_connection
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from apps.config.forms.email_forms import SimpleEmailConfigForm
from apps.config.services.email_config_service import DynamicEmailConfigService as EmailConfigService
from apps.config.services.system_config_service import SystemConfigService


@method_decorator(login_required, name='dispatch')
class EmailConfigView(TemplateView):
    template_name = 'config/email/config.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obter configuração atual
        email_service = EmailConfigService()
        email_config = email_service.get_active_config()
        
        # Verificar se está configurado
        email_config = email_service.get_active_config()
        email_configured = bool(
            email_config.get('EMAIL_HOST') and 
            email_config.get('EMAIL_HOST_USER') and
            email_config.get('EMAIL_BACKEND') != 'django.core.mail.backends.dummy.EmailBackend'
        )
        
        # Obter backend atual
        current_backend = getattr(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
        
        # Criar formulário com dados iniciais
        form = SimpleEmailConfigForm(initial=email_config)
        
        context.update({
            'form': form,
            'email_config': email_config,
            'email_configured': email_configured,
            'current_backend': current_backend,
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        email_service = EmailConfigService()
        
        # Garantir que email_backend esteja presente
        post_data = request.POST.copy()
        if 'email_backend' not in post_data:
            post_data['email_backend'] = 'django.core.mail.backends.smtp.EmailBackend'
        
        form = SimpleEmailConfigForm(post_data)
        
        if form.is_valid():
            # Garantir tipos corretos
            def to_bool(val):
                if isinstance(val, bool):
                    return val
                if isinstance(val, str):
                    return val.lower() in ['true', '1', 'on', 'yes']
                return bool(val)
            def to_int(val, default=0):
                try:
                    return int(val)
                except (TypeError, ValueError):
                    return default

            config_dict = {
                'EMAIL_BACKEND': form.cleaned_data.get('email_backend', 'django.core.mail.backends.smtp.EmailBackend'),
                'EMAIL_HOST': form.cleaned_data.get('email_host', ''),
                'EMAIL_PORT': to_int(form.cleaned_data.get('email_port', 587), 587),
                'EMAIL_HOST_USER': form.cleaned_data.get('email_host_user', ''),
                'EMAIL_HOST_PASSWORD': form.cleaned_data.get('email_host_password', ''),
                'EMAIL_USE_TLS': to_bool(form.cleaned_data.get('email_use_tls', True)),
                'EMAIL_USE_SSL': to_bool(form.cleaned_data.get('email_use_ssl', False)),
                'DEFAULT_FROM_EMAIL': form.cleaned_data.get('default_from_email', ''),
                'EMAIL_TIMEOUT': to_int(form.cleaned_data.get('email_timeout', 30), 30),
                'SERVER_EMAIL': form.cleaned_data.get('server_email', ''),
            }
            # Garante que EMAIL_TIMEOUT sempre exista
            if not config_dict['EMAIL_TIMEOUT']:
                config_dict['EMAIL_TIMEOUT'] = 30
            success = email_service.save_config(config_dict, request.user, 'Configuração via formulário')
            if success:
                messages.success(request, 'Configurações de email salvas com sucesso!')
                return redirect('config:email_config')
            else:
                messages.error(request, 'Erro ao salvar configurações.')
        else:
            messages.error(request, 'Erro ao salvar configurações. Verifique os dados.')
        
        return self.get(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class EmailTestView(TemplateView):
    template_name = 'config/email/test.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        email_service = EmailConfigService()
        email_config = email_service.get_active_config()
        email_configured = bool(
            email_config.get('EMAIL_HOST') and 
            email_config.get('EMAIL_HOST_USER') and
            email_config.get('EMAIL_BACKEND') != 'django.core.mail.backends.dummy.EmailBackend'
        )
        
        context.update({
            'email_configured': email_configured,
        })
        
        return context


@login_required
@require_http_methods(["POST"])
def email_sync_view(request):
    """Sincronizar configurações de email do banco para .env"""
    try:
        email_service = EmailConfigService()
        success = email_service.sync_config_to_env()
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Configurações sincronizadas com sucesso para o arquivo .env'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Erro ao sincronizar configurações'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro inesperado: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def email_quick_setup_view(request):
    """Configuração rápida de email"""
    try:
        data = json.loads(request.body)
        backend = data.get('backend')
        
        email_service = EmailConfigService()
        
        if backend == 'console':
            config = {
                'EMAIL_BACKEND': 'django.core.mail.backends.console.EmailBackend',
                'DEFAULT_FROM_EMAIL': 'noreply@localhost'
            }
            success = email_service.save_config(config, request.user, 'Backend Console')
            message = 'Backend console configurado. Emails aparecerão no terminal.'
        elif backend == 'file':
            config = {
                'EMAIL_BACKEND': 'django.core.mail.backends.filebased.EmailBackend',
                'EMAIL_FILE_PATH': '/tmp/django-mails',
                'DEFAULT_FROM_EMAIL': 'noreply@localhost'
            }
            success = email_service.save_config(config, request.user, 'Backend Arquivo')
            message = 'Backend de arquivo configurado. Emails serão salvos em arquivos.'
        elif backend == 'dummy':
            config = {
                'EMAIL_BACKEND': 'django.core.mail.backends.dummy.EmailBackend',
                'DEFAULT_FROM_EMAIL': 'noreply@localhost'
            }
            success = email_service.save_config(config, request.user, 'Email Desabilitado')
            message = 'Email desabilitado. Nenhum email será enviado.'
        elif backend == 'smtp':
            # Configuração SMTP personalizada (ex: Gmail)
            host = data.get('host', 'smtp.gmail.com')
            user = data.get('user')
            password = data.get('password')
            from_email = data.get('from_email')
            tls = data.get('tls', True)
            
            if not all([user, password]):
                return JsonResponse({
                    'success': False,
                    'message': 'Usuário e senha são obrigatórios'
                })
            
            config = {
                'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
                'EMAIL_HOST': host,
                'EMAIL_PORT': 587 if tls else 465,
                'EMAIL_HOST_USER': user,
                'EMAIL_HOST_PASSWORD': password,
                'EMAIL_USE_TLS': tls,
                'EMAIL_USE_SSL': not tls,
                'DEFAULT_FROM_EMAIL': from_email or user
            }
            success = email_service.save_config(config, request.user, f'SMTP {host}')
            message = f'SMTP configurado para {host}. Teste a conexão para verificar.'
        else:
            return JsonResponse({
                'success': False,
                'message': 'Backend inválido'
            })
        
        if success:
            return JsonResponse({
                'success': True,
                'message': message
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Erro ao configurar backend'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro inesperado: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def test_email_connection_view(request):
    """Testar conexão de email"""
    try:
        email_service = EmailConfigService()
        
        email_config = email_service.get_active_config()
        if not email_config or not email_config.get('EMAIL_HOST'):
            return JsonResponse({
                'success': False,
                'message': 'Email não está configurado'
            })
        
        # Testar conexão
        success, message = email_service.test_connection()
        
        return JsonResponse({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro inesperado: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def email_detailed_status_view(request):
    """Status detalhado do sistema de email"""
    try:
        from django.template.loader import render_to_string
        
        email_service = EmailConfigService()
        
        # Coletar informações detalhadas
        email_config = email_service.get_active_config()
        email_configured = bool(
            email_config.get('EMAIL_HOST') and 
            email_config.get('EMAIL_HOST_USER') and
            email_config.get('EMAIL_BACKEND') != 'django.core.mail.backends.dummy.EmailBackend'
        )
        
        status_info = {
            'email_configured': email_configured,
            'current_backend': getattr(settings, 'EMAIL_BACKEND', 'Não configurado'),
            'email_config': email_config,
            'env_file_exists': os.path.exists('.env'),
            'settings_loaded': hasattr(settings, 'EMAIL_HOST'),
            'database_connection': True,  # Simplificado
            'system_info': {},  # Simplificado
        }
        
        # Renderizar HTML do status
        html = render_to_string('config/email/detailed_status.html', status_info)
        
        return JsonResponse({
            'success': True,
            'html': html
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao carregar status: {str(e)}'
        })


@login_required
def email_stats_view(request):
    """Estatísticas de email"""
    return render(request, 'config/email/stats.html')


@login_required
def email_templates_view(request):
    """Gerenciamento de templates de email"""
    return render(request, 'config/email/templates.html')
