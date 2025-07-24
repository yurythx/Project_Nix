# Guia de Testes

## 📋 Índice
- [🚀 Executando Testes](#-executando-testes)
- [🧪 Tipos de Testes](#-tipos-de-testes)
- [✍️ Escrevendo Testes](#️-escrevendo-testes)
- [🧩 Ferramentas](#-ferramentas)

## 🚀 Executando Testes

### Pré-requisitos
```bash
pip install -r requirements-dev.txt
```

### Comandos Básicos
```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=.

# Testes específicos
pytest apps/articles/tests/test_models.py
```

## 🧪 Tipos de Testes

### 1. Testes Unitários
Testam unidades individuais de código.

**Exemplo:** `apps/articles/tests/test_models.py`
```python
from django.test import TestCase
from apps.articles.models import Article

class TestArticleModel(TestCase):
    def test_article_creation(self):
        article = Article.objects.create(
            title='Test',
            content='Content',
            status='draft'
        )
        self.assertEqual(article.title, 'Test')
        self.assertEqual(article.status, 'draft')
```

### 2. Testes de API
Testam endpoints da API REST.

**Exemplo:** `apps/api/tests/test_views.py`
```python
from rest_framework.test import APITestCase
from django.urls import reverse

class ArticleAPITest(APITestCase):
    def test_list_articles(self):
        url = reverse('api:article-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
```

## ✍️ Escrevendo Testes

### Estrutura de Diretórios
```
app/
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   └── factories.py  # Para dados de teste
```

### Boas Práticas
1. Use nomes descritivos
2. Siga o padrão Arrange-Act-Assert
3. Mantenha os testes independentes
4. Use factories para criar dados de teste

## 🧩 Ferramentas

### Testes
- `pytest` - Framework de testes
- `pytest-django` - Suporte ao Django
- `factory-boy` - Criação de dados de teste
- `pytest-cov` - Cobertura de código

### Qualidade
- `black` - Formatação de código
- `flake8` - Linter
- `isort` - Ordenação de imports

### Testes de Interface
- `playwright` - Testes E2E
- `pytest-playwright` - Integração com pytest
