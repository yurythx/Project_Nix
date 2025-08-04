# Sistema de Verificação de Módulos para Comentários

Este documento explica como o sistema de verificação de módulos foi implementado para o aplicativo de comentários, garantindo que os comentários só sejam exibidos quando o módulo estiver ativo.

## Componentes Implementados

### 1. Decorador e Mixin (`apps/comments/decorators.py`)

#### `@require_comments_module`
Decorador para views baseadas em função que verifica se o módulo de comentários está ativo.

```python
from apps.comments.decorators import require_comments_module

@require_comments_module
def my_comment_view(request):
    # Sua lógica aqui
    pass
```

#### `CommentsModuleMixin`
Mixin para views baseadas em classe que verifica se o módulo de comentários está ativo.

```python
from apps.comments.decorators import CommentsModuleMixin

class MyCommentView(CommentsModuleMixin, View):
    # Sua view aqui
    pass
```

### 2. Template Tags Condicionais (`apps/comments/templatetags/comments_tags.py`)

#### Tags Disponíveis:

- `{% is_comments_module_enabled %}` - Verifica se o módulo de comentários está ativo
- `{% is_comments_enabled_for_app 'app_name' %}` - Verifica se comentários estão ativos para um app específico
- `{% can_show_comments object %}` - Verifica se comentários podem ser exibidos para um objeto

#### Exemplo de Uso:

```django
{% load comments_tags %}

{% is_comments_enabled_for_app 'articles' as comments_enabled %}
{% if comments_enabled %}
    {% render_comments_for_object article %}
{% else %}
    <div class="alert alert-info">
        O sistema de comentários está temporariamente desabilitado.
    </div>
{% endif %}
```

### 3. Templates Atualizados

#### Artigos
- `apps/articles/templates/articles/article_detail.html`
- `apps/articles/templates/articles/article_detail_simple.html`

Ambos templates foram atualizados para verificar se o módulo de comentários está ativo antes de exibir a seção de comentários.

#### Template de Lista de Comentários
- `apps/comments/templates/comments/comment_list_for_object.html`

Atualizado para exibir uma mensagem quando o sistema de comentários estiver desabilitado.

### 4. Views Protegidas

#### Views de Comentários (`apps/comments/views/comment_views.py`)
Todas as principais views de comentários foram protegidas com `CommentsModuleMixin`:
- `CommentListView`
- `CommentDetailView`
- `CommentCreateView`
- `CommentUpdateView`
- `CommentDeleteView`

#### Views Unificadas de Mangás (`apps/mangas/views/unified_comment_views.py`)
Views de comentários dos mangás também foram protegidas:
- `MangaCommentCreateView`
- `ChapterCommentCreateView`
- `CommentUpdateView`
- `CommentDeleteView`
- `CommentModerationView`

## Como Funciona

### 1. Verificação de Módulo
O sistema usa `ModuleService.is_module_enabled('comments')` para verificar se o módulo está ativo.

### 2. Comportamento quando Desabilitado

#### Views:
- Redirecionam para a página inicial com mensagem de aviso
- Ou retornam erro 404 dependendo do contexto

#### Templates:
- Exibem mensagem informativa em vez dos comentários
- Mantêm a estrutura visual da página

#### Template Tags:
- Retornam valores padrão (0 para contagens, listas vazias para comentários)
- Permitem verificação condicional nos templates

## Vantagens da Implementação

1. **Segurança**: Impede acesso a funcionalidades desabilitadas
2. **UX Consistente**: Usuários recebem feedback claro sobre o status
3. **Flexibilidade**: Pode ser aplicado a qualquer app que use comentários
4. **Manutenibilidade**: Centraliza a lógica de verificação
5. **Performance**: Evita processamento desnecessário quando desabilitado

## Exemplo de Integração em Novos Apps

Para integrar o sistema em um novo app (ex: `books`):

### 1. No Template:
```django
{% load comments_tags %}

{% is_comments_enabled_for_app 'books' as comments_enabled %}
{% if book.allow_comments and comments_enabled %}
    <section class="comments-section">
        <h3>Comentários</h3>
        {% render_comments_for_object book %}
    </section>
{% elif book.allow_comments and not comments_enabled %}
    <div class="alert alert-info">
        O sistema de comentários está temporariamente desabilitado.
    </div>
{% endif %}
```

### 2. Nas Views (se houver views específicas de comentários):
```python
from apps.comments.decorators import CommentsModuleMixin

class BookCommentView(CommentsModuleMixin, View):
    # Sua view aqui
    pass
```

## Configuração do Módulo

Para habilitar/desabilitar o módulo de comentários:

1. Acesse o painel administrativo
2. Vá para "Configurações de Módulos"
3. Encontre o módulo "comments"
4. Altere o status conforme necessário

Ou via código:
```python
from apps.config.services.module_service import ModuleService

# Desabilitar
ModuleService.disable_module('comments')

# Habilitar
ModuleService.enable_module('comments')
```

## Testes

Para testar a funcionalidade:

1. Desabilite o módulo de comentários no admin
2. Visite uma página com comentários (ex: artigo)
3. Verifique se a mensagem informativa é exibida
4. Tente acessar URLs de comentários diretamente
5. Reabilite o módulo e verifique se tudo volta ao normal