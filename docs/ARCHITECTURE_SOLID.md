# Arquitetura SOLID e Utilitários Core

Este documento apresenta os utilitários core do projeto, exemplos de uso e recomendações de integração seguindo princípios SOLID.

## 1. Observer Pattern (`core/observers.py`)

Permite comunicação desacoplada entre componentes via eventos.

### Exemplo de uso
```python
from core.observers import event_dispatcher, Event, LoggingObserver

def on_article_created(event):
    print(f"Artigo criado: {event.data}")

observer = LoggingObserver()
event_dispatcher.subscribe('article_created', observer)
event_dispatcher.dispatch(Event(name='article_created', data={'id': 1}, timestamp=None, source='articles'))
```

### Integração sugerida
- Dispare eventos em serviços após operações importantes (ex: criação de usuário, artigo, etc).
- Use observers para logging, métricas ou notificações.

---

## 2. Cache System (`core/cache.py`)

Fornece cache multi-backend (Django, memória) e decoradores para cache de funções.

### Exemplo de uso
```python
from core.cache import cache_manager, cache_result

@cache_result(timeout=60)
def expensive_operation(x):
    return x * x

result = expensive_operation(10)
```

### Integração sugerida
- Use cache em serviços para resultados de consultas pesadas.
- Utilize cache para listas, detalhes de objetos e integrações externas.

---

## 3. Validators (`core/validators.py`)

Validação extensível de dados, com resultados detalhados.

### Exemplo de uso
```python
from core.validators import validate_email, validate_password

result = validate_email('user@example.com')
if not result.is_valid:
    print(result.errors)
```

### Integração sugerida
- Valide dados em forms, serializers e serviços antes de persistir.
- Use `CompositeValidator` para regras complexas.

---

## 4. Security (`core/security.py`)

Autenticação, autorização, geração de tokens, sanitização e auditoria.

### Exemplo de uso
```python
from core.security import authenticate_user, require_permission

user = authenticate_user('admin', 'senha123')

@require_permission('articles.add_article')
def create_article(request):
    ...
```

### Integração sugerida
- Use decoradores de permissão em views.
- Utilize `SecurityProvider` para autenticação customizada.
- Sanitize entradas de usuário em serviços e forms.

---

## 5. Performance (`core/performance.py`)

Monitoramento de performance de funções, métodos e recursos do sistema.

### Exemplo de uso
```python
from core.performance import monitor_performance

@monitor_performance()
def process_data():
    ...
```

### Integração sugerida
- Decore funções críticas para monitorar tempo de execução.
- Gere relatórios de performance periodicamente.

---

## Recomendações Gerais de Integração
- Utilize ServiceFactory para injeção de dependências.
- Prefira interfaces para acoplamento fraco.
- Dispare eventos para logging, métricas e auditoria.
- Valide e sanitize dados em todas as camadas de entrada.
- Use cache para otimizar consultas e integrações externas.
- Monitore performance e segurança continuamente. 