# Guia ServiceFactory e Observer - Django Skeleton

## 📋 Visão Geral

Este guia explica como usar o **ServiceFactory** para injeção automática de dependências e o **Observer/EventDispatcher** para implementar lógica reativa desacoplada.

## 🏭 ServiceFactory

### **Uso Básico**

```python
from core.factories import service_factory

# Obter serviços com dependências injetadas automaticamente
article_service = service_factory.create_article_service()
profile_service = service_factory.create_profile_service()
registration_service = service_factory.create_registration_service()
```

### **Injeção de Dependências Customizadas**

```python
# Usar repository customizado
custom_repo = MockArticleRepository()
article_service = service_factory.create_article_service(
    article_repository=custom_repo
)

# Usar email service customizado
custom_email = MockEmailService()
registration_service = service_factory.create_registration_service(
    email_service=custom_email
)
```

### **Configuração via Settings**

```python
# settings.py
SERVICE_OVERRIDES = {
    'IArticleService': 'core.examples.cached_article_service.CachedArticleService',
    'IEmailService': 'apps.accounts.services.mock_email_service.MockEmailService',
}
```

### **Cache de Serviços**

O ServiceFactory implementa cache automático:

```python
# Primeira chamada - cria nova instância
service1 = service_factory.create_article_service()

# Segunda chamada - retorna instância cachead
service2 = service_factory.create_article_service()

# São a mesma instância
assert service1 is service2

# Limpar cache se necessário
service_factory.clear_cache()
```

## 👁️ Observer/EventDispatcher

### **Uso Básico**

```python
from core.observers import event_dispatcher

# Definir callback para evento
def on_article_created(article):
    print(f"Novo artigo criado: {article.title}")
    # Lógica adicional: notificação, log, cache invalidation, etc.

# Inscrever para evento
event_dispatcher.subscribe('article_created', on_article_created)

# Disparar evento (geralmente feito pelos serviços)
event_dispatcher.notify('article_created', article_instance)

# Remover inscrição quando não precisar mais
event_dispatcher.unsubscribe('article_created', on_article_created)
```

### **Múltiplos Observers**

```python
def log_article_created(article):
    logger.info(f"Artigo criado: {article.title}")

def send_notification(article):
    notification_service.send_to_admin(f"Novo artigo: {article.title}")

def update_cache(article):
    cache.delete('published_articles')

# Todos os callbacks são executados quando o evento é disparado
event_dispatcher.subscribe('article_created', log_article_created)
event_dispatcher.subscribe('article_created', send_notification)
event_dispatcher.subscribe('article_created', update_cache)
```

### **Eventos Disponíveis**

#### **Articles App**
- `article_created` - Disparado ao criar artigo
- `article_updated` - Disparado ao atualizar artigo
- `article_deleted` - Disparado ao deletar artigo

#### **Accounts App**
- `user_registered` - Disparado ao registrar usuário
- `user_verified` - Disparado ao verificar usuário
- `password_changed` - Disparado ao alterar senha

#### **Config App**
- `config_changed` - Disparado ao alterar configuração
- `module_enabled` - Disparado ao habilitar módulo
- `module_disabled` - Disparado ao desabilitar módulo

#### **Pages App**
- `page_created` - Disparado ao criar página
- `page_updated` - Disparado ao atualizar página
- `page_deleted` - Disparado ao deletar página

## 🔧 Integração com Views

### **Views com ServiceFactory**

```python
from core.factories import service_factory

class ArticleListView(View):
    def __init__(self, article_service=None):
        super().__init__()
        # Usa factory para injeção automática
        self.article_service = article_service or service_factory.create_article_service()
    
    def get(self, request):
        articles = self.article_service.get_published_articles()
        return render(request, 'articles/list.html', {'articles': articles})
```

### **Views com Observer**

```python
from core.observers import event_dispatcher

class ArticleCreateView(CreateView):
    def form_valid(self, form):
        article = form.save()
        
        # Dispara evento para observers
        event_dispatcher.notify('article_created', article)
        
        return super().form_valid(form)
```

## 🧪 Testes

### **Testes com ServiceFactory**

