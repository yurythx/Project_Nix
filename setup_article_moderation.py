#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.comments.models.moderation import CommentModeration
from django.contrib.contenttypes.models import ContentType
from apps.articles.models import Article

def setup_article_moderation():
    """Configura moderação para o modelo Article no sistema global de comentários"""
    
    # Obter ContentType para Article
    ct = ContentType.objects.get_for_model(Article)
    
    # Criar ou obter configuração de moderação
    config, created = CommentModeration.objects.get_or_create(
        app_label='articles',
        model_name='Article',
        defaults={
            'moderation_type': 'manual_review',
            'auto_approve_trusted_users': True,
            'require_email_verification': False,
            'max_comment_length': 2000,
            'min_comment_length': 10,
            'enable_spam_filter': True,
            'max_comments_per_hour': 5,
            'max_comments_per_day': 20,
            'notify_moderators': True,
            'notify_authors': True,
            'is_active': True
        }
    )
    
    if created:
        print(f"✅ Configuração de moderação criada para Article: {config}")
    else:
        print(f"ℹ️  Configuração de moderação já existia para Article: {config}")
    
    # Verificar configurações atuais
    print("\n📋 Configurações atuais:")
    print(f"   - Tipo de moderação: {config.moderation_type}")
    print(f"   - Auto-aprovar usuários confiáveis: {config.auto_approve_trusted_users}")
    print(f"   - Filtro de spam: {config.enable_spam_filter}")
    print(f"   - Máx. comentários/hora: {config.max_comments_per_hour}")
    print(f"   - Máx. comentários/dia: {config.max_comments_per_day}")
    print(f"   - Notificar moderadores: {config.notify_moderators}")
    print(f"   - Ativo: {config.is_active}")
    
    return config

if __name__ == '__main__':
    setup_article_moderation()