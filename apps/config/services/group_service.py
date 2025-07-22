from apps.config.models.group import Group
from django.db import transaction

class GroupService:
    """Serviço para gerenciamento de grupos de usuários."""
    @staticmethod
    def list_groups():
        return Group.objects.all()

    @staticmethod
    def get_group(group_id):
        return Group.objects.get(id=group_id)

    @staticmethod
    def create_group(**kwargs):
        return Group.objects.create(**kwargs)

    @staticmethod
    def update_group(group_id, **kwargs):
        group = Group.objects.get(id=group_id)
        for key, value in kwargs.items():
            setattr(group, key, value)
        group.save()
        return group

    @staticmethod
    def delete_group(group_id):
        group = Group.objects.get(id=group_id)
        group.delete() 