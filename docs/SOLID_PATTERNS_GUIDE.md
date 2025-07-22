# Guia de Padrões SOLID - Django Skeleton

## 📋 Visão Geral

Este documento descreve como os princípios SOLID foram aplicados no projeto Django Skeleton, fornecendo exemplos práticos e padrões de implementação.

## 🎯 Princípios SOLID

### **1. Single Responsibility Principle (SRP)**

**Definição**: Uma classe deve ter apenas uma razão para mudar.

#### **Exemplos Aplicados**

##### **✅ Bom - Service com Responsabilidade Única**

```python
class ArticleService(IArticleService):
    """Responsabilidade única: Gerenciar operações de artigos"""
    
    def __init__(self, article_repository: IArticleRepository):
        self.article_repository = article_repository
    
    def get_published_articles(self) -> List[Article]:
        """Obtém apenas artigos publicados"""
        return self.article_repository.get_published_articles()
    
    def create_article(self, article_data: Dict[str, Any], user: User) -> Optional[Article]:
        """Cria um novo artigo"""
        return self.article_repository.create_article(article_data)
```

##### **❌ Ruim - Service com Múltiplas Responsabilidades**

```python
class ArticleService:
    """Múltiplas responsabilidades: artigos, usuários, emails"""
    
    def get_published_articles(self):
        # Responsabilidade 1: Artigos
        pass
    
    def send_email_notification(self):
        # Responsabilidade 2: Emails
        pass
    
    def update_user_profile(self):
        # Responsabilidade 3: Usuários
        pass
```

#### **Padrões de Implementação**

1. **Services Especializados**
   - `ArticleService` - Apenas operações de artigos
   - `UserService` - Apenas operações de usuários
   - `EmailService` - Apenas operações de email

2. **Repositories Especializados**
   - `ArticleRepository` - Apenas acesso a dados de artigos
   - `UserRepository` - Apenas acesso a dados de usuários

3. **Views Especializadas**
   - `ArticleListView` - Apenas listagem de artigos
   - `ArticleDetailView` - Apenas detalhes de artigo

### **2. Open/Closed Principle (OCP)**

**Definição**: Entidades devem estar abertas para extensão, mas fechadas para modificação.

#### **Exemplos Aplicados**

##### **✅ Bom - Extensível via Interfaces**

```python
# Interface permite extensão
class IArticleService(ABC):
    @abstractmethod
    def get_published_articles(self) -> List[Article]:
        pass

# Implementação padrão
class ArticleService(IArticleService):
    def get_published_articles(self) -> List[Article]:
        return self.repository.get_published_articles()

# Nova implementação sem modificar código existente
class CachedArticleService(IArticleService):
    def get_published_articles(self) -> List[Article]:
        # Implementação com cache
        cached = cache.get('published_articles')
        if cached:
            return cached
        articles = self.repository.get_published_articles()
        cache.set('published_articles', articles, 3600)
        return articles
```

##### **❌ Ruim - Modificação Direta**

```python
class ArticleService:
    def get_published_articles(self):
        # Se quisermos adicionar cache, precisamos modificar esta classe
        return self.repository.get_published_articles()
```

#### **Padrões de Implementação**

1. **Interfaces Abstratas**
   ```python
   class IArticleService(ABC):
       @abstractmethod
       def get_published_articles(self) -> List[Article]:
           pass
   ```

2. **Strategy Pattern**
   ```python
   class ArticleServiceFactory:
       @staticmethod
       def create_service(strategy: str = 'default') -> IArticleService:
           if strategy == 'cached':
               return CachedArticleService()
           return ArticleService()
   ```

3. **Plugin Architecture**
   ```python
   class PluginManager:
       def register_plugin(self, name: str, plugin: IArticleService):
           self.plugins[name] = plugin
   ```

### **3. Liskov Substitution Principle (LSP)**

**Definição**: Objetos de uma superclasse devem poder ser substituídos por objetos de uma subclasse sem quebrar a aplicação.

#### **Exemplos Aplicados**

##### **✅ Bom - Substituição Transparente**

```python
# Interface base
class IArticleService(ABC):
    @abstractmethod
    def get_published_articles(self) -> List[Article]:
        pass

# Implementação real
class ArticleService(IArticleService):
    def get_published_articles(self) -> List[Article]:
        return self.repository.get_published_articles()

# Mock para testes - substitui perfeitamente
class MockArticleService(IArticleService):
    def get_published_articles(self) -> List[Article]:
        return [MockArticle(), MockArticle()]

# View funciona com qualquer implementação
class ArticleListView(View):
    def __init__(self, article_service: IArticleService):
        self.article_service = article_service
    
    def get(self, request):
        articles = self.article_service.get_published_articles()  # Funciona com ambas!
```

