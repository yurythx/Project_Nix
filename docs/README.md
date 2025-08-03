# 📚 Project Nix - Documentação Oficial

> **Plataforma de Gerenciamento de Conteúdo Digital Modular e Moderna**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://djangoproject.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

---

## 🎯 Visão Geral

O **Project Nix** é uma plataforma completa de gerenciamento de conteúdo digital, projetada para ser o centro unificado de diferentes tipos de mídia e conteúdo. Com uma arquitetura modular baseada em princípios SOLID, oferece uma experiência moderna e responsiva para criadores e consumidores de conteúdo.

### 🌟 Propósito Principal

**Centralizar e democratizar o acesso a conteúdo digital diversificado**, oferecendo:

- 📖 **Biblioteca Digital**: Livros, e-books e audiolivros
- 📰 **Portal de Artigos**: Sistema completo de publicação e leitura
- 🎌 **Leitor de Mangás**: Experiência otimizada para quadrinhos digitais
- 📄 **Páginas Dinâmicas**: Conteúdo institucional e informativo
- 👥 **Comunidade**: Sistema de usuários, comentários e interações

---

## 🏗️ Arquitetura do Sistema

### **Módulos Principais**

```
🏠 Project Nix
├── 👤 Accounts      → Autenticação e perfis de usuário
├── 📰 Articles      → Sistema de artigos e blog
├── 📚 Books         → Biblioteca digital e e-books
├── 🎧 Audiobooks    → Audiolivros e conteúdo sonoro
├── 🎌 Mangas        → Leitor de mangás e quadrinhos
├── 📄 Pages         → Páginas estáticas e dinâmicas
├── 💬 Comments      → Sistema unificado de comentários
└── ⚙️ Config       → Administração e configurações
```

### **Tecnologias Core**

- **Backend**: Django 5.2 + Django REST Framework
- **Frontend**: HTML5, CSS3, JavaScript ES6+, Bootstrap 5
- **Banco de Dados**: PostgreSQL (produção) / SQLite (desenvolvimento)
- **Cache**: Redis (opcional)
- **Arquitetura**: SOLID Principles + Design Patterns

---

## 🚀 Início Rápido

### **Pré-requisitos**
```bash
# Requisitos mínimos
Python 3.11+
Git
PostgreSQL 12+ (produção)
```

### **Instalação**

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/project-nix.git
cd project-nix

# 2. Ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 3. Dependências
pip install -r requirements.txt

# 4. Configuração
cp .env.example .env
# Edite o .env com suas configurações

# 5. Banco de dados
python manage.py migrate
python manage.py collectstatic --noinput

# 6. Superusuário
python manage.py createsuperuser

# 7. Executar
python manage.py runserver
```

### **Acesso**
- **Frontend**: http://localhost:8000
- **Admin**: http://localhost:8000/admin
- **API**: http://localhost:8000/api

---

## 📖 Guias de Uso

### **Para Administradores**

1. **Configuração Inicial**
   - Acesse `/admin` e configure os módulos ativos
   - Configure email e notificações
   - Defina permissões de usuários

2. **Gerenciamento de Conteúdo**
   - Crie categorias para artigos e livros
   - Configure moderação de comentários
   - Monitore estatísticas de uso

### **Para Criadores de Conteúdo**

1. **Artigos**
   ```python
   # Criar artigo via interface web ou API
   POST /api/articles/
   {
     "title": "Meu Artigo",
     "content": "Conteúdo...",
     "category": "tecnologia"
   }
   ```

2. **Livros/E-books**
   - Upload de arquivos PDF/EPUB
   - Configuração de metadados
   - Controle de acesso

3. **Mangás**
   - Upload de capítulos em lote
   - Organização por volumes
   - Sistema de páginas otimizado

### **Para Desenvolvedores**

1. **Extensão de Módulos**
   ```python
   # Criar novo módulo
   python manage.py startapp meu_modulo
   
   # Registrar no sistema
   # apps/config/models/app_module_config.py
   ```

2. **API Personalizada**
   ```python
   # Usar services existentes
   from apps.articles.services import ArticleService
   
   article_service = ArticleService()
   articles = article_service.get_featured_articles()
   ```

---

## 🔧 Configuração Avançada

### **Variáveis de Ambiente**

```env
# Ambiente
ENVIRONMENT=development
DEBUG=True

# Banco de dados
DB_ENGINE=django.db.backends.postgresql
DB_NAME=project_nix
DB_USER=nix_user
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu_email@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_app

