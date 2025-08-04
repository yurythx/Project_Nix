from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q
import os
import mimetypes

from ..models import BackupMetadata
from apps.config.forms.backup_forms import (
    BackupCreateForm, BackupUpdateForm, BackupRestoreForm, BackupDeleteForm
)
from ..services.backup_service import BackupService
from ..mixins import BackupViewMixin

class BackupListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """View para listagem de backups com filtros e paginação"""
    model = BackupMetadata
    template_name = 'config/backup_list.html'
    context_object_name = 'backups'
    paginate_by = 20
    permission_required = 'config.view_backupmetadata'
    
    def get_queryset(self):
        queryset = BackupMetadata.objects.all()
        
        # Filtros
        backup_type = self.request.GET.get('type')
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')
        
        if backup_type:
            queryset = queryset.filter(backup_type=backup_type)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['backup_types'] = BackupMetadata.BACKUP_TYPES
        context['backup_status'] = BackupMetadata.BACKUP_STATUS
        context['current_filters'] = {
            'type': self.request.GET.get('type', ''),
            'status': self.request.GET.get('status', ''),
            'search': self.request.GET.get('search', ''),
        }
        return context

class BackupDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """View para detalhes de um backup específico"""
    model = BackupMetadata
    template_name = 'config/backup_detail.html'
    context_object_name = 'backup'
    permission_required = 'config.view_backupmetadata'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        backup = self.get_object()
        
        # Verificar se o arquivo físico existe
        context['file_exists'] = os.path.exists(backup.file_path)
        
        # Informações adicionais
        if context['file_exists']:
            context['file_size_mb'] = round(backup.file_size / (1024 * 1024), 2)
        
        return context

class BackupCreateView(LoginRequiredMixin, PermissionRequiredMixin, BackupViewMixin, CreateView):
    """View para criação de novos backups"""
    model = BackupMetadata
    form_class = BackupCreateForm
    template_name = 'config/backup_create.html'
    permission_required = 'config.add_backupmetadata'
    
    def get_initial(self):
        initial = super().get_initial()
        backup_type = self.kwargs.get('backup_type')
        if backup_type:
            initial['backup_type'] = backup_type
        return initial
    
    def form_valid(self, form):
        # Não criar backup_metadata aqui, pois o serviço já cria
        backup_type = form.cleaned_data['backup_type']
        description = form.cleaned_data.get('description', '')
        
        try:
            # Criar o backup usando o serviço
            backup_service = self.get_backup_service()
            
            if backup_type == 'database':
                success, message, file_path = backup_service.create_database_backup(self.request.user, description)
            elif backup_type == 'media':
                success, message, file_path = backup_service.create_media_backup(self.request.user)
            elif backup_type == 'configuration':
                success, message, file_path = backup_service.create_configuration_backup(self.request.user)
            else:
                raise ValueError(f"Tipo de backup não suportado: {backup_type}")
            
            if not success:
                raise Exception(message)
            
            if not file_path:
                raise Exception("Caminho do arquivo de backup não foi retornado")
            
            # Buscar o backup criado pelo serviço
            backup_metadata = BackupMetadata.objects.filter(
                file_path=file_path,
                backup_type=backup_type
            ).order_by('-created_at').first()
            
            if not backup_metadata:
                raise Exception("Backup criado mas registro não encontrado")
            
            # Definir o objeto para redirecionamento
            self.object = backup_metadata
            
            messages.success(self.request, f'Backup {backup_metadata.name} criado com sucesso!')
            return redirect(self.get_success_url())
            
        except Exception as e:
            messages.error(self.request, f'Erro ao criar backup: {str(e)}')
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse('config:backup_detail', kwargs={'slug': self.object.slug})

class BackupUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """View para atualização de metadados de backup"""
    model = BackupMetadata
    form_class = BackupUpdateForm
    template_name = 'config/backup_update.html'
    permission_required = 'config.change_backupmetadata'
    
    def get_success_url(self):
        return reverse('config:backup_detail', kwargs={'slug': self.object.slug})
    
    def form_valid(self, form):
        messages.success(self.request, 'Metadados do backup atualizados com sucesso!')
        return super().form_valid(form)

class BackupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, BackupViewMixin, DeleteView):
    """View para exclusão de backups"""
    model = BackupMetadata
    template_name = 'config/backup_delete.html'
    success_url = reverse_lazy('config:backup_list')
    permission_required = 'config.delete_backupmetadata'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = BackupDeleteForm()
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = BackupDeleteForm(request.POST)
        
        if form.is_valid():
            delete_file = form.cleaned_data.get('delete_file', True)
            
            try:
                # Excluir arquivo físico se solicitado
                if delete_file and os.path.exists(self.object.file_path):
                    os.remove(self.object.file_path)
                
                # Excluir registro do banco
                backup_name = self.object.name
                self.object.delete()
                
                messages.success(request, f'Backup "{backup_name}" excluído com sucesso!')
                return self.get_success_response()
                
            except Exception as e:
                messages.error(request, f'Erro ao excluir backup: {str(e)}')
                return self.form_invalid(form)
        
        return self.form_invalid(form)
    
    def get_success_response(self):
        return redirect(self.success_url)

class BackupDownloadView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """View para download de arquivos de backup"""
    model = BackupMetadata
    permission_required = 'config.view_backupmetadata'
    
    def get(self, request, *args, **kwargs):
        backup = self.get_object()
        
        if not os.path.exists(backup.file_path):
            raise Http404("Arquivo de backup não encontrado")
        
        # Verificar integridade do arquivo
        backup_service = BackupService()
        integrity_result = backup_service.verify_backup_integrity(backup.file_path)
        
        if not integrity_result['valid']:
            error_msg = integrity_result.get('error', 'Arquivo de backup corrompido!')
            messages.error(request, error_msg)
            return redirect('config:backup_detail', slug=backup.slug)
        
        # Preparar resposta para download
        with open(backup.file_path, 'rb') as file:
            response = HttpResponse(file.read())
            
        content_type, _ = mimetypes.guess_type(backup.file_path)
        if content_type:
            response['Content-Type'] = content_type
        else:
            response['Content-Type'] = 'application/octet-stream'
        
        filename = os.path.basename(backup.file_path)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = backup.file_size
        
        return response

class BackupRestoreOptionsView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """View para opções de restauração por tipo de backup"""
    template_name = 'config/backup_restore_options.html'
    permission_required = 'config.view_backupmetadata'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Contar backups por tipo
        backup_counts = {
            'database': BackupMetadata.objects.filter(
                backup_type='database', 
                status='completed'
            ).count(),
            'media': BackupMetadata.objects.filter(
                backup_type='media', 
                status='completed'
            ).count(),
            'configuration': BackupMetadata.objects.filter(
                backup_type='configuration', 
                status='completed'
            ).count(),
        }
        
        # Últimos backups por tipo
        latest_backups = {
            'database': BackupMetadata.objects.filter(
                backup_type='database', 
                status='completed'
            ).order_by('-created_at').first(),
            'media': BackupMetadata.objects.filter(
                backup_type='media', 
                status='completed'
            ).order_by('-created_at').first(),
            'configuration': BackupMetadata.objects.filter(
                backup_type='configuration', 
                status='completed'
            ).order_by('-created_at').first(),
        }
        
        context['backup_counts'] = backup_counts
        context['latest_backups'] = latest_backups
        context['total_backups'] = sum(backup_counts.values())
        
        return context
    
    def get_success_url(self):
        return reverse('config:backup_detail', kwargs={'slug': self.object.slug})
    
    def form_valid(self, form):
        messages.success(self.request, 'Metadados do backup atualizados com sucesso!')
        return super().form_valid(form)

class BackupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, BackupViewMixin, DeleteView):
    """View para exclusão de backups"""
    model = BackupMetadata
    template_name = 'config/backup_delete.html'
    success_url = reverse_lazy('config:backup_list')
    permission_required = 'config.delete_backupmetadata'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = BackupDeleteForm()
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = BackupDeleteForm(request.POST)
        
        if form.is_valid():
            delete_file = form.cleaned_data.get('delete_file', True)
            
            try:
                # Excluir arquivo físico se solicitado
                if delete_file and os.path.exists(self.object.file_path):
                    os.remove(self.object.file_path)
                
                # Excluir registro do banco
                backup_name = self.object.name
                self.object.delete()
                
                messages.success(request, f'Backup "{backup_name}" excluído com sucesso!')
                return self.get_success_response()
                
            except Exception as e:
                messages.error(request, f'Erro ao excluir backup: {str(e)}')
                return self.form_invalid(form)
        
        return self.form_invalid(form)
    
    def get_success_response(self):
        return redirect(self.success_url)

class BackupDownloadView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """View para download de arquivos de backup"""
    model = BackupMetadata
    permission_required = 'config.view_backupmetadata'
    
    def get(self, request, *args, **kwargs):
        backup = self.get_object()
        
        if not os.path.exists(backup.file_path):
            raise Http404("Arquivo de backup não encontrado")
        
        # Verificar integridade do arquivo
        backup_service = BackupService()
        integrity_result = backup_service.verify_backup_integrity(backup.file_path)
        
        if not integrity_result['valid']:
            error_msg = integrity_result.get('error', 'Arquivo de backup corrompido!')
            messages.error(request, error_msg)
            return redirect('config:backup_detail', slug=backup.slug)
        
        # Preparar resposta para download
        with open(backup.file_path, 'rb') as file:
            response = HttpResponse(file.read())
            
        content_type, _ = mimetypes.guess_type(backup.file_path)
        if content_type:
            response['Content-Type'] = content_type
        else:
            response['Content-Type'] = 'application/octet-stream'
        
        filename = os.path.basename(backup.file_path)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = backup.file_size
        
        return response

class BackupRestoreView(LoginRequiredMixin, PermissionRequiredMixin, BackupViewMixin, DetailView):
    """View para restauração de backups"""
    model = BackupMetadata
    template_name = 'config/backup_restore.html'
    permission_required = 'config.change_backupmetadata'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = BackupRestoreForm()
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = BackupRestoreForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                backup_service = self.get_backup_service()
                backup_before_restore = form.cleaned_data.get('backup_before_restore', True)
                
                # Determinar qual arquivo usar para restauração
                backup_file_path = self.object.file_path
                uploaded_file = form.cleaned_data.get('backup_file')
                
                if uploaded_file:
                    # Se um arquivo foi enviado, salvar temporariamente
                    import tempfile
                    import os
                    
                    temp_dir = tempfile.mkdtemp()
                    temp_file_path = os.path.join(temp_dir, uploaded_file.name)
                    
                    with open(temp_file_path, 'wb+') as destination:
                        for chunk in uploaded_file.chunks():
                            destination.write(chunk)
                    
                    backup_file_path = temp_file_path
                
                # Realizar restauração usando backup_file_path
                if self.object.backup_type == 'database':
                    success, message = backup_service.restore_database_backup(backup_file_path, request.user)
                elif self.object.backup_type == 'media':
                    success, message = backup_service.restore_media_backup(backup_file_path, request.user)
                elif self.object.backup_type == 'configuration':
                    success, message = backup_service.restore_configuration_backup(backup_file_path, request.user)
                
                if not success:
                    raise Exception(message)
                
                messages.success(request, f'Backup "{self.object.name}" restaurado com sucesso!')
                return redirect('config:backup_detail', slug=self.object.slug)
                
            except Exception as e:
                # Limpar arquivo temporário se foi criado
                if uploaded_file and os.path.exists(backup_file_path):
                    os.remove(backup_file_path)
                    os.rmdir(temp_dir)
                
            messages.error(request, f'Erro ao restaurar backup: {str(e)}')
            return self.render_to_response(self.get_context_data(form=form))
        
        return self.render_to_response(self.get_context_data(form=form))