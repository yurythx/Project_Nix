from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from apps.config.mixins import SuperuserRequiredMixin, PermissionHelperMixin
from apps.config.models import EmailConfiguration, DatabaseConfiguration
from apps.config.forms.multi_config_forms import (
    EmailConfigurationForm, 
    DatabaseConfigurationForm, 
    ConfigurationTestForm
)
import logging

logger = logging.getLogger(__name__)


class EmailConfigListView(SuperuserRequiredMixin, PermissionHelperMixin, View):
    """Lista todas as configurações de email"""
    template_name = 'config/email_configs/list.html'
    
    def get(self, request):
        configs = EmailConfiguration.objects.all()
        default_config = EmailConfiguration.get_default()
        
        context = {
            'configs': configs,
            'default_config': default_config,
            'total_configs': configs.count(),
            'active_configs': configs.filter(is_active=True).count(),
        }
        
        return render(request, self.template_name, context)


class EmailConfigCreateView(SuperuserRequiredMixin, PermissionHelperMixin, View):
    """Criar nova configuração de email"""
    template_name = 'config/email_configs/form.html'
    
    def get(self, request):
        form = EmailConfigurationForm()
        return render(request, self.template_name, {
            'form': form,
            'title': 'Nova Configuração de Email',
            'action': 'Criar'
        })
    
    def post(self, request):
        form = EmailConfigurationForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    config = form.save(commit=False)
                    config.created_by = request.user
                    config.updated_by = request.user
                    
                    # Se é a primeira configuração, tornar padrão
                    if not EmailConfiguration.objects.exists():
                        config.is_default = True
                    
                    config.save()
                    
                    messages.success(request, '✅ Configuração criada com sucesso!')
                    
                    return redirect('config:email_configs')
                    
            except Exception as e:
                logger.error(f'Erro ao criar configuração de email: {e}', exc_info=True)
                messages.error(request, '❌ Ocorreu um erro ao criar a configuração. Tente novamente.')
        
        return render(request, self.template_name, {
            'form': form,
            'title': 'Nova Configuração de Email',
            'action': 'Criar'
        })


class EmailConfigUpdateView(SuperuserRequiredMixin, PermissionHelperMixin, View):
    """Editar configuração de email"""
    template_name = 'config/email_configs/form.html'
    
    def get(self, request, pk):
        config = get_object_or_404(EmailConfiguration, pk=pk)
        form = EmailConfigurationForm(instance=config)
        
        return render(request, self.template_name, {
            'form': form,
            'config': config,
            'title': f'Editar {config.name}',
            'action': 'Salvar'
        })
    
    def post(self, request, pk):
        config = get_object_or_404(EmailConfiguration, pk=pk)
        form = EmailConfigurationForm(request.POST, instance=config)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    config = form.save(commit=False)
                    config.updated_by = request.user
                    config.save()
                    
                    messages.success(request, '✅ Configuração atualizada com sucesso!')
                    
                    return redirect('config:email_configs')
                    
            except Exception as e:
                logger.error(f'Erro ao atualizar configuração de email: {e}', exc_info=True)
                messages.error(request, '❌ Ocorreu um erro ao atualizar a configuração. Tente novamente.')
        
        return render(request, self.template_name, {
            'form': form,
            'config': config,
            'title': f'Editar {config.name}',
            'action': 'Salvar'
        })


class EmailConfigDeleteView(SuperuserRequiredMixin, PermissionHelperMixin, View):
    """Deletar configuração de email"""
    
    def post(self, request, pk):
        config = get_object_or_404(EmailConfiguration, pk=pk)
        
        try:
            if config.is_default:
                messages.error(
                    request,
                    '❌ Não é possível deletar a configuração padrão. '
                    'Defina outra como padrão primeiro.'
                )
            else:
                config_name = config.name
                config.delete()
                
                messages.success(request, '🗑️ Configuração removida com sucesso!')
                
        except Exception as e:
            logger.error(f'Erro ao deletar configuração de email: {e}', exc_info=True)
            messages.error(request, '❌ Ocorreu um erro ao remover a configuração. Tente novamente.')
        
        return redirect('config:email_configs')