##### **❌ Ruim - Quebra de Contrato**

```python
class ArticleService:
    def get_published_articles(self):
        return self.repository.get_published_articles()

class MockArticleService:
    def get_published_articles(self):
        raise Exception("Database not available")  # Quebra o contrato!
```

#### **Testes LSP**

```python
class TestLiskovSubstitution(TestCase):
    """Testa se implementações podem ser substituídas"""
    
    def test_article_service_substitution(self):
        # Testa implementação real
        real_service = ArticleService(DjangoArticleRepository())
        self._test_service_contract(real_service)
        
        # Testa mock - deve funcionar igual
        mock_service = MockArticleService()
        self._test_service_contract(mock_service)
    
    def _test_service_contract(self, service: IArticleService):
        """Testa contrato da interface"""
        # Deve retornar lista
        articles = service.get_published_articles()
        self.assertIsInstance(articles, list)
        
        # Deve não lançar exceções inesperadas
        try:
            service.get_published_articles()
        except Exception as e:
            self.fail(f"Service quebrou contrato: {e}")
```

### **4. Interface Segregation Principle (ISP)**

**Definição**: Muitas interfaces específicas são melhores que uma interface geral.

#### **Exemplos Aplicados**

##### **✅ Bom - Interfaces Específicas**

```python
# Interface específica para leitura
class IArticleReader(ABC):
    @abstractmethod
    def get_published_articles(self) -> List[Article]:
        pass
    
    @abstractmethod
    def get_article_by_slug(self, slug: str) -> Optional[Article]:
        pass

# Interface específica para escrita
class IArticleWriter(ABC):
    @abstractmethod
    def create_article(self, article_data: Dict[str, Any], user: User) -> Optional[Article]:
        pass
    
    @abstractmethod
    def update_article(self, article_id: int, article_data: Dict[str, Any], user: User) -> bool:
        pass

# Interface completa herda das específicas
class IArticleService(IArticleReader, IArticleWriter):
    pass
```

##### **❌ Ruim - Interface Monolítica**

```python
class IArticleService(ABC):
    # Métodos de leitura
    def get_published_articles(self): pass
    def get_article_by_slug(self): pass
    
    # Métodos de escrita
    def create_article(self): pass
    def update_article(self): pass
    
    # Métodos de administração
    def delete_article(self): pass
    def moderate_comments(self): pass
    def generate_reports(self): pass
```

#### **Padrões de Implementação**

1. **Interfaces Granulares**
   ```python
   class IReadOnlyRepository(ABC):
       @abstractmethod
       def get_by_id(self, id: int): pass
   
   class IWritableRepository(ABC):
       @abstractmethod
       def create(self, data: Dict): pass
   
   class IRepository(IReadOnlyRepository, IWritableRepository):
       pass
   ```

2. **Composição de Interfaces**
   ```python
   class IArticleService(IArticleReader, IArticleWriter, IArticleModerator):
       pass
   ```

### **5. Dependency Inversion Principle (DIP)**

**Definição**: Dependa de abstrações, não de implementações concretas.

#### **Exemplos Aplicados**

##### **✅ Bom - Injeção de Dependência**

```python
class ArticleListView(View):
    def __init__(self, article_service: IArticleService = None):
        super().__init__()
        # Depende da abstração (interface)
        self.article_service = article_service or ArticleService(DjangoArticleRepository())
    
    def get(self, request):
        # Usa a abstração
        articles = self.article_service.get_published_articles()
        return render(request, 'articles/list.html', {'articles': articles})
```

##### **❌ Ruim - Dependência Concreta**

```python
class ArticleListView(View):
    def get(self, request):
        # Depende diretamente da implementação
        service = ArticleService(DjangoArticleRepository())
        articles = service.get_published_articles()
        return render(request, 'articles/list.html', {'articles': articles})
```

#### **Padrões de Implementação**

1. **Injeção via Construtor**
   ```python
   class Service:
       def __init__(self, repository: IRepository):
           self.repository = repository
   ```

2. **Factory Pattern**
   ```python
   class ServiceFactory:
       @staticmethod
       def create_article_service() -> IArticleService:
           return ArticleService(DjangoArticleRepository())
   ```

