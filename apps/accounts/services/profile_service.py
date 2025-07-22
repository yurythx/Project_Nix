import os
from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps
from apps.accounts.interfaces.services import IProfileService
from apps.accounts.interfaces.repositories import IUserRepository
import logging

logger = logging.getLogger(__name__)

class ProfileService(IProfileService):
    """Serviço para gerenciamento de perfil de usuários"""

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    def get_profile(self, slug: str):
        """
        Obtém o perfil de um usuário pelo slug
        :param slug: Slug do usuário
        :return: Instância do usuário
        :raises ObjectDoesNotExist: Se o usuário não for encontrado
        """
        try:
            return self.user_repository.get_user_by_slug(slug)
        except ObjectDoesNotExist:
            logger.warning(f"Tentativa de acessar perfil inexistente: {slug}")
            raise

    def update_profile(self, user, data: dict):
        """
        Atualiza os dados do perfil de um usuário
        :param user: Instância do usuário a ser atualizado
        :param data: Dados a serem atualizados
        :return: Instância do usuário atualizado
        """
        try:
            updated_user = self.user_repository.update_user(user, **data)
            logger.info(f"Perfil atualizado para usuário: {user.email}")
            return updated_user
        except Exception as e:
            logger.error(f"Erro ao atualizar perfil do usuário {user.email}: {str(e)}")
            raise

    def remove_avatar(self, user) -> bool:
        """
        Remove o avatar de um usuário
        :param user: Instância do usuário
        :return: True se o avatar foi removido com sucesso
        """
        try:
            if user.avatar:
                # Remove o arquivo físico
                if os.path.exists(user.avatar.path):
                    os.remove(user.avatar.path)
                
                # Atualiza o usuário removendo a referência ao avatar
                self.user_repository.update_user(user, avatar=None)
                logger.info(f"Avatar removido para usuário: {user.email}")
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao remover avatar do usuário {user.email}: {str(e)}")
            return False

    def get_user_statistics(self, user) -> dict:
        """
        Obtém estatísticas do usuário (artigos, comentários, etc.)
        :param user: Instância do usuário
        :return: Dicionário com estatísticas
        """
        try:
            stats = {
                'total_articles': 0,
                'total_comments': 0,
                'member_since': user.date_joined,
                'last_login': user.last_login,
                'is_verified': user.is_verified,
            }
            
            # Contar artigos se o app articles estiver disponível
            try:
                Article = apps.get_model('articles', 'Article')
                stats['total_articles'] = Article.objects.filter(author=user).count()
            except (LookupError, AttributeError):
                pass
            
            # Contar comentários se o app articles estiver disponível
            try:
                Comment = apps.get_model('articles', 'Comment')
                # Tenta pelo campo 'user', se não existir tenta 'author'
                if hasattr(Comment, 'user'):
                    stats['total_comments'] = Comment.objects.filter(user=user).count()
                elif hasattr(Comment, 'author'):
                    stats['total_comments'] = Comment.objects.filter(author=user).count()
            except (LookupError, AttributeError):
                pass
            
            logger.debug(f"Estatísticas obtidas para usuário: {user.email}")
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do usuário {user.email}: {str(e)}")
            return {
                'total_articles': 0,
                'total_comments': 0,
                'member_since': user.date_joined,
                'last_login': user.last_login,
                'is_verified': user.is_verified,
            }

    # Implementação dos métodos abstratos da interface
    def get_user_profile(self, user) -> dict:
        """
        Obtém o perfil do usuário
        :param user: Usuário
        :return: Dados do perfil
        """
        try:
            profile_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'bio': getattr(user, 'bio', ''),
                'location': getattr(user, 'location', ''),
                'birth_date': getattr(user, 'birth_date', None),
                'avatar': user.avatar.url if user.avatar else None,
                'is_verified': getattr(user, 'is_verified', False),
                'date_joined': user.date_joined,
                'last_login': user.last_login,
            }
            
            # Adicionar estatísticas
            stats = self.get_user_statistics(user)
            profile_data.update(stats)
            
            logger.debug(f"Perfil obtido para usuário: {user.email}")
            return profile_data
            
        except Exception as e:
            logger.error(f"Erro ao obter perfil do usuário {user.email}: {str(e)}")
            return {}

    def update_user_profile(self, user, profile_data: dict) -> bool:
        """
        Atualiza o perfil do usuário
        :param user: Usuário
        :param profile_data: Dados para atualização
        :return: True se atualizado com sucesso
        """
        try:
            # Campos permitidos para atualização
            allowed_fields = ['first_name', 'last_name', 'bio', 'location', 'birth_date']
            
            update_data = {}
            for field in allowed_fields:
                if field in profile_data:
                    update_data[field] = profile_data[field]
            
            if update_data:
                self.user_repository.update_user(user, **update_data)
                logger.info(f"Perfil atualizado para usuário: {user.email}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao atualizar perfil do usuário {user.email}: {str(e)}")
            return False

    def update_avatar(self, user, avatar_file) -> bool:
        """
        Atualiza o avatar do usuário
        :param user: Usuário
        :param avatar_file: Arquivo do avatar
        :return: True se atualizado com sucesso
        """
        try:
            # Remove avatar anterior se existir
            if user.avatar:
                self.delete_avatar(user)
            
            # Atualiza com novo avatar
            self.user_repository.update_user(user, avatar=avatar_file)
            logger.info(f"Avatar atualizado para usuário: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar avatar do usuário {user.email}: {str(e)}")
            return False

    def delete_avatar(self, user) -> bool:
        """
        Remove o avatar do usuário
        :param user: Usuário
        :return: True se removido com sucesso
        """
        return self.remove_avatar(user) 