"""
Views para upload de volumes compactados.

Este módulo contém as views para upload de arquivos compactados contendo
volumes de mangá com múltiplos capítulos organizados em pastas.
"""
import logging
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _

from apps.mangas.models.manga import Manga
from apps.mangas.models.volume import Volume
from apps.mangas.forms.volume_upload_form import VolumeUploadForm
from apps.mangas.mixins.permission_mixins import StaffOrSuperuserRequiredMixin

logger = logging.getLogger(__name__)

class VolumeUploadCreateView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, CreateView):
    """
    View para criar um novo volume com upload de arquivo compactado.
    
    Permite o upload de um arquivo compactado contendo múltiplos capítulos
    organizados em pastas. A estrutura esperada é:
    
    volume_<número>/capitulo_<número>/*.jpg
    """
    model = Volume
    form_class = VolumeUploadForm
    template_name = 'mangas/volume_upload_form.html'
    
    def get_initial(self):
        """Define o mangá relacionado ao volume."""
        initial = super().get_initial()
        manga_slug = self.kwargs.get('manga_slug')
        if manga_slug:
            initial['manga'] = get_object_or_404(Manga, slug=manga_slug)
        return initial
    
    def get_context_data(self, **kwargs):
        """Adiciona o mangá ao contexto."""
        context = super().get_context_data(**kwargs)
        manga_slug = self.kwargs.get('manga_slug')
        if manga_slug:
            context['manga'] = get_object_or_404(Manga, slug=manga_slug)
        
        # Adiciona informações sobre o formato esperado
        context['upload_help'] = {
            'title': _('Formato do Arquivo Compactado'),
            'structure': [
                _('O arquivo compactado deve conter pastas de capítulos no formato:'),
                _('- Pasta principal: volume_<NÚMERO> (ex: volume_1)'),
                _('- Subpastas: capitulo_<NÚMERO> (ex: capitulo_1, capitulo_2)'),
                _('- Arquivos: imagens numeradas (ex: 001.jpg, 002.jpg)'),
            ],
            'example': _('Exemplo de estrutura:\nvolume_1/\n  capitulo_1/\n    001.jpg\n    002.jpg\n  capitulo_2/\n    001.jpg\n    002.jpg')
        }
        
        return context
    
    def form_valid(self, form):
        """Processa o formulário e o arquivo compactado."""
        # Define o mangá relacionado ao volume
        manga_slug = self.kwargs.get('manga_slug')
        manga = get_object_or_404(Manga, slug=manga_slug)
        form.instance.manga = manga
        
        # Salva o volume e processa o arquivo compactado
        self.object = form.save()
        
        # Adiciona mensagem de sucesso
        messages.success(
            self.request, 
            _('Volume %(number)s criado com sucesso! %(chapters)s capítulos processados.') % {
                'number': self.object.number,
                'chapters': self.object.capitulos.count()
            }
        )
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Exibe mensagem de erro se o formulário for inválido."""
        messages.error(
            self.request,
            _('Erro ao criar o volume. Por favor, verifique os campos e tente novamente.')
        )
        return super().form_invalid(form)
    
    def get_success_url(self):
        """Redireciona para a página do mangá após a criação do volume."""
        return reverse('mangas:manga_detail', kwargs={'slug': self.object.manga.slug})


class VolumeUploadUpdateView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, UpdateView):
    """
    View para atualizar um volume existente com um novo arquivo compactado.
    
    Permite o upload de um novo arquivo compactado para um volume existente,
    substituindo ou adicionando aos capítulos existentes.
    """
    model = Volume
    form_class = VolumeUploadForm
    template_name = 'mangas/volume_upload_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'volume_slug'
    
    def get_queryset(self):
        """Filtra os volumes pelo mangá relacionado."""
        return Volume.objects.filter(manga__slug=self.kwargs['manga_slug'])
    
    def get_context_data(self, **kwargs):
        """Adiciona o mangá e informações sobre o volume atual ao contexto."""
        context = super().get_context_data(**kwargs)
        context['manga'] = self.object.manga
        
        # Adiciona informações sobre o volume atual
        context['current_volume'] = {
            'number': self.object.number,
            'chapters_count': self.object.capitulos.count(),
            'pages_count': sum(c.paginas.count() for c in self.object.capitulos.all())
        }
        
        # Adiciona informações sobre o formato esperado
        context['upload_help'] = {
            'title': _('Atualizar Volume %(number)s') % {'number': self.object.number},
            'structure': [
                _('O arquivo compactado deve conter pastas de capítulos no formato:'),
                _('- Pasta principal: volume_<NÚMERO> (ex: volume_%(number)d)') % {'number': self.object.number},
                _('- Subpastas: capitulo_<NÚMERO> (ex: capitulo_1, capitulo_2)'),
                _('- Arquivos: imagens numeradas (ex: 001.jpg, 002.jpg)'),
            ],
            'note': _('Nota: O upload de um novo arquivo substituirá os capítulos existentes.')
        }
        
        return context
    
    def form_valid(self, form):
        """Processa o formulário e o arquivo compactado."""
        # Salva o volume e processa o arquivo compactado
        self.object = form.save()
        
        # Adiciona mensagem de sucesso
        messages.success(
            self.request, 
            _('Volume %(number)s atualizado com sucesso! %(chapters)s capítulos processados.') % {
                'number': self.object.number,
                'chapters': self.object.capitulos.count()
            }
        )
        
        return redirect(self.get_success_url())
    
    def form_invalid(self, form):
        """Exibe mensagem de erro se o formulário for inválido."""
        messages.error(
            self.request,
            _('Erro ao atualizar o volume. Por favor, verifique o arquivo e tente novamente.')
        )
        return super().form_invalid(form)
    
    def get_success_url(self):
        """Redireciona para a página do volume após a atualização."""
        return reverse('mangas:volume_detail', kwargs={
            'manga_slug': self.object.manga.slug,
            'volume_slug': self.object.slug
        })
