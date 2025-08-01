import logging
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView, ListView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models

from apps.mangas.models.manga import Manga
from apps.mangas.models.volume import Volume
from apps.mangas.models.capitulo import Capitulo
from apps.mangas.forms.volume_form import VolumeForm
from apps.mangas.mixins.permission_mixins import StaffOrSuperuserRequiredMixin

logger = logging.getLogger(__name__)

class VolumeCreateView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, CreateView):
    """
    View para criar um novo volume.
    Apenas membros da equipe ou superusuários podem acessar.
    """
    model = Volume
    form_class = VolumeForm
    template_name = 'mangas/volume_form.html'
    
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
        return context
    
    def form_valid(self, form):
        """Define o mangá e o criador do volume, com tratamento de erros."""
        try:
            manga_slug = self.kwargs.get('manga_slug')
            manga = get_object_or_404(Manga, slug=manga_slug)
            form.instance.manga = manga
            
            # Verifica se já existe um volume com o mesmo número para este mangá
            number = form.cleaned_data.get('number')
            if Volume.objects.filter(manga=manga, number=number).exists():
                form.add_error('number', f'Já existe um volume com o número {number} para este mangá.')
                return self.form_invalid(form)
                
            response = super().form_valid(form)
            messages.success(self.request, f'Volume {self.object.number} criado com sucesso!')
            return response
            
        except Exception as e:
            logger.error(f"Erro ao criar volume: {str(e)}")
            messages.error(self.request, 'Ocorreu um erro ao criar o volume. Por favor, tente novamente.')
            return self.form_invalid(form)
    
    def get_success_url(self):
        """Redireciona para a página do mangá após a criação do volume."""
        return reverse('mangas:manga_detail', kwargs={'slug': self.object.manga.slug})


class VolumeUpdateView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, UpdateView):
    """
    View para atualizar um volume existente.
    Apenas membros da equipe ou superusuários podem acessar.
    """
    model = Volume
    form_class = VolumeForm
    template_name = 'mangas/volume_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'volume_slug'
    
    def get_queryset(self):
        """Filtra os volumes pelo mangá relacionado."""
        return Volume.objects.filter(manga__slug=self.kwargs['manga_slug']).select_related('manga')
    
    def get_context_data(self, **kwargs):
        """Adiciona o mangá ao contexto."""
        context = super().get_context_data(**kwargs)
        manga_slug = self.kwargs.get('manga_slug')
        if manga_slug:
            context['manga'] = get_object_or_404(Manga, slug=manga_slug)
        return context
    
    def form_valid(self, form):
        """Exibe mensagem de sucesso ao atualizar o volume."""
        response = super().form_valid(form)
        messages.success(self.request, f'Volume {self.object.number} atualizado com sucesso!')
        return response
    
    def get_success_url(self):
        """Redireciona para a página do mangá após a atualização do volume."""
        return reverse('mangas:manga_detail', kwargs={'slug': self.object.manga.slug})


class VolumeDeleteView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, DeleteView):
    """
    View para excluir um volume existente.
    Apenas membros da equipe ou superusuários podem acessar.
    """
    model = Volume
    template_name = 'mangas/volume_confirm_delete.html'
    slug_field = 'slug'
    slug_url_kwarg = 'volume_slug'
    
    def get_queryset(self):
        """Filtra os volumes pelo mangá relacionado."""
        return Volume.objects.filter(manga__slug=self.kwargs['manga_slug']).select_related('manga')
    
    def delete(self, request, *args, **kwargs):
        """Exibe mensagem de sucesso ao excluir o volume."""
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Volume excluído com sucesso!')
        return response
    
    def get_success_url(self):
        """Redireciona para a página do mangá após a exclusão do volume."""
        return reverse('mangas:manga_detail', kwargs={'slug': self.object.manga.slug})


class VolumeDetailView(DetailView):
    """
    Exibe os detalhes de um volume, incluindo uma lista paginada de capítulos.
    """
    model = Volume
    template_name = 'mangas/volume_detail.html'
    context_object_name = 'volume'
    slug_field = 'slug'
    slug_url_kwarg = 'volume_slug'
    paginate_by = 10  # Número de capítulos por página
    
    def get_queryset(self):
        """Otimiza a consulta ao banco de dados para incluir o mangá relacionado e os capítulos."""
        # Filtra capítulos publicados para usuários não autenticados ou sem permissões
        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            capitulos_queryset = Capitulo.objects.filter(is_published=True).order_by('number').annotate(num_paginas=models.Count('paginas'))
        else:
            capitulos_queryset = Capitulo.objects.order_by('number').annotate(num_paginas=models.Count('paginas'))
            
        return (
            Volume.objects
            .filter(manga__slug=self.kwargs['manga_slug'])
            .select_related('manga')
            .prefetch_related(
                models.Prefetch(
                    'capitulos',
                    queryset=capitulos_queryset
                )
            )
        )
    
    def get_context_data(self, **kwargs):
        """Adiciona a lista paginada de capítulos e informações adicionais ao contexto."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Iniciando get_context_data para o volume: {self.object}")
        
        context = super().get_context_data(**kwargs)
        volume = self.object
        
        logger.info(f"Volume ID: {volume.id}, Número: {volume.number}, Título: {volume.title}")
        logger.info(f"Mangá: {volume.manga.title} (ID: {volume.manga.id}, Slug: {volume.manga.slug})")
        
        # Obtém todos os capítulos do volume
        logger.info("Buscando capítulos do volume...")
        capitulos = list(volume.capitulos.all())
        logger.info(f"Total de capítulos encontrados: {len(capitulos)}")
        
        # Log detalhado dos capítulos
        for i, cap in enumerate(capitulos, 1):
            logger.info(f"Capítulo {i}: ID={cap.id}, Número={cap.number}, Título='{cap.title}', Publicado={cap.is_published}")
        
        # Configura a paginação
        logger.info(f"Configurando paginação com {self.paginate_by} itens por página...")
        paginator = Paginator(capitulos, self.paginate_by)
        page = self.request.GET.get('page')
        logger.info(f"Página solicitada: {page if page else '1 (padrão)'}")
        
        try:
            capitulos_paginados = paginator.page(page)
        except PageNotAnInteger:
            # Se a página não for um inteiro, exibe a primeira página
            capitulos_paginados = paginator.page(1)
        except EmptyPage:
            # Se a página estiver fora do alcance, exibe a última página
            capitulos_paginados = paginator.page(paginator.num_pages)
        
        # Conta o total de páginas em todos os capítulos do volume
        total_paginas = sum(cap.num_paginas for cap in capitulos)
        
        # Adiciona informações ao contexto
        context.update({
            'capitulos': capitulos_paginados,
            'total_capitulos': len(capitulos),
            'total_paginas': total_paginas,
            'manga': volume.manga,
            'volumes_irmandade': list(
                Volume.objects
                .filter(manga=volume.manga)
                .exclude(id=volume.id)
                .annotate(
                    capitulo_count=models.Count('capitulos'),
                    pagina_count=models.Count('capitulos__paginas')
                )
                .order_by('number')
            )
        })
        
        return context
