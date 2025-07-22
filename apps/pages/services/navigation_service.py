from typing import List, Dict, Any
from apps.pages.interfaces.services import INavigationService
from apps.pages.interfaces.repositories import INavigationRepository
import logging

logger = logging.getLogger(__name__)

class NavigationService(INavigationService):
    """Serviço para gerenciamento de navegação"""
    
    def __init__(self, navigation_repository: INavigationRepository):
        self.navigation_repository = navigation_repository
    
    def get_main_navigation(self) -> List[Dict]:
        """
        Obtém navegação principal
        :return: Lista de itens de navegação
        """
        try:
            items = self.navigation_repository.get_main_navigation()
            navigation_data = []
            
            for item in items:
                item_data = {
                    'id': item.id,
                    'title': item.title,
                    'url': item.get_url(),
                    'icon': item.icon,
                    'css_class': item.css_class,
                    'open_in_new_tab': item.open_in_new_tab,
                    'children': []
                }
                
                # Adiciona filhos se existirem
                children = item.get_children()
                for child in children:
                    child_data = {
                        'id': child.id,
                        'title': child.title,
                        'url': child.get_url(),
                        'icon': child.icon,
                        'css_class': child.css_class,
                        'open_in_new_tab': child.open_in_new_tab,
                    }
                    item_data['children'].append(child_data)
                
                navigation_data.append(item_data)
            
            return navigation_data
        except Exception as e:
            logger.error(f"Erro ao obter navegação principal: {str(e)}")
            return []
    
    def get_breadcrumbs(self, page) -> List[Dict]:
        """
        Obtém breadcrumbs para uma página
        :param page: Página atual
        :return: Lista de breadcrumbs
        """
        breadcrumbs = []
        
        # Adiciona Home
        breadcrumbs.append({
            'title': 'Home',
            'url': '/',
            'is_current': False
        })
        
        # Adiciona páginas pai
        if page and hasattr(page, 'get_breadcrumbs'):
            page_breadcrumbs = page.get_breadcrumbs()
            
            for i, breadcrumb_page in enumerate(page_breadcrumbs):
                is_current = (i == len(page_breadcrumbs) - 1)
                
                breadcrumbs.append({
                    'title': breadcrumb_page.title,
                    'url': breadcrumb_page.get_absolute_url() if not is_current else None,
                    'is_current': is_current
                })
        
        return breadcrumbs
    
    def create_navigation_item(self, item_data: Dict[str, Any]):
        """
        Cria item de navegação
        :param item_data: Dados do item
        :return: Item criado
        """
        # Validações
        title = item_data.get('title')
        if not title:
            raise ValueError("Título é obrigatório")
        
        nav_type = item_data.get('nav_type', 'page')
        
        if nav_type == 'page' and not item_data.get('page'):
            raise ValueError("Página é obrigatória para itens do tipo 'Página'")
        
        if nav_type == 'url' and not item_data.get('url'):
            raise ValueError("URL é obrigatória para itens do tipo 'URL Externa'")
        
        # Cria o item
        item = self.navigation_repository.create_item(item_data)
        
        logger.info(f"Item de navegação criado: {item.title}")
        return item
    
    def update_navigation_order(self, items_order: List[Dict]) -> bool:
        """
        Atualiza ordem dos itens de navegação
        :param items_order: Lista com IDs e novas ordens
        :return: True se atualizado com sucesso
        """
        try:
            for item_order in items_order:
                item_id = item_order.get('id')
                new_order = item_order.get('order')
                
                if item_id and new_order is not None:
                    self.navigation_repository.update_order(item_id, new_order)
            
            logger.info("Ordem de navegação atualizada")
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar ordem de navegação: {str(e)}")
            return False