class EmailConfigTestView(SuperuserRequiredMixin, PermissionHelperMixin, View):
    """Testar configuração de email"""
    template_name = 'config/email_configs/test.html'
    
    def get(self, request, pk):
        config = get_object_or_404(EmailConfiguration, pk=pk)
        form = ConfigurationTestForm(config_type='email')
        
        return render(request, self.template_name, {
            'config': config,
            'form': form,
        })
    
    def post(self, request, pk):
        config = get_object_or_404(EmailConfiguration, pk=pk)
        form = ConfigurationTestForm(request.POST, config_type='email')
        action = request.POST.get('action')
        
        try:
            if action == 'test_connection':
                success, message = config.test_connection()
                
                if success:
                    messages.success(request, f'✅ {message}')
                else:
                    messages.error(request, f'❌ {message}')
                    
            elif action == 'send_test':
                if form.is_valid():
                    test_email = form.cleaned_data.get('test_email') or request.user.email
                    
                    if not test_email:
                        messages.error(request, 'Email de destino é obrigatório.')
                    else:
                        success, message = config.send_test_email(
                            test_email,
                            request.user.get_full_name() or request.user.username
                        )
                        
                        if success:
                            messages.success(request, f'✅ {message}')
                        else:
                            messages.error(request, f'❌ {message}')
                else:
                    messages.error(request, 'Formulário inválido.')
                    
        except Exception as e:
            logger.error(f'Erro ao testar configuração de email: {e}', exc_info=True)
            messages.error(request, f'Erro no teste: {str(e)}')
        
        return render(request, self.template_name, {
            'config': config,
            'form': form,
        })


@method_decorator(csrf_exempt, name='dispatch')
class EmailConfigSetDefaultView(SuperuserRequiredMixin, PermissionHelperMixin, View):
    """Definir configuração como padrão"""
    
    def post(self, request, pk):
        try:
            config = get_object_or_404(EmailConfiguration, pk=pk)
            
            with transaction.atomic():
                # Remover padrão de todas as outras
                EmailConfiguration.objects.filter(is_default=True).update(is_default=False)
                
                # Definir esta como padrão
                config.is_default = True
                config.save(update_fields=['is_default'])
                
                return JsonResponse({
                    'success': True,
                    'message': f'Configuração "{config.name}" definida como padrão!'
                })
                
        except Exception as e:
            logger.error(f'Erro ao definir configuração padrão: {e}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': f'Erro: {str(e)}'
            })


# Views para Banco de Dados (similar às de email)

class DatabaseConfigListView(SuperuserRequiredMixin, PermissionHelperMixin, View):
    """Lista todas as configurações de banco de dados"""
    template_name = 'config/database_configs/list.html'
    
    def get(self, request):
        configs = DatabaseConfiguration.objects.all()
        default_config = DatabaseConfiguration.get_default()
        
        context = {
            'configs': configs,
            'default_config': default_config,
            'total_configs': configs.count(),
            'active_configs': configs.filter(is_active=True).count(),
        }
        
        return render(request, self.template_name, context)


class DatabaseConfigCreateView(SuperuserRequiredMixin, PermissionHelperMixin, View):
    """Criar nova configuração de banco"""
    template_name = 'config/database_configs/form.html'
    
    def get(self, request):
        form = DatabaseConfigurationForm()
        return render(request, self.template_name, {
            'form': form,
            'title': 'Nova Configuração de Banco',
            'action': 'Criar'
        })
    
    def post(self, request):
        form = DatabaseConfigurationForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    config = form.save(commit=False)
                    config.created_by = request.user
                    
                    # Se é a primeira configuração, tornar padrão
                    if not DatabaseConfiguration.objects.exists():
                        config.is_default = True
                    
                    config.save()
                    
                    messages.success(
                        request,
                        f'✅ Configuração "{config.name}" criada com sucesso!'
                    )
                    
                    return redirect('config:database_configs')
                    
            except Exception as e:
                logger.error(f'Erro ao criar configuração de banco: {e}', exc_info=True)
                messages.error(request, f'Erro ao criar configuração: {str(e)}')
        
        return render(request, self.template_name, {
            'form': form,
            'title': 'Nova Configuração de Banco',
            'action': 'Criar'
        })