```python
from django.test import TestCase
from unittest.mock import Mock
from core.factories import service_factory

class ArticleViewTest(TestCase):
    def test_article_list_with_mock_service(self):
        # Criar mock service
        mock_service = Mock()
        mock_service.get_published_articles.return_value = []
        
        # Injetar mock na view
        view = ArticleListView(article_service=mock_service)
        
        # Testar
        request = self.factory.get('/articles/')
        response = view.get(request)
        
        self.assertEqual(response.status_code, 200)
        mock_service.get_published_articles.assert_called_once()
```

### **Testes com Observer**

```python
from core.observers import event_dispatcher

class ObserverTest(TestCase):
    def test_article_created_event(self):
        called = {'count': 0}
        
        def callback(article):
            called['count'] += 1
            called['title'] = article.title
        
        # Inscrever para evento
        event_dispatcher.subscribe('article_created', callback)
        
        # Simular criação de artigo
        article = Article.objects.create(title='Test Article')
        event_dispatcher.notify('article_created', article)
        
        # Verificar se callback foi chamado
        self.assertEqual(called['count'], 1)
        self.assertEqual(called['title'], 'Test Article')
        
        # Limpar
        event_dispatcher.unsubscribe('article_created', callback)
```

## 📊 Exemplos Avançados

### **Implementação Customizada com Cache**

```python
# core/examples/cached_article_service.py
from django.core.cache import cache
from apps.articles.interfaces.services import IArticleService

class CachedArticleService(IArticleService):
    def get_published_articles(self):
        cache_key = 'published_articles'
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        articles = self.article_repository.get_published_articles()
        cache.set(cache_key, articles, 3600)
        return articles
```

### **Observer para Logging**

```python
import logging
from core.observers import event_dispatcher

logger = logging.getLogger(__name__)

def log_user_events(data):
    user = data['user']
    logger.info(f"Usuário registrado: {user.email}")

def log_article_events(article):
    logger.info(f"Artigo criado: {article.title} por {article.author}")

# Inscrever para eventos
event_dispatcher.subscribe('user_registered', log_user_events)
event_dispatcher.subscribe('article_created', log_article_events)
```

### **Observer para Notificações**

```python
from core.observers import event_dispatcher

def notify_admin_article_created(article):
    # Enviar notificação para admin
    notification_service.send_to_admin(
        f"Novo artigo criado: {article.title}"
    )

def notify_author_article_published(article):
    # Enviar notificação para autor
    notification_service.send_to_user(
        article.author,
        f"Seu artigo '{article.title}' foi publicado!"
    )

# Inscrever para eventos
event_dispatcher.subscribe('article_created', notify_admin_article_created)
event_dispatcher.subscribe('article_published', notify_author_article_published)
```

## 🚀 Boas Práticas

### **1. ServiceFactory**
- ✅ Use sempre o factory para obter serviços
- ✅ Injete dependências customizadas apenas quando necessário
- ✅ Configure implementações customizadas via settings
- ✅ Limpe o cache quando precisar de nova instância

### **2. Observer**
- ✅ Mantenha callbacks simples e focados
- ✅ Use nomes descritivos para eventos
- ✅ Sempre remova inscrições quando não precisar mais
- ✅ Trate exceções nos callbacks
- ✅ Use logging para debug

### **3. Performance**
- ✅ O cache do ServiceFactory melhora performance
- ✅ Observers são executados de forma síncrona
- ✅ Para operações pesadas, considere usar Celery
- ✅ Monitore o número de observers por evento

## 🔍 Debugging

### **Verificar Serviços em Cache**

```python
from core.factories import service_factory

# Ver quais serviços estão cacheados
cached_services = service_factory.get_cached_services()
print(f"Serviços em cache: {list(cached_services.keys())}")
```

### **Verificar Observers Ativos**

```python
from core.observers import event_dispatcher

# Ver quais eventos têm observers
active_events = event_dispatcher._subscribers.keys()
print(f"Eventos ativos: {list(active_events)}")

# Ver quantos observers por evento
for event, callbacks in event_dispatcher._subscribers.items():
    print(f"{event}: {len(callbacks)} observers")
```

---

**Última Atualização**: Dezembro 2024  
**Versão**: 1.0  
**Status**: ✅ Implementado 