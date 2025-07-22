# Includes Globais de Templates

Este diretório contém os includes reutilizáveis para todos os templates do Project Nix.

## Principais Includes
- `_head.html`: Cabeçalho HTML (meta, title, links, etc).
- `_nav.html`: Navbar principal do site.
- `_footer.html`: Footer global.
- `_toasts.html`: Toasts/alertas globais.
- `_breadcrumbs.html`: Breadcrumbs padronizados (use sempre via bloco `breadcrumbs`).

## Como usar
Sempre inclua estes arquivos usando:
```django
{% include 'includes/_nome_do_include.html' %}
```

Para breadcrumbs, use o bloco:
```django
{% block breadcrumbs %}
    {% with breadcrumbs=[ ... ] %}
        {{ block.super }}
    {% endwith %}
{% endblock %}
```

## Boas práticas
- Não duplique includes em outros diretórios.
- Para componentes específicos do admin, use apenas em `config/includes/`.
- Mantenha este README atualizado ao criar novos includes globais. 