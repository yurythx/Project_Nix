from typing import Dict, Any
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, QuerySet, F
from django.utils import timezone
from apps.pages.interfaces.repositories import IPageRepository
from apps.pages.models import Page

class DjangoPageRepository(IPageRepository):
    """Implementação concreta do repositório de páginas para Django"""
    
    def create(self, page_data: Dict[str, Any]) -> Page:
        """Cria uma nova página"""
        try:
            page = Page.objects.create(**page_data)
            return page
        except Exception as e:
            raise ValueError(f"Erro ao criar página: {str(e)}")
    
    def get_by_id(self, page_id: int) -> Page:
        """Obtém página por ID"""
        try:
            return Page.objects.get(id=page_id)
        except Page.DoesNotExist:
            raise ObjectDoesNotExist(f"Página com ID {page_id} não encontrada")
    
    def get_by_slug(self, slug: str) -> Page:
        """Obtém página por slug"""
        try:
            return Page.objects.get(slug=slug, status='published')
        except Page.DoesNotExist:
            raise ObjectDoesNotExist(f"Página com slug '{slug}' não encontrada")
    
    def get_homepage(self) -> Page:
        """Obtém página inicial"""
        try:
            return Page.objects.get(is_homepage=True, status='published')
        except Page.DoesNotExist:
            # Se não há homepage definida, retorna a primeira página publicada
            try:
                return Page.objects.filter(status='published').order_by('created_at').first()
            except:
                raise ObjectDoesNotExist("Nenhuma página inicial encontrada")
    
    def update(self, page_id: int, page_data: Dict[str, Any]) -> Page:
        """Atualiza página"""
        page = self.get_by_id(page_id)
        
        for field, value in page_data.items():
            if hasattr(page, field):
                setattr(page, field, value)
        
        page.save()
        return page
    
    def delete(self, page_id: int) -> bool:
        """Deleta página"""
        try:
            page = self.get_by_id(page_id)
            
            # Não permite deletar homepage
            if page.is_homepage:
                raise ValueError("Não é possível deletar a página inicial")
            
            page.delete()
            return True
        except ObjectDoesNotExist:
            return False
    
    def list_published(self) -> QuerySet:
        """Lista páginas publicadas"""
        return Page.objects.filter(
            status='published'
        ).order_by('menu_order', 'title')
    
    def list_menu_pages(self) -> QuerySet:
        """Lista páginas para menu"""
        return Page.objects.filter(
            status='published',
            show_in_menu=True
        ).order_by('menu_order', 'title')
    
    def search(self, query: str) -> QuerySet:
        """Busca páginas por termo"""
        if not query:
            return Page.objects.none()
        
        return Page.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(meta_keywords__icontains=query),
            status='published'
        ).order_by('-updated_at')
    
    def get_popular_pages(self, limit: int = 10) -> QuerySet:
        """Obtém páginas mais populares"""
        return Page.objects.filter(
            status='published'
        ).order_by('-view_count')[:limit]
    
    def increment_view_count(self, page_id: int) -> None:
        """Incrementa contador de visualizações"""
        try:
            Page.objects.filter(id=page_id).update(
                view_count=F('view_count') + 1
            )
        except Exception:
            # Falha silenciosa para não afetar a experiência do usuário
            pass
    
    def get_children(self, parent_id: int) -> QuerySet:
        """Obtém páginas filhas"""
        return Page.objects.filter(
            parent_id=parent_id,
            status='published'
        ).order_by('menu_order', 'title')
    
    def get_breadcrumb_pages(self, page: Page) -> list:
        """Obtém páginas para breadcrumb"""
        breadcrumbs = []
        current_page = page
        
        while current_page:
            breadcrumbs.insert(0, current_page)
            current_page = current_page.parent
        
        return breadcrumbs
    
    def list_all(self, filters: Dict[str, Any] = None) -> QuerySet:
        """Lista todas as páginas com filtros opcionais"""
        queryset = Page.objects.all()
        
        if filters:
            # Filtro por status
            if 'status' in filters:
                queryset = queryset.filter(status=filters['status'])
            
            # Filtro por autor
            if 'created_by' in filters:
                queryset = queryset.filter(created_by=filters['created_by'])
            
            # Filtro por data
            if 'date_from' in filters:
                queryset = queryset.filter(created_at__gte=filters['date_from'])
            
            if 'date_to' in filters:
                queryset = queryset.filter(created_at__lte=filters['date_to'])
            
            # Filtro por template
            if 'template' in filters:
                queryset = queryset.filter(template=filters['template'])
        
        return queryset.order_by('-updated_at')
    
    def exists_by_slug(self, slug: str, exclude_id: int = None) -> bool:
        """Verifica se existe página com o slug"""
        queryset = Page.objects.filter(slug=slug)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        return queryset.exists()
    
    def publish_page(self, page_id: int) -> Page:
        """Publica uma página"""
        page = self.get_by_id(page_id)
        page.status = 'published'
        page.published_at = timezone.now()
        page.save()
        return page
    
    def unpublish_page(self, page_id: int) -> Page:
        """Despublica uma página"""
        page = self.get_by_id(page_id)
        page.status = 'draft'
        page.save()
        return page
