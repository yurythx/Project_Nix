from typing import Dict, Any
from django.core.exceptions import ObjectDoesNotExist
from apps.pages.interfaces.repositories import ISEORepository
from apps.pages.models import SEOSettings

class DjangoSEORepository(ISEORepository):
    """Implementação concreta do repositório de SEO para Django"""
    
    def get_settings(self) -> SEOSettings:
        """Obtém configurações de SEO"""
        return SEOSettings.get_settings()
    
    def update_settings(self, seo_data: Dict[str, Any]) -> SEOSettings:
        """Atualiza configurações de SEO"""
        settings = self.get_settings()
        
        for field, value in seo_data.items():
            if hasattr(settings, field):
                setattr(settings, field, value)
        
        settings.save()
        return settings
    
    def create_settings(self, seo_data: Dict[str, Any]) -> SEOSettings:
        """Cria configurações de SEO"""
        try:
            settings = SEOSettings.objects.create(**seo_data)
            return settings
        except Exception as e:
            raise ValueError(f"Erro ao criar configurações de SEO: {str(e)}")
