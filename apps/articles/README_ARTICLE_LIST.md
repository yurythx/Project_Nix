# Listagem de Artigos - Nova Interface

## Visão Geral

A listagem de artigos foi redesenhada para ter uma aparência mais moderna e similar ao layout do WordPress, mantendo a compatibilidade com o CSS e JavaScript existentes do projeto FireFlies.

## Características Principais

### ✅ Funcionalidades Implementadas

1. **Layout Inspirado no WordPress**
   - Estrutura de artigo similar ao blog compartilhado
   - Imagem destacada com efeitos hover
   - Metadados organizados (data, autor, visualizações, comentários)
   - Categorias e tags clicáveis

2. **Informações Exibidas**
   - ✅ Número de visualizações (`view_count`)
   - ✅ Quantidade de comentários (`comment_count`)
   - ✅ Autor do artigo
   - ✅ Data de criação/publicação
   - ✅ Categoria do artigo
   - ✅ Tags relacionadas
   - ✅ Tempo estimado de leitura

3. **Reutilização de Implementações Existentes**
   - Modelo `Article` com todos os campos necessários
   - Sistema de comentários já implementado
   - Contador de visualizações funcional
   - Sistema de categorias e tags

## Arquivos Criados/Modificados

### Templates
- `article_list.html` - Template principal redesenhado
- `article_list_simple.html` - Versão simplificada alternativa

### CSS
- `static/css/article-list.css` - Estilos específicos para a nova listagem

### JavaScript
- `static/js/article-list.js` - Funcionalidades interativas

### Views
- `article_views.py` - Adicionado contexto de categorias

## Como Usar

### Template Principal
```html
<!-- Usar o template principal -->
{% extends 'base.html' %}
{% load static %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/article-list.css' %}">
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/article-list.js' %}"></script>
{% endblock %}
```

### Template Simples
```python
# Na view, especificar o template simples
class ArticleListView(ModuleEnabledRequiredMixin, ListView):
    template_name = 'articles/article_list_simple.html'
```

## Estrutura do Layout

### Artigo Individual
```html
<article class="article-item">
    <header class="article-header">
        <!-- Imagem destacada -->
        <div class="featured-image">...</div>
        
        <!-- Categoria -->
        <div class="category-links">...</div>
        
        <!-- Título -->
        <h2 class="article-title">...</h2>
        
        <!-- Metadados -->
        <div class="article-meta">
            <span class="posted-on">Data</span>
            <span class="byline">Autor</span>
            <span class="views">Visualizações</span>
            <span class="comments">Comentários</span>
        </div>
    </header>
    
    <div class="article-content">
        <!-- Resumo -->
        <p class="article-excerpt">...</p>
        
        <!-- Tags -->
        <div class="article-tags">...</div>
        
        <!-- Rodapé -->
        <div class="article-footer">
            <div class="reading-info">Tempo de leitura</div>
            <a href="..." class="btn">Ler mais</a>
        </div>
    </div>
</article>
```

## Funcionalidades JavaScript

### Animações
- Entrada suave dos artigos com Intersection Observer
- Efeitos hover nas imagens
- Animações de contadores

### Interatividade
- Filtros de categoria e tag
- Busca em tempo real
- Tooltips informativos
- Melhorias de acessibilidade

### Performance
- Lazy loading de imagens
- Debounce para busca
- Throttle para eventos

## Responsividade

### Desktop (> 768px)
- Layout em duas colunas (artigos + sidebar)
- Imagens grandes com efeitos hover
- Metadados em linha horizontal

### Tablet (768px - 576px)
- Layout responsivo
- Metadados em coluna
- Imagens redimensionadas

### Mobile (< 576px)
- Layout em coluna única
- Imagens menores
- Texto otimizado para leitura

## Customização

### Cores
```css
:root {
    --article-title-color: #2c3e50;
    --article-meta-color: #6c757d;
    --article-excerpt-color: #495057;
}
```

### Animações
```css
.article-item {
    animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

## Compatibilidade

### CSS Existente
- Mantém compatibilidade com `fireflies-theme.css`
- Não interfere com estilos globais
- Usa variáveis CSS do Bootstrap

### JavaScript Existente
- Não conflita com scripts existentes
- Usa padrões modernos (ES6+)
- Fallbacks para navegadores antigos

## Próximas Melhorias

### Sugeridas
1. **Filtros AJAX** - Implementar filtros sem recarregar a página
2. **Infinite Scroll** - Carregamento automático de mais artigos
3. **Modo de Visualização** - Alternar entre grid e lista
4. **Ordenação** - Por data, popularidade, título
5. **Favoritos** - Sistema de artigos favoritos

### Implementação Futura
```python
# Exemplo de filtros AJAX
class ArticleFilterView(View):
    def get(self, request):
        category = request.GET.get('category')
        tag = request.GET.get('tag')
        sort = request.GET.get('sort', '-published_at')
        
        articles = Article.objects.filter(status='published')
        
        if category:
            articles = articles.filter(category__slug=category)
        if tag:
            articles = articles.filter(tags__slug=tag)
            
        articles = articles.order_by(sort)
        
        return JsonResponse({
            'articles': [article.to_dict() for article in articles]
        })
```

## Troubleshooting

### Problemas Comuns

1. **CSS não carrega**
   - Verificar se `{% load static %}` está no template
   - Confirmar se o arquivo `article-list.css` existe

2. **JavaScript não funciona**
   - Verificar console do navegador
   - Confirmar se `article-list.js` está sendo carregado

3. **Imagens não aparecem**
   - Verificar se `MEDIA_URL` está configurado
   - Confirmar se as imagens existem no servidor

### Debug
```python
# Adicionar debug na view
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    print(f"Artigos encontrados: {len(context['articles'])}")
    print(f"Categorias: {len(context['categories'])}")
    return context
```

## Contribuição

Para contribuir com melhorias:

1. Teste em diferentes navegadores
2. Verifique responsividade
3. Mantenha compatibilidade com CSS/JS existentes
4. Documente mudanças significativas

---

**Versão**: 1.0  
**Data**: Janeiro 2025  
**Autor**: FireFlies Team 