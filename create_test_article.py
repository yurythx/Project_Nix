#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.articles.models import Article
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def create_test_article():
    # Verificar se existe usuário
    user = User.objects.first()
    if not user:
        print("Nenhum usuário encontrado. Criando usuário de teste...")
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True
        )
        print(f"Usuário criado: {user.username}")
    
    # Verificar se já existe artigo de teste
    existing_article = Article.objects.filter(slug='teste-comentarios').first()
    if existing_article:
        print(f"Artigo de teste já existe: {existing_article.title} (ID: {existing_article.id})")
        return existing_article
    
    # Criar artigo de teste
    article = Article.objects.create(
        title='Teste de Comentários',
        slug='teste-comentarios',
        excerpt='Artigo para testar o sistema de comentários',
        content='<p>Este é um artigo de teste para verificar se o sistema de comentários está funcionando corretamente.</p><p>Você pode deixar um comentário abaixo para testar a funcionalidade.</p>',
        author=user,
        status='published',
        published_at=timezone.now(),
        allow_comments=True
    )
    
    print(f"Artigo criado com sucesso: {article.title} (ID: {article.id})")
    print(f"URL: /articles/{article.slug}/")
    return article

if __name__ == '__main__':
    create_test_article()