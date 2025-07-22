# 📁 Estrutura Detalhada de Diretórios - FireFlies CMS

## 🌳 Árvore Completa do Projeto

```
Project_Nix/
├── 📁 apps/                           # Aplicações Django modulares
│   ├── 📁 accounts/                   # Sistema de usuários e autenticação
│   │   ├── 📁 migrations/             # Migrações do banco de dados
│   │   ├── 📁 templates/accounts/     # Templates específicos de usuários
│   │   │   ├── login.html             # Página de login
│   │   │   ├── register.html          # Página de registro
│   │   │   ├── profile.html           # Perfil do usuário
│   │   │   └── password_reset.html    # Recuperação de senha
│   │   ├── 📁 tests/                  # Testes do app accounts
│   │   ├── __init__.py
│   │   ├── admin.py                   # Configuração do admin
│   │   ├── apps.py                    # Configuração do app
│   │   ├── forms.py                   # Formulários de autenticação
│   │   ├── models.py                  # User, Profile models
│   │   ├── services.py                # Lógica de negócio
│   │   ├── urls.py                    # URLs do app
│   │   └── views.py                   # Views de autenticação
│   │
│   ├── 📁 articles/                   # Sistema de artigos e blog
│   │   ├── 📁 migrations/             # Migrações do banco
│   │   ├── 📁 templates/articles/     # Templates de artigos
│   │   │   ├── article_list.html      # Lista de artigos
│   │   │   ├── article_detail.html    # Detalhe do artigo
│   │   │   ├── category_list.html     # Lista de categorias
│   │   │   └── featured_articles.html # Artigos em destaque
│   │   ├── 📁 tests/                  # Testes do sistema de artigos
│   │   │   ├── test_articles_comments.py
│   │   │   ├── test_featured_articles.py
│   │   │   ├── test_editor_permissions.py
│   │   │   └── test_toc.py
│   │   ├── 📁 templatetags/           # Tags customizadas
│   │   │   ├── __init__.py
│   │   │   └── article_extras.py      # Tags para artigos
│   │   ├── __init__.py
│   │   ├── admin.py                   # Interface administrativa
│   │   ├── apps.py                    # Configuração do app
│   │   ├── forms.py                   # Formulários de artigos
│   │   ├── models.py                  # Article, Category, Tag, Comment
│   │   ├── repositories.py            # Repository pattern
│   │   ├── services.py                # Service layer
│   │   ├── urls.py                    # URLs do app
│   │   └── views.py                   # Views de artigos
│   │
│   ├── 📁 config/                     # Configurações do sistema
│   │   ├── 📁 migrations/             # Migrações de configuração
│   │   ├── 📁 templates/config/       # Templates administrativos
│   │   │   ├── base_config.html       # Base para admin
│   │   │   ├── dashboard.html         # Dashboard principal
│   │   │   ├── email_config.html      # Configuração de email
│   │   │   ├── module_config.html     # Gerenciamento de módulos
│   │   │   └── setup_wizard.html      # Wizard de configuração
│   │   ├── 📁 tests/                  # Testes de configuração
│   │   ├── __init__.py
│   │   ├── admin.py                   # Admin de configurações
│   │   ├── apps.py                    # Configuração do app
│   │   ├── forms.py                   # Formulários de config
│   │   ├── middleware.py              # SmartRedirectMiddleware
│   │   ├── models.py                  # SystemConfig, ModuleConfig
│   │   ├── services.py                # Serviços de configuração
│   │   ├── urls.py                    # URLs administrativas
│   │   └── views.py                   # Views de configuração
│   │
│   ├── 📁 pages/                      # Sistema de páginas estáticas
│   │   ├── 📁 migrations/             # Migrações de páginas
│   │   ├── 📁 templates/              # Templates globais
│   │   │   ├── 📁 includes/           # Includes reutilizáveis
│   │   │   │   ├── _head.html         # Meta tags, CSS, JS
│   │   │   │   ├── _nav.html          # Navegação principal
│   │   │   │   ├── _footer.html       # Rodapé global
│   │   │   │   ├── _toasts.html       # Sistema de notificações
│   │   │   │   └── _breadcrumbs.html  # Breadcrumbs
│   │   │   ├── 📁 pages/              # Templates de páginas
│   │   │   │   ├── default.html       # Template padrão
│   │   │   │   ├── home.html          # Página inicial
│   │   │   │   └── about.html         # Sobre
│   │   │   ├── base.html              # Template base principal
│   │   │   └── 404.html               # Página de erro 404
│   │   ├── 📁 tests/                  # Testes de páginas
│   │   ├── 📁 templatetags/           # Tags de template
│   │   │   ├── __init__.py
│   │   │   └── page_extras.py         # Tags para páginas
│   │   ├── __init__.py
│   │   ├── admin.py                   # Admin de páginas
│   │   ├── apps.py                    # Configuração do app
│   │   ├── models.py                  # Page model
│   │   ├── urls.py                    # URLs de páginas
│   │   └── views.py                   # Views de páginas
│   │
│   └── 📁 common/                     # Utilitários compartilhados
│       ├── 📁 tests/                  # Testes de utilitários
│       ├── __init__.py
│       ├── apps.py                    # Configuração do app
│       ├── factories.py               # Factory pattern
│       ├── mixins.py                  # Mixins reutilizáveis
│       ├── utils.py                   # Utilitários gerais
│       └── validators.py              # Validadores customizados
│
├── 📁 core/                           # Configurações principais Django
│   ├── __init__.py
│   ├── asgi.py                        # Configuração ASGI
│   ├── settings.py                    # Configurações principais
│   ├── urls.py                        # URLs principais
│   └── wsgi.py                        # Configuração WSGI
│
├── 📁 static/                         # Arquivos estáticos
│   ├── 📁 css/                        # Folhas de estilo
│   │   ├── main.css                   # CSS principal com sistema de cores
│   │   ├── forms.css                  # Estilos de formulários
│   │   ├── accessibility.css          # Utilitários de acessibilidade
│   │   └── tinymce-content.css        # Estilos do editor
│   ├── 📁 js/                         # JavaScript
│   │   ├── main.js                    # JavaScript principal
│   │   ├── theme-toggle.js            # Toggle de tema claro/escuro
│   │   ├── animations.js              # Animações e transições
│   │   ├── performance.js             # Otimizações de performance
│   │   └── image-optimizer.js         # Otimização de imagens
│   ├── 📁 images/                     # Imagens do sistema
│   │   ├── logo.png                   # Logo do projeto
│   │   ├── favicon.ico                # Favicon
│   │   └── placeholder.jpg            # Imagem placeholder
│   ├── 📁 fonts/                      # Fontes customizadas
│   └── demo-cores.html                # Demonstração da paleta de cores
│
├── 📁 media/                          # Uploads de usuários
│   ├── 📁 articles/                   # Uploads de artigos
│   │   └── 📁 images/                 # Imagens de artigos
│   ├── 📁 profiles/                   # Avatars de usuários
│   │   └── 📁 avatars/                # Imagens de perfil
│   └── 📁 pages/                      # Uploads de páginas
│
├── 📁 templates/                      # Templates globais adicionais
│   └── 📁 admin/                      # Customização do admin Django
│       └── base_site_custom.html      # Admin customizado
│
├── 📁 docs/                           # Documentação do projeto
│   ├── ARQUITETURA_ATUAL.md           # Documentação da arquitetura
│   ├── ACESSIBILIDADE.md              # Guia de acessibilidade
│   ├── NOVA_PALETA_ROXO.md            # Documentação das cores
│   ├── ESTRUTURA_COMPLETA_PROJETO.md  # Este documento
│   ├── ESTRUTURA_DIRETORIOS.md        # Estrutura de diretórios
│   └── API_DOCUMENTATION.md           # Documentação da API
│
├── 📁 scripts/                        # Scripts de automação
│   ├── deploy_gcp.sh                  # Deploy para Google Cloud
│   ├── setup_production.sh            # Configuração de produção
│   ├── backup.sh                      # Script de backup
│   └── migrate_data.py                # Migração de dados
│
├── 📁 env/                            # Ambiente virtual Python
│   ├── 📁 Scripts/                    # Scripts do ambiente (Windows)
│   ├── 📁 Lib/                        # Bibliotecas Python
│   └── 📁 Include/                    # Headers Python
│
├── 📁 .pytest_cache/                  # Cache do pytest
├── 📁 .git/                           # Repositório Git
│
├── 📄 manage.py                       # Script de gerenciamento Django
├── 📄 requirements.txt                # Dependências Python
├── 📄 pytest.ini                     # Configuração do pytest
├── 📄 Makefile                        # Comandos automatizados
├── 📄 .gitignore                      # Arquivos ignorados pelo Git
├── 📄 .env.example                    # Exemplo de variáveis de ambiente
├── 📄 README.md                       # Documentação principal
└── 📄 test_email_config.py            # Teste de configuração de email
```

