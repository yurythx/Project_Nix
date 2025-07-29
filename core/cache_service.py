"""
Serviço de cache distribuído usando Redis para o sistema de permissões.
"""
import json
import hashlib
from typing import Any, Optional, Dict, List
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class DistributedCacheService:
    """
    Serviço de cache distribuído com Redis para melhorar performance
    e permitir múltiplas instâncias da aplicação.
    """
    
    # Prefixos para diferentes tipos de cache
    CACHE_PREFIXES = {
        'user_groups': 'ug',
        'user_permissions': 'up',
        'object_owners': 'oo',
        'permission_checks': 'pc',
        'module_status': 'ms',
        'system_config': 'sc',
    }
    
    # TTL padrão em segundos
    DEFAULT_TTL = 300  # 5 minutos
    
    def __init__(self):
        """Inicializa o serviço de cache."""
        self.cache = cache
        self._validate_cache_backend()
    
    def _validate_cache_backend(self):
        """Valida se o backend de cache está configurado corretamente."""
        try:
            # Testa se o cache está funcionando
            test_key = "cache_test"
            self.cache.set(test_key, "test", 10)
            result = self.cache.get(test_key)
            if result != "test":
                logger.warning("Cache backend não está funcionando corretamente")
        except Exception as e:
            logger.error(f"Erro ao validar cache backend: {str(e)}")
    
    def _generate_key(self, prefix: str, *args) -> str:
        """
        Gera uma chave de cache consistente.
        
        Args:
            prefix: Prefixo do tipo de cache
            *args: Argumentos para gerar a chave
            
        Returns:
            Chave de cache formatada
        """
        # Cria uma string com todos os argumentos
        key_parts = [str(arg) for arg in args]
        key_string = f"{prefix}:{':'.join(key_parts)}"
        
        # Gera hash para chaves muito longas
        if len(key_string) > 250:
            hash_obj = hashlib.md5(key_string.encode())
            return f"{prefix}:hash:{hash_obj.hexdigest()}"
        
        return key_string
    
    def get_user_groups(self, user_id: int, groups: List[str]) -> Optional[bool]:
        """
        Obtém as permissões de grupo do usuário do cache.
        
        Args:
            user_id: ID do usuário
            groups: Lista de grupos para verificar
            
        Returns:
            True se o usuário pertence a algum grupo, False caso contrário, None se não encontrado
        """
        prefix = self.CACHE_PREFIXES['user_groups']
        key = self._generate_key(prefix, user_id, '_'.join(sorted(groups)))
        
        try:
            return self.cache.get(key)
        except Exception as e:
            logger.error(f"Erro ao obter grupos do usuário do cache: {str(e)}")
            return None
    
    def set_user_groups(self, user_id: int, groups: List[str], has_groups: bool, ttl: int = None) -> bool:
        """
        Armazena as permissões de grupo do usuário no cache.
        
        Args:
            user_id: ID do usuário
            groups: Lista de grupos verificados
            has_groups: Se o usuário pertence a algum grupo
            ttl: Tempo de vida em segundos (opcional)
            
        Returns:
            True se armazenado com sucesso, False caso contrário
        """
        prefix = self.CACHE_PREFIXES['user_groups']
        key = self._generate_key(prefix, user_id, '_'.join(sorted(groups)))
        ttl = ttl or self.DEFAULT_TTL
        
        try:
            self.cache.set(key, has_groups, ttl)
            return True
        except Exception as e:
            logger.error(f"Erro ao armazenar grupos do usuário no cache: {str(e)}")
            return False
    
    def get_user_permissions(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtém as permissões completas do usuário do cache.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dicionário com permissões ou None se não encontrado
        """
        prefix = self.CACHE_PREFIXES['user_permissions']
        key = self._generate_key(prefix, user_id)
        
        try:
            permissions_data = self.cache.get(key)
            if permissions_data and isinstance(permissions_data, str):
                return json.loads(permissions_data)
            return permissions_data
        except Exception as e:
            logger.error(f"Erro ao obter permissões do usuário do cache: {str(e)}")
            return None
    
    def set_user_permissions(self, user_id: int, permissions: Dict[str, Any], ttl: int = None) -> bool:
        """
        Armazena as permissões completas do usuário no cache.
        
        Args:
            user_id: ID do usuário
            permissions: Dicionário com permissões
            ttl: Tempo de vida em segundos (opcional)
            
        Returns:
            True se armazenado com sucesso, False caso contrário
        """
        prefix = self.CACHE_PREFIXES['user_permissions']
        key = self._generate_key(prefix, user_id)
        ttl = ttl or self.DEFAULT_TTL
        
        try:
            # Serializa para JSON para garantir compatibilidade
            permissions_json = json.dumps(permissions, default=str)
            self.cache.set(key, permissions_json, ttl)
            return True
        except Exception as e:
            logger.error(f"Erro ao armazenar permissões do usuário no cache: {str(e)}")
            return False
    
    def get_object_owner(self, model_name: str, object_id: int) -> Optional[int]:
        """
        Obtém o ID do proprietário de um objeto do cache.
        
        Args:
            model_name: Nome do modelo
            object_id: ID do objeto
            
        Returns:
            ID do usuário proprietário ou None se não encontrado
        """
        prefix = self.CACHE_PREFIXES['object_owners']
        key = self._generate_key(prefix, model_name, object_id)
        
        try:
            return self.cache.get(key)
        except Exception as e:
            logger.error(f"Erro ao obter proprietário do objeto do cache: {str(e)}")
            return None
    
    def set_object_owner(self, model_name: str, object_id: int, owner_id: int, ttl: int = None) -> bool:
        """
        Armazena o proprietário de um objeto no cache.
        
        Args:
            model_name: Nome do modelo
            object_id: ID do objeto
            owner_id: ID do usuário proprietário
            ttl: Tempo de vida em segundos (opcional)
            
        Returns:
            True se armazenado com sucesso, False caso contrário
        """
        prefix = self.CACHE_PREFIXES['object_owners']
        key = self._generate_key(prefix, model_name, object_id)
        ttl = ttl or self.DEFAULT_TTL
        
        try:
            self.cache.set(key, owner_id, ttl)
            return True
        except Exception as e:
            logger.error(f"Erro ao armazenar proprietário do objeto no cache: {str(e)}")
            return False
    
    def get_permission_check(self, user_id: int, action: str, resource: str) -> Optional[bool]:
        """
        Obtém o resultado de uma verificação de permissão do cache.
        
        Args:
            user_id: ID do usuário
            action: Ação sendo verificada
            resource: Recurso sendo acessado
            
        Returns:
            True se permitido, False se negado, None se não encontrado
        """
        prefix = self.CACHE_PREFIXES['permission_checks']
        key = self._generate_key(prefix, user_id, action, resource)
        
        try:
            return self.cache.get(key)
        except Exception as e:
            logger.error(f"Erro ao obter verificação de permissão do cache: {str(e)}")
            return None
    
    def set_permission_check(self, user_id: int, action: str, resource: str, allowed: bool, ttl: int = None) -> bool:
        """
        Armazena o resultado de uma verificação de permissão no cache.
        
        Args:
            user_id: ID do usuário
            action: Ação sendo verificada
            resource: Recurso sendo acessado
            allowed: Se a ação é permitida
            ttl: Tempo de vida em segundos (opcional)
            
        Returns:
            True se armazenado com sucesso, False caso contrário
        """
        prefix = self.CACHE_PREFIXES['permission_checks']
        key = self._generate_key(prefix, user_id, action, resource)
        ttl = ttl or self.DEFAULT_TTL
        
        try:
            self.cache.set(key, allowed, ttl)
            return True
        except Exception as e:
            logger.error(f"Erro ao armazenar verificação de permissão no cache: {str(e)}")
            return False
    
    def invalidate_user_cache(self, user_id: int) -> bool:
        """
        Invalida todo o cache relacionado a um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            True se invalidação bem-sucedida, False caso contrário
        """
        try:
            # Invalida cache de grupos
            for prefix in [self.CACHE_PREFIXES['user_groups'], self.CACHE_PREFIXES['user_permissions']]:
                pattern = f"{prefix}:{user_id}:*"
                self._delete_pattern(pattern)
            
            # Invalida verificações de permissão
            pattern = f"{self.CACHE_PREFIXES['permission_checks']}:{user_id}:*"
            self._delete_pattern(pattern)
            
            logger.info(f"Cache do usuário {user_id} invalidado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao invalidar cache do usuário {user_id}: {str(e)}")
            return False
    
    def invalidate_object_cache(self, model_name: str, object_id: int) -> bool:
        """
        Invalida o cache relacionado a um objeto específico.
        
        Args:
            model_name: Nome do modelo
            object_id: ID do objeto
            
        Returns:
            True se invalidação bem-sucedida, False caso contrário
        """
        try:
            pattern = f"{self.CACHE_PREFIXES['object_owners']}:{model_name}:{object_id}"
            self._delete_pattern(pattern)
            
            logger.info(f"Cache do objeto {model_name}:{object_id} invalidado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao invalidar cache do objeto {model_name}:{object_id}: {str(e)}")
            return False
    
    def _delete_pattern(self, pattern: str) -> bool:
        """
        Deleta chaves que correspondem a um padrão.
        
        Args:
            pattern: Padrão das chaves a serem deletadas
            
        Returns:
            True se deletado com sucesso, False caso contrário
        """
        try:
            # Para backends que suportam delete_pattern (como Redis)
            if hasattr(self.cache, 'delete_pattern'):
                return self.cache.delete_pattern(pattern)
            
            # Fallback para backends que não suportam delete_pattern
            # Nota: Esta é uma implementação simplificada
            logger.warning("Backend de cache não suporta delete_pattern")
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar padrão {pattern}: {str(e)}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do cache.
        
        Returns:
            Dicionário com estatísticas do cache
        """
        try:
            stats = {
                'backend': getattr(settings, 'CACHES', {}).get('default', {}).get('BACKEND', 'Unknown'),
                'prefixes': list(self.CACHE_PREFIXES.keys()),
                'default_ttl': self.DEFAULT_TTL,
            }
            
            # Adiciona estatísticas específicas do backend se disponível
            if hasattr(self.cache, 'get_stats'):
                stats.update(self.cache.get_stats())
            
            return stats
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do cache: {str(e)}")
            return {'error': str(e)}
    
    def clear_all_cache(self) -> bool:
        """
        Limpa todo o cache.
        
        Returns:
            True se limpeza bem-sucedida, False caso contrário
        """
        try:
            self.cache.clear()
            logger.info("Cache limpo com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {str(e)}")
            return False


# Instância global do serviço de cache
cache_service = DistributedCacheService() 