import os
import tempfile
import zipfile
import tarfile
import shutil
import logging
from pathlib import Path
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from ..services.backup_service import BackupService
from ..interfaces.services import IBackupService
from ..mixins import BackupViewMixin

logger = logging.getLogger(__name__)

class BackupViewMixin:
    """Mixin para views de backup que implementa injeção de dependência"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backup_service: IBackupService = BackupService()
    
    def get_backup_service(self) -> IBackupService:
        """Retorna o serviço de backup (permite injeção de dependência)"""
        return self.backup_service
    
    def handle_backup_error(self, request, error_message: str, redirect_url: str):
        """Trata erros de backup de forma consistente"""
        messages.error(request, error_message)
        logger.error(f"Erro de backup para usuário {request.user.username}: {error_message}")
        return redirect(redirect_url)
    
    def handle_backup_success(self, request, success_message: str, redirect_url: str):
        """Trata sucessos de backup de forma consistente"""
        messages.success(request, success_message)
        logger.info(f"Backup bem-sucedido para usuário {request.user.username}: {success_message}")
        return redirect(redirect_url)

@method_decorator(staff_member_required, name='dispatch')
class BackupDatabaseView(BackupViewMixin, View):
    """View para gerenciar backups de banco de dados"""
    
    def get(self, request):
        """Exibe lista de backups de banco de dados"""
        try:
            backup_service = self.get_backup_service()
            backups = backup_service.list_backups('database')
            
            # Formatar dados para o template
            formatted_backups = []
            for backup in backups:
                formatted_backups.append({
                    'name': backup['name'],
                    'size': backup['size'],
                    'modified': backup['modified'],
                    'sha256': backup.get('sha256'),
                    'path': backup['path']
                })
            
            return render(request, 'config/backup_database.html', {
                'backups': formatted_backups
            })
            
        except Exception as e:
            return self.handle_backup_error(
                request, 
                f'Erro ao listar backups: {str(e)}',
                reverse('config:dashboard')
            )
    def post(self, request):
        """Cria um novo backup de banco de dados"""
        try:
            backup_service = self.get_backup_service()
            success, message, backup_path = backup_service.create_database_backup(request.user)
            
            if success:
                # Retorna o arquivo de backup para download
                backup_filename = Path(backup_path).name
                
                response = FileResponse(
                    open(backup_path, 'rb'),
                    as_attachment=True,
                    filename=backup_filename
                )
                
                return self.handle_backup_success(
                    request,
                    message,
                    response
                )
            else:
                return self.handle_backup_error(
                    request,
                    message,
                    reverse('config:backup_database')
                )
                
        except Exception as e:
            return self.handle_backup_error(
                request,
                f'Erro inesperado ao gerar backup: {str(e)}',
                reverse('config:backup_database')
            )

@method_decorator(staff_member_required, name='dispatch')
class BackupMediaView(BackupViewMixin, View):
    """View para gerenciar backups de mídia"""
    
    def get(self, request):
        """Exibe lista de backups de mídia"""
        try:
            backup_service = self.get_backup_service()
            backups = backup_service.list_backups('media')
            
            # Formatar dados para o template
            formatted_backups = []
            for backup in backups:
                formatted_backups.append({
                    'name': backup['name'],
                    'size': backup['size'],
                    'modified': backup['modified'],
                    'path': backup['path']
                })
            
            return render(request, 'config/backup_media.html', {
                'backups': formatted_backups
            })
            
        except Exception as e:
            return self.handle_backup_error(
                request,
                f'Erro ao listar backups de mídia: {str(e)}',
                reverse('config:dashboard')
            )
    
    def post(self, request):
        """Cria um novo backup de mídia"""
        try:
            backup_service = self.get_backup_service()
            success, message, backup_path = backup_service.create_media_backup(request.user)
            
            if success:
                # Retorna o arquivo de backup para download
                backup_filename = Path(backup_path).name
                
                response = FileResponse(
                    open(backup_path, 'rb'),
                    as_attachment=True,
                    filename=backup_filename
                )
                
                return self.handle_backup_success(
                    request,
                    message,
                    response
                )
            else:
                return self.handle_backup_error(
                    request,
                    message,
                    reverse('config:backup_media')
                )
                
        except Exception as e:
            return self.handle_backup_error(
                request,
                f'Erro inesperado ao gerar backup de mídia: {str(e)}',
                reverse('config:backup_media')
            )

@method_decorator(staff_member_required, name='dispatch')
class DeleteBackupView(BackupViewMixin, View):
    """View para excluir backups"""
    
    def post(self, request, backup_type, filename):
        """Exclui um backup específico"""
        try:
            backup_service = self.get_backup_service()
            
            # Primeiro, obter o caminho completo do arquivo
            file_success, file_message, backup_file_path = backup_service.get_backup_file(
                backup_type, filename, request.user
            )
            
            if not file_success:
                messages.error(request, f'Erro ao localizar backup: {file_message}')
                return redirect('config:dashboard')
            
            # Agora excluir usando o caminho completo
            success, message = backup_service.delete_backup(str(backup_file_path), request.user)
            
            if success:
                messages.success(request, f'Backup {filename} excluído com sucesso!')
                
                # Redireciona para a página apropriada
                if backup_type == 'database':
                    return redirect('config:backup_database')
                else:
                    return redirect('config:backup_media')
            else:
                messages.error(request, f'Erro ao excluir backup: {message}')
                return redirect('config:dashboard')
                
        except Exception as e:
            messages.error(request, f'Erro inesperado ao excluir backup: {str(e)}')
            return redirect('config:dashboard')

@method_decorator(staff_member_required, name='dispatch')
class RestoreDatabaseView(BackupViewMixin, View):
    """View para restaurar backup de banco de dados"""
    
    def get(self, request):
        """Exibe formulário de restauração"""
        return render(request, 'config/restore_database_form.html')
    
    def post(self, request):
        """Processa restauração de backup de banco de dados"""
        if not request.FILES.get('backup_file'):
            messages.error(request, 'Nenhum arquivo de backup foi enviado.')
            return render(request, 'config/restore_database_form.html')
        
        backup_file = request.FILES['backup_file']
        
        try:
            backup_service = self.get_backup_service()
            restore_result = backup_service.restore_database_backup(backup_file)
            
            if restore_result['success']:
                messages.success(request, 'Restauração do banco de dados concluída com sucesso!')
                
                # Informar sobre backup pré-restauração se criado
                if restore_result.get('pre_restore_backup'):
                    messages.info(
                        request, 
                        f'Backup automático pré-restauração salvo: {restore_result["pre_restore_backup"]}'
                    )
                
                return self.handle_backup_success(
                    request,
                    'Restauração concluída com sucesso!',
                    redirect('config:dashboard')
                )
            else:
                return self.handle_backup_error(
                    request,
                    f'Erro ao restaurar backup: {restore_result["error"]}',
                    reverse('config:restore_database')
                )
                
        except Exception as e:
            return self.handle_backup_error(
                request,
                f'Erro inesperado ao restaurar backup: {str(e)}',
                reverse('config:restore_database')
            )

@method_decorator(staff_member_required, name='dispatch')
class RestoreMediaView(BackupViewMixin, View):
    """View para restaurar backup de mídia"""
    
    def get(self, request):
        """Exibe formulário de restauração de mídia"""
        return render(request, 'config/restore_media_form.html')
    
    def post(self, request):
        """Processa restauração de backup de mídia"""
        if not request.FILES.get('media_file'):
            messages.error(request, 'Nenhum arquivo de mídia foi enviado.')
            return render(request, 'config/restore_media_form.html')
        
        media_file = request.FILES['media_file']
        
        try:
            backup_service = self.get_backup_service()
            restore_result = backup_service.restore_media_backup(media_file)
            
            if restore_result['success']:
                messages.success(request, 'Restauração de mídia concluída com sucesso!')
                
                # Informar sobre backup pré-restauração se criado
                if restore_result.get('pre_restore_backup'):
                    messages.info(
                        request, 
                        f'Backup automático pré-restauração salvo: {restore_result["pre_restore_backup"]}'
                    )
                
                return self.handle_backup_success(
                    request,
                    'Restauração de mídia concluída com sucesso!',
                    redirect('config:dashboard')
                )
            else:
                return self.handle_backup_error(
                    request,
                    f'Erro ao restaurar mídia: {restore_result["error"]}',
                    reverse('config:restore_media')
                )
                
        except Exception as e:
            return self.handle_backup_error(
                request,
                f'Erro inesperado ao restaurar mídia: {str(e)}',
                reverse('config:restore_media')
            )

@staff_member_required
def download_backup(request, backup_type, filename):
    """Função para download de backups usando BackupService"""
    logger.info(f"[DOWNLOAD BACKUP] {backup_type}/{filename} solicitado por {request.user.username}")
    
    try:
        # Usar BackupService para validar e obter o arquivo
        backup_service = BackupService()
        success, message, file_path = backup_service.get_backup_file(backup_type, filename, request.user)
        
        if success and file_path:
            return FileResponse(
                open(file_path, 'rb'), 
                as_attachment=True, 
                filename=filename
            )
        else:
            logger.error(f"[DOWNLOAD BACKUP] Erro: {message} para {backup_type}/{filename}")
            raise Http404(message)
            
    except Exception as e:
        logger.error(f"[DOWNLOAD BACKUP] Erro inesperado: {str(e)} para {backup_type}/{filename}")
        raise Http404('Erro ao acessar arquivo de backup.')