## 📊 Estatísticas do Projeto

### Arquivos por Tipo
- **Python**: ~45 arquivos (.py)
- **HTML**: ~25 templates (.html)
- **CSS**: 4 arquivos principais (.css)
- **JavaScript**: 5 arquivos (.js)
- **Markdown**: 6 documentações (.md)
- **Configuração**: 8 arquivos (requirements.txt, pytest.ini, etc.)

### Linhas de Código (Aproximado)
- **Python**: ~3,500 linhas
- **HTML/Templates**: ~2,000 linhas
- **CSS**: ~1,800 linhas
- **JavaScript**: ~800 linhas
- **Documentação**: ~1,200 linhas

### Apps e Responsabilidades
1. **accounts** (15 arquivos) - Autenticação e usuários
2. **articles** (18 arquivos) - Sistema de blog e artigos
3. **config** (12 arquivos) - Configurações administrativas
4. **pages** (10 arquivos) - Páginas estáticas e templates
5. **common** (6 arquivos) - Utilitários compartilhados

## 🔍 Arquivos Mais Importantes

### Configuração Principal
- `core/settings.py` - Todas as configurações Django
- `core/urls.py` - Roteamento principal
- `requirements.txt` - Dependências do projeto

### Templates Base
- `apps/pages/templates/base.html` - Template principal
- `apps/pages/templates/includes/_head.html` - Meta tags e CSS
- `apps/pages/templates/includes/_nav.html` - Navegação

### Modelos Principais
- `apps/articles/models.py` - Article, Category, Tag, Comment
- `apps/accounts/models.py` - User, Profile
- `apps/config/models.py` - SystemConfig, ModuleConfig

### CSS e Design
- `static/css/main.css` - Sistema de cores e layout principal
- `static/css/accessibility.css` - Utilitários de acessibilidade
- `static/demo-cores.html` - Demonstração da paleta

### Documentação
- `README.md` - Guia principal do projeto
- `docs/ARQUITETURA_ATUAL.md` - Arquitetura detalhada
- `docs/ACESSIBILIDADE.md` - Guia de acessibilidade

---

**Esta estrutura mostra a organização completa do projeto FireFlies CMS, facilitando a navegação e compreensão do código.**
