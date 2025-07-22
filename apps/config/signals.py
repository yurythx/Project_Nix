from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    """Log quando um usuário é criado ou atualizado"""
    if created:
        logger.info(f"Novo usuário criado: {instance.email} (ID: {instance.id})")
    else:
        logger.info(f"Usuário atualizado: {instance.email} (ID: {instance.id})")

@receiver(post_delete, sender=User)
def log_user_deletion(sender, instance, **kwargs):
    """Log quando um usuário é deletado"""
    logger.info(f"Usuário deletado: {instance.email} (ID: {instance.id})")

@receiver(post_save, sender=Group)
def log_group_creation(sender, instance, created, **kwargs):
    """Log quando um grupo é criado ou atualizado"""
    if created:
        logger.info(f"Novo grupo criado: {instance.name} (ID: {instance.id})")
    else:
        logger.info(f"Grupo atualizado: {instance.name} (ID: {instance.id})")