3. **Container de Dependências**
   ```python
   class ServiceContainer:
       def __init__(self):
           self.services = {}
       
       def register(self, interface, implementation):
           self.services[interface] = implementation
       
       def resolve(self, interface):
           return self.services[interface]()
   ```

## 🏗️ Arquitetura SOLID

### **Estrutura de Camadas**

```
┌─────────────────────────────────────┐
│              Views                  │ ← Depende de Services via interfaces
├─────────────────────────────────────┤
│            Services                 │ ← Implementa interfaces, depende de repositories
├─────────────────────────────────────┤
│           Interfaces                │ ← Contratos abstratos
├─────────────────────────────────────┤
│          Repositories               │ ← Implementa interfaces, depende de models
├─────────────────────────────────────┤
│             Models                  │ ← Entidades Django
└─────────────────────────────────────┘
```

### **Fluxo de Dependências**

```python
# 1. View depende de Service via interface
class ArticleListView(View):
    def __init__(self, article_service: IArticleService):
        self.article_service = article_service

# 2. Service implementa interface e depende de repository
class ArticleService(IArticleService):
    def __init__(self, repository: IArticleRepository):
        self.repository = repository

# 3. Repository implementa interface e depende de model
class DjangoArticleRepository(IArticleRepository):
    def get_published_articles(self):
        return Article.objects.filter(status='published')
```

## 🧪 Testes SOLID

### **1. Testes de Contrato (LSP)**

```python
class TestServiceContract(TestCase):
    """Testa se implementações respeitam contratos"""
    
    def test_article_service_contract(self):
        # Testa implementação real
        real_service = ArticleService(DjangoArticleRepository())
        self._test_contract(real_service)
        
        # Testa mock
        mock_service = MockArticleService()
        self._test_contract(mock_service)
    
    def _test_contract(self, service: IArticleService):
        """Testa contrato da interface"""
        # Deve retornar lista
        articles = service.get_published_articles()
        self.assertIsInstance(articles, list)
        
        # Deve não lançar exceções inesperadas
        try:
            service.get_published_articles()
        except Exception as e:
            self.fail(f"Quebrou contrato: {e}")
```

### **2. Testes de Injeção de Dependência**

```python
class TestDependencyInjection(TestCase):
    """Testa injeção de dependência"""
    
    def test_view_with_mock_service(self):
        mock_service = MockArticleService()
        view = ArticleListView(article_service=mock_service)
        
        # View deve funcionar com mock
        request = self.factory.get('/articles/')
        response = view.get(request)
        self.assertEqual(response.status_code, 200)
```

### **3. Testes de Responsabilidade Única**

```python
class TestSingleResponsibility(TestCase):
    """Testa se classes têm responsabilidade única"""
    
    def test_article_service_single_responsibility(self):
        service = ArticleService(DjangoArticleRepository())
        
        # Deve ter apenas métodos relacionados a artigos
        methods = [method for method in dir(service) if not method.startswith('_')]
        
        # Verifica se métodos são relacionados a artigos
        for method in methods:
            self.assertTrue(
                'article' in method.lower() or 
                method in ['get_published_articles', 'get_featured_articles'],
                f"Método {method} não parece relacionado a artigos"
            )
```

## 📊 Métricas de Qualidade SOLID

### **1. Coesão (SRP)**
- **Alto**: Classes com responsabilidades bem definidas
- **Médio**: Classes com algumas responsabilidades relacionadas
- **Baixo**: Classes com múltiplas responsabilidades não relacionadas

### **2. Acoplamento (DIP)**
- **Baixo**: Dependências via interfaces
- **Médio**: Algumas dependências diretas
- **Alto**: Muitas dependências diretas

### **3. Extensibilidade (OCP)**
- **Alta**: Novas funcionalidades via extensão
- **Média**: Algumas modificações necessárias
- **Baixa**: Muitas modificações necessárias

## 🚀 Próximos Passos

### **1. Melhorias de Arquitetura**
- [ ] Implementar container de dependências
- [ ] Adicionar mais interfaces granulares
- [ ] Implementar padrão Observer para eventos

### **2. Testes Avançados**
- [ ] Testes de performance com mocks
- [ ] Testes de integração completos
- [ ] Testes de stress

### **3. Documentação**
- [ ] Documentar padrões de design
- [ ] Criar exemplos de uso
- [ ] Documentar decisões arquiteturais

---

**Última Atualização**: Dezembro 2024  
**Versão**: 1.0  
**Status**: ✅ Implementado 