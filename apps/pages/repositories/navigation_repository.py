from typing import Dict, Any
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
from apps.pages.interfaces.repositories import INavigationRepository
from apps.pages.models import NavigationItem

class DjangoNavigationRepository(INavigationRepository):
    """Implementação concreta do repositório de navegação para Django"""
    
    def get_main_navigation(self) -> QuerySet:
        """Obtém itens de navegação principal"""
        return NavigationItem.objects.filter(
            is_active=True,
            parent__isnull=True
        ).order_by('order', 'title')
    
    def create_item(self, item_data: Dict[str, Any]) -> NavigationItem:
        """Cria item de navegação"""
        try:
            item = NavigationItem.objects.create(**item_data)
            return item
        except Exception as e:
            raise ValueError(f"Erro ao criar item de navegação: {str(e)}")
    
    def update_item(self, item_id: int, item_data: Dict[str, Any]) -> NavigationItem:
        """Atualiza item de navegação"""
        try:
            item = NavigationItem.objects.get(id=item_id)
            
            for field, value in item_data.items():
                if hasattr(item, field):
                    setattr(item, field, value)
            
            item.save()
            return item
        except NavigationItem.DoesNotExist:
            raise ObjectDoesNotExist(f"Item de navegação com ID {item_id} não encontrado")
    
    def delete_item(self, item_id: int) -> bool:
        """Deleta item de navegação"""
        try:
            item = NavigationItem.objects.get(id=item_id)
            item.delete()
            return True
        except NavigationItem.DoesNotExist:
            return False
    
    def update_order(self, item_id: int, new_order: int) -> bool:
        """Atualiza ordem do item"""
        try:
            NavigationItem.objects.filter(id=item_id).update(order=new_order)
            return True
        except Exception:
            return False
    
    def get_children(self, parent_id: int) -> QuerySet:
        """Obtém itens filhos"""
        return NavigationItem.objects.filter(
            parent_id=parent_id,
            is_active=True
        ).order_by('order', 'title')
    
    def get_by_id(self, item_id: int) -> NavigationItem:
        """Obtém item por ID"""
        try:
            return NavigationItem.objects.get(id=item_id)
        except NavigationItem.DoesNotExist:
            raise ObjectDoesNotExist(f"Item de navegação com ID {item_id} não encontrado")
    
    def list_all(self) -> QuerySet:
        """Lista todos os itens de navegação"""
        return NavigationItem.objects.all().order_by('order', 'title')