# Segurança
SECRET_KEY=sua_chave_secreta_muito_longa
ALLOWED_HOSTS=localhost,127.0.0.1,seudominio.com

# Módulos (separados por vírgula)
ACTIVE_MODULES=accounts,config,pages,articles,books,mangas,audiobooks,comments

# Cache (opcional)
REDIS_URL=redis://localhost:6379/0

# Storage (produção)
AWS_ACCESS_KEY_ID=sua_chave
AWS_SECRET_ACCESS_KEY=sua_chave_secreta
AWS_STORAGE_BUCKET_NAME=seu_bucket
```

### **Configuração de Módulos**

```python
# Habilitar/desabilitar módulos dinamicamente
from apps.config.models import AppModuleConfiguration

# Habilitar módulo de mangás
AppModuleConfiguration.objects.filter(
    app_name='mangas'
).update(is_enabled=True)

# Configurar permissões específicas
module = AppModuleConfiguration.objects.get(app_name='articles')
module.required_permissions = ['articles.add_article']
module.save()
```

---

## 🎨 Personalização

### **Temas e Estilos**

O Project Nix utiliza uma paleta moderna baseada em roxo:

```css
:root {
  --primary-color: #6f42c1;
  --secondary-color: #e83e8c;
  --accent-color: #20c997;
  --dark-color: #2d1b69;
  --light-color: #f8f9fa;
}
```

### **Customização de Templates**

```html
<!-- Estender template base -->
{% extends 'base.html' %}
{% load static %}

{% block title %}Minha Página{% endblock %}

{% block content %}
<div class="container">
  <h1 class="text-primary">Conteúdo Personalizado</h1>
</div>
{% endblock %}
```

---

## 🔌 API REST

### **Endpoints Principais**

```bash
# Artigos
GET    /api/articles/              # Listar artigos
POST   /api/articles/              # Criar artigo
GET    /api/articles/{id}/         # Detalhes do artigo
PUT    /api/articles/{id}/         # Atualizar artigo
DELETE /api/articles/{id}/         # Excluir artigo

# Livros
GET    /api/books/                 # Listar livros
POST   /api/books/                 # Adicionar livro
GET    /api/books/{id}/            # Detalhes do livro
GET    /api/books/{id}/progress/   # Progresso de leitura

# Mangás
GET    /api/mangas/                # Listar mangás
GET    /api/mangas/{id}/chapters/  # Capítulos do mangá
GET    /api/chapters/{id}/pages/   # Páginas do capítulo

# Comentários
GET    /api/comments/              # Listar comentários
POST   /api/comments/              # Criar comentário
PUT    /api/comments/{id}/         # Atualizar comentário
DELETE /api/comments/{id}/         # Excluir comentário

# Usuários
GET    /api/users/profile/         # Perfil do usuário
PUT    /api/users/profile/         # Atualizar perfil
GET    /api/users/favorites/       # Favoritos do usuário
```

### **Autenticação**

```python
# Token de acesso
POST /api/auth/login/
{
  "username": "usuario",
  "password": "senha"
}

# Resposta
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}

# Usar token nas requisições
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

---

## 🧪 Testes

### **Executar Testes**

```bash
# Todos os testes
python manage.py test

# Testes específicos
python manage.py test apps.articles
python manage.py test apps.mangas.tests.test_models

# Com cobertura
coverage run --source='.' manage.py test
coverage report -m
coverage html  # Relatório HTML

# Testes de integração
pytest tests/integration/

# Testes de performance
pytest tests/performance/ --benchmark-only
```

### **Estrutura de Testes**

```
tests/
├── unit/           # Testes unitários
├── integration/    # Testes de integração
├── performance/    # Testes de performance
├── fixtures/       # Dados de teste
└── conftest.py     # Configurações pytest
```

---

## 🚀 Deploy

### **Deploy Local (Docker)**

```bash
# Build da imagem
docker build -t project-nix .

# Executar com docker-compose
docker-compose up -d

# Verificar status
docker-compose ps
```

### **Deploy em Produção**

```bash
# Configurar servidor
sudo apt update
sudo apt install python3.11 python3.11-venv postgresql nginx

# Deploy automatizado
bash scripts/deploy_gcp.sh

# Ou deploy manual
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart project-nix
```

### **Monitoramento**

