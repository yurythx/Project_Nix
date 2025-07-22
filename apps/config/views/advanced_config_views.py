from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from apps.config.forms.advanced_config_forms import (
    EnvironmentVariablesForm
)

from apps.config.mixins import SuperuserRequiredMixin, PermissionHelperMixin





class EnvironmentVariablesView(SuperuserRequiredMixin, PermissionHelperMixin, View):
    """View para configurações de variáveis de ambiente - Apenas superusuários"""
    template_name = 'config/environment_variables.html'

    def get(self, request):
        """Exibe formulário de variáveis de ambiente"""
        form = EnvironmentVariablesForm()

        # Informações adicionais para o template
        context = {
            'form': form,
            'env_file_exists': self._env_file_exists(),
            'env_file_path': self._get_env_file_path(),
            'backup_files': self._get_backup_files(),
        }

        return render(request, self.template_name, context)

    def post(self, request):
        """Processa variáveis de ambiente"""
        form = EnvironmentVariablesForm(request.POST)

        if 'backup' in request.POST:
            # Cria backup do arquivo atual
            success, message = form.create_backup()
            if success:
                messages.success(request, f'🗄️ Backup criado com sucesso: {message}')
            else:
                messages.error(request, f'❌ Erro ao criar backup: {message}')

        elif form.is_valid():
            try:
                success = form.save(user=request.user)

                if success:
                    messages.success(request, '✅ Arquivo .env salvo com sucesso!')
                    messages.warning(request, '⚠️ IMPORTANTE: Reinicie o servidor para aplicar as alterações.')
                    return redirect('config:environment_variables')
                else:
                    messages.error(request, '❌ Erro ao salvar arquivo .env.')

            except Exception as e:
                messages.error(request, f'❌ Erro ao salvar arquivo: {str(e)}')

        # Recarrega informações para o template
        context = {
            'form': form,
            'env_file_exists': self._env_file_exists(),
            'env_file_path': self._get_env_file_path(),
            'backup_files': self._get_backup_files(),
        }

        return render(request, self.template_name, context)

    def _env_file_exists(self):
        """Verifica se o arquivo .env existe"""
        try:
            from pathlib import Path
            from django.conf import settings
            env_path = Path(settings.BASE_DIR) / '.env'
            return env_path.exists()
        except:
            return False

    def _get_env_file_path(self):
        """Retorna o caminho do arquivo .env"""
        try:
            from pathlib import Path
            from django.conf import settings
            env_path = Path(settings.BASE_DIR) / '.env'
            return str(env_path)
        except:
            return "Não encontrado"

    def _get_backup_files(self):
        """Lista arquivos de backup do .env"""
        try:
            from pathlib import Path
            from django.conf import settings

            base_dir = Path(settings.BASE_DIR)
            backup_files = []

            for file in base_dir.glob('.env.backup.*'):
                stat = file.stat()
                backup_files.append({
                    'name': file.name,
                    'size': stat.st_size,
                    'modified': stat.st_mtime,
                })

            # Ordena por data de modificação (mais recente primeiro)
            backup_files.sort(key=lambda x: x['modified'], reverse=True)
            return backup_files[:10]  # Máximo 10 backups

        except:
            return []









