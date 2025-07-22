from django.contrib.auth import get_user_model
from apps.config.models.group import Group
from django.db import transaction

User = get_user_model()

class UserService:
    """Serviço para gerenciamento de usuários."""
    @staticmethod
    def list_users():
        return User.objects.all()

    @staticmethod
    def get_user(user_id):
        return User.objects.get(id=user_id)

    @staticmethod
    def create_user(**kwargs):
        return User.objects.create_user(**kwargs)

    @staticmethod
    def update_user(user_id, **kwargs):
        user = User.objects.get(id=user_id)
        for key, value in kwargs.items():
            setattr(user, key, value)
        user.save()
        return user

    @staticmethod
    def delete_user(user_id):
        user = User.objects.get(id=user_id)
        user.delete()

    @staticmethod
    @transaction.atomic
    def add_user_to_group(user_id, group_id):
        user = User.objects.get(id=user_id)
        group = Group.objects.get(id=group_id)
        user.groups.add(group)
        user.save()
        return user

    @staticmethod
    @transaction.atomic
    def remove_user_from_group(user_id, group_id):
        user = User.objects.get(id=user_id)
        group = Group.objects.get(id=group_id)
        user.groups.remove(group)
        user.save()
        return user 