```bash
# Health checks
curl http://localhost:8000/health/
curl http://localhost:8000/health/ready/
curl http://localhost:8000/health/live/

# Logs
tail -f /var/log/project-nix/django.log
sudo journalctl -u project-nix -f
```

---

## 🔒 Segurança

### **Configurações de Segurança**

- ✅ HTTPS obrigatório em produção
- ✅ Rate limiting implementado
- ✅ Validação de entrada rigorosa
- ✅ Proteção CSRF ativa
- ✅ Headers de segurança configurados
- ✅ Sanitização de uploads

### **Backup e Recuperação**

```bash
# Backup do banco
pg_dump project_nix > backup_$(date +%Y%m%d).sql

# Backup de arquivos
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/

# Restore
psql project_nix < backup_20241203.sql
tar -xzf media_backup_20241203.tar.gz
```

---

## 🤝 Contribuição

### **Como Contribuir**

1. **Fork** o repositório
2. **Clone** seu fork: `git clone https://github.com/seu-usuario/project-nix.git`
3. **Branch**: `git checkout -b feature/nova-funcionalidade`
4. **Commit**: `git commit -am 'Adiciona nova funcionalidade'`
5. **Push**: `git push origin feature/nova-funcionalidade`
6. **Pull Request**: Abra um PR descrevendo as mudanças

### **Padrões de Código**

```python
# Seguir PEP 8
black .
flake8 .
isort .

# Testes obrigatórios
python manage.py test

# Documentação
# Docstrings em todas as funções públicas
def minha_funcao(param: str) -> dict:
    """
    Descrição da função.
    
    Args:
        param: Descrição do parâmetro
        
    Returns:
        Descrição do retorno
    """
    pass
```

---

## 📞 Suporte

### **Canais de Suporte**

- 🐛 **Issues**: [GitHub Issues](https://github.com/seu-usuario/project-nix/issues)
- 💬 **Discussões**: [GitHub Discussions](https://github.com/seu-usuario/project-nix/discussions)
- 📧 **Email**: suporte@projectnix.com
- 📖 **Wiki**: [GitHub Wiki](https://github.com/seu-usuario/project-nix/wiki)

### **FAQ**

**Q: Como adicionar um novo tipo de conteúdo?**
A: Crie um novo app Django e registre-o no sistema de módulos.

**Q: É possível usar com outros bancos de dados?**
A: Sim, Django suporta MySQL, SQLite, PostgreSQL e Oracle.

**Q: Como configurar HTTPS?**
A: Configure seu servidor web (Nginx/Apache) com certificados SSL.

---

## 📄 Licença

Este projeto está licenciado sob a **Licença MIT** - veja o arquivo [LICENSE](../LICENSE) para detalhes.

```
MIT License

Copyright (c) 2024 Project Nix

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

## 🎯 Roadmap

### **Versão Atual (v1.0)**
- ✅ Sistema modular completo
- ✅ Arquitetura SOLID
- ✅ API REST
- ✅ Interface responsiva
- ✅ Sistema de comentários unificado

### **Próximas Versões**

**v1.1 - Melhorias de Performance**
- [ ] Cache avançado com Redis
- [ ] Otimização de queries
- [ ] CDN para arquivos estáticos
- [ ] Compressão de imagens automática

**v1.2 - Recursos Sociais**
- [ ] Sistema de seguir usuários
- [ ] Feed personalizado
- [ ] Notificações em tempo real
- [ ] Sistema de reputação

**v1.3 - Integrações**
- [ ] API de terceiros (Goodreads, MyAnimeList)
- [ ] Importação de conteúdo
- [ ] Sincronização com cloud storage
- [ ] Webhooks para eventos

**v2.0 - Mobile e PWA**
- [ ] Progressive Web App
- [ ] App mobile nativo
- [ ] Sincronização offline
- [ ] Push notifications

---

## 🌟 Agradecimentos

Obrigado a todos os contribuidores que tornaram este projeto possível:

- **Comunidade Django** - Framework incrível
- **Bootstrap Team** - Interface moderna
- **Contribuidores** - Melhorias e correções
- **Usuários** - Feedback valioso

---

<div align="center">

**Project Nix** - *Democratizando o acesso ao conteúdo digital* 📚✨

[🏠 Home](http://localhost:8000) • [📖 Docs](README.md) • [🐛 Issues](https://github.com/seu-usuario/project-nix/issues) • [💬 Discussions](https://github.com/seu-usuario/project-nix/discussions)

</div>