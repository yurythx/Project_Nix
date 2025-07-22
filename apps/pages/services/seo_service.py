from typing import Dict, Any, List
from django.conf import settings
from apps.pages.interfaces.services import ISEOService
from apps.pages.interfaces.repositories import ISEORepository, IPageRepository
import logging

logger = logging.getLogger(__name__)

class SEOService(ISEOService):
    """Serviço para gerenciamento de SEO"""
    
    def __init__(self, seo_repository: ISEORepository, page_repository: IPageRepository = None):
        self.seo_repository = seo_repository
        self.page_repository = page_repository
    
    def get_seo_settings(self):
        """
        Obtém configurações de SEO
        :return: Configurações de SEO
        """
        return self.seo_repository.get_settings()
    
    def update_seo_settings(self, seo_data: Dict[str, Any]):
        """
        Atualiza configurações de SEO
        :param seo_data: Dados de SEO
        :return: Configurações atualizadas
        """
        settings = self.seo_repository.update_settings(seo_data)
        logger.info("Configurações de SEO atualizadas")
        return settings
    
    def generate_meta_tags(self, page) -> Dict[str, str]:
        """
        Gera meta tags para uma página
        :param page: Página
        :return: Dicionário com meta tags
        """
        seo_settings = self.get_seo_settings()
        
        meta_tags = {
            'title': page.seo_title if page else seo_settings.site_name,
            'description': page.seo_description if page else seo_settings.site_description,
            'keywords': page.meta_keywords if page and page.meta_keywords else seo_settings.site_keywords,
            'site_name': seo_settings.site_name,
            'url': page.get_absolute_url() if page else '/',
        }
        
        # Open Graph tags
        meta_tags.update({
            'og:title': meta_tags['title'],
            'og:description': meta_tags['description'],
            'og:url': meta_tags['url'],
            'og:site_name': meta_tags['site_name'],
            'og:type': 'website',
        })
        
        # Twitter Card tags
        meta_tags.update({
            'twitter:card': 'summary_large_image',
            'twitter:title': meta_tags['title'],
            'twitter:description': meta_tags['description'],
        })
        
        return meta_tags
    
    def generate_structured_data(self, page) -> Dict[str, Any]:
        """
        Gera dados estruturados (Schema.org) para uma página
        :param page: Página
        :return: Dados estruturados
        """
        seo_settings = self.get_seo_settings()
        
        # Dados básicos da organização
        organization_data = {
            "@context": "https://schema.org",
            "@type": seo_settings.organization_type,
            "name": seo_settings.site_name,
            "description": seo_settings.site_description,
            "url": getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        # Adiciona informações de contato se disponíveis
        if seo_settings.contact_email:
            organization_data["email"] = seo_settings.contact_email
        
        if seo_settings.contact_phone:
            organization_data["telephone"] = seo_settings.contact_phone
        
        if seo_settings.address:
            organization_data["address"] = seo_settings.address
        
        # Adiciona redes sociais
        social_links = seo_settings.get_social_links()
        if social_links:
            organization_data["sameAs"] = [link['url'] for link in social_links]
        
        # Se for uma página específica, adiciona dados da página
        if page:
            page_data = {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": page.title,
                "description": page.seo_description,
                "url": page.get_absolute_url(),
                "isPartOf": {
                    "@type": "WebSite",
                    "name": seo_settings.site_name,
                    "url": getattr(settings, 'SITE_URL', 'http://localhost:8000'),
                }
            }
            
            if page.published_at:
                page_data["datePublished"] = page.published_at.isoformat()
            
            if page.updated_at:
                page_data["dateModified"] = page.updated_at.isoformat()
            
            return [organization_data, page_data]
        
        return [organization_data]
    
    def generate_sitemap_data(self) -> List[Dict]:
        """
        Gera dados para sitemap
        :return: Lista de URLs para sitemap
        """
        if not self.page_repository:
            return []
        
        try:
            pages = self.page_repository.list_published()
            sitemap_data = []
            
            for page in pages:
                sitemap_data.append({
                    'url': page.get_absolute_url(),
                    'lastmod': page.updated_at,
                    'changefreq': 'weekly',
                    'priority': 1.0 if page.is_homepage else 0.8,
                })
            
            return sitemap_data
        except Exception as e:
            logger.error(f"Erro ao gerar dados do sitemap: {str(e)}")
            return []