class DatabaseConfigUpdateView(SuperuserRequiredMixin, PermissionHelperMixin, View):
    """Editar configuração de banco"""
    template_name = 'config/database_configs/form.html'

    def get(self, request, pk):
        config = get_object_or_404(DatabaseConfiguration, pk=pk)
        form = DatabaseConfigurationForm(instance=config)

        return render(request, self.template_name, {
            'form': form,
            'config': config,
            'title': f'Editar {config.name}',
            'action': 'Salvar'
        })

    def post(self, request, pk):
        config = get_object_or_404(DatabaseConfiguration, pk=pk)
        form = DatabaseConfigurationForm(request.POST, instance=config)

        if form.is_valid():
            try:
                with transaction.atomic():
                    config = form.save(commit=False)
                    config.save()

                    messages.success(
                        request,
                        f'✅ Configuração "{config.name}" atualizada com sucesso!'
                    )

                    return redirect('config:database_configs')

            except Exception as e:
                logger.error(f'Erro ao atualizar configuração de banco: {e}', exc_info=True)
                messages.error(request, f'Erro ao atualizar configuração: {str(e)}')

        return render(request, self.template_name, {
            'form': form,
            'config': config,
            'title': f'Editar {config.name}',
            'action': 'Salvar'
        })


class DatabaseConfigDeleteView(SuperuserRequiredMixin, PermissionHelperMixin, View):
    """Deletar configuração de banco"""

    def post(self, request, pk):
        config = get_object_or_404(DatabaseConfiguration, pk=pk)

        try:
            if config.is_default:
                messages.error(
                    request,
                    '❌ Não é possível deletar a configuração padrão. '
                    'Defina outra como padrão primeiro.'
                )
            else:
                config_name = config.name
                config.delete()

                messages.success(
                    request,
                    f'✅ Configuração "{config_name}" deletada com sucesso!'
                )

        except Exception as e:
            logger.error(f'Erro ao deletar configuração de banco: {e}', exc_info=True)
            messages.error(request, f'Erro ao deletar configuração: {str(e)}')

        return redirect('config:database_configs')


@method_decorator(csrf_exempt, name='dispatch')
class DatabaseConfigSetDefaultView(SuperuserRequiredMixin, PermissionHelperMixin, View):
    """Definir configuração de banco como padrão"""

    def post(self, request, pk):
        try:
            config = get_object_or_404(DatabaseConfiguration, pk=pk)

            with transaction.atomic():
                # Remover padrão de todas as outras
                DatabaseConfiguration.objects.filter(is_default=True).update(is_default=False)

                # Definir esta como padrão
                config.is_default = True
                config.save(update_fields=['is_default'])

                return JsonResponse({
                    'success': True,
                    'message': f'Configuração "{config.name}" definida como padrão!'
                })

        except Exception as e:
            logger.error(f'Erro ao definir configuração padrão de banco: {e}', exc_info=True)
            return JsonResponse({
                'success': False,
                'message': f'Erro: {str(e)}'
            })


class DatabaseConfigTestView(SuperuserRequiredMixin, PermissionHelperMixin, View):
    """Testar configuração de banco"""
    template_name = 'config/database_configs/test.html'

    def get(self, request, pk):
        config = get_object_or_404(DatabaseConfiguration, pk=pk)
        form = ConfigurationTestForm(config_type='database')

        return render(request, self.template_name, {
            'config': config,
            'form': form,
        })

    def post(self, request, pk):
        config = get_object_or_404(DatabaseConfiguration, pk=pk)
        action = request.POST.get('action')

        try:
            if action == 'test_connection':
                success, message = config.test_connection()

                if success:
                    messages.success(request, f'✅ {message}')
                else:
                    messages.error(request, f'❌ {message}')

        except Exception as e:
            logger.error(f'Erro ao testar configuração de banco: {e}', exc_info=True)
            messages.error(request, f'Erro no teste: {str(e)}')

        form = ConfigurationTestForm(config_type='database')
        return render(request, self.template_name, {
            'config': config,
            'form': form,
        })
