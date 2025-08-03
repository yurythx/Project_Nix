# 📚 Project Nix

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/django-5.2-brightgreen)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

> **Plataforma Completa de Gerenciamento de Conteúdo Digital**

Uma plataforma moderna e modular para centralizar diferentes tipos de conteúdo digital: livros, artigos, mangás, audiolivros e páginas dinâmicas. Desenvolvida com Django 5.2 e arquitetura SOLID para máxima escalabilidade e manutenibilidade.

## 📌 Índice

- [🚀 Características](#-características)
- [📋 Pré-requisitos](#-pré-requisitos)
- [🛠️ Instalação Rápida](#️-instalação-rápida)
- [🌍 Ambientes](#-ambientes)
- [📁 Estrutura do Projeto](#-estrutura-do-projeto)
- [🏗️ Arquitetura](#️-arquitetura)
- [🔧 Configuração](#-configuração)
- [🚀 Deploy](#-deploy-em-produção)
- [🧪 Testes](#-testes)
- [🤝 Como Contribuir](#-como-contribuir)
- [📄 Licença](#-licença)
- [📞 Suporte](#-suporte)

## 🚀 Características

### 🎯 **Propósito Principal**
**Democratizar o acesso a conteúdo digital diversificado** através de uma plataforma unificada que centraliza diferentes tipos de mídia e oferece uma experiência moderna e responsiva.

### 📚 **Tipos de Conteúdo Suportados**
- 📖 **Livros Digitais**: E-books em PDF/EPUB com leitor integrado
- 📰 **Artigos e Blog**: Sistema completo de publicação com categorias e tags
- 🎌 **Mangás e Quadrinhos**: Leitor otimizado com navegação por capítulos
- 🎧 **Audiolivros**: Reprodução de conteúdo sonoro com controle de progresso
- 📄 **Páginas Dinâmicas**: Conteúdo institucional e informativo
- 💬 **Sistema Social**: Comentários, favoritos e interações entre usuários

### 🔌 **Módulos do Sistema**
- **Accounts**: Autenticação, perfis e gerenciamento de usuários
- **Articles**: Publicação e gerenciamento de artigos com SEO otimizado
- **Books**: Biblioteca digital com progresso de leitura
- **Audiobooks**: Reprodutor de audiolivros com bookmarks
- **Mangas**: Leitor de mangás com suporte a volumes e capítulos
- **Pages**: CMS para páginas estáticas e dinâmicas
- **Comments**: Sistema unificado de comentários para todos os conteúdos
- **Config**: Painel administrativo e configurações modulares

### 🛠️ Tecnologias
- **Backend**: Django 5.2, Django REST Framework
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Banco de Dados**: PostgreSQL (produção), SQLite (desenvolvimento)
- **Cache**: Redis (opcional)
- **Ferramentas**: Docker, Gunicorn, Nginx

### ✨ **Funcionalidades Principais**

#### 🎨 **Interface e Experiência**
- **Design Responsivo**: Interface moderna que se adapta a qualquer dispositivo
- **Tema Elegante**: Paleta roxa moderna com suporte a modo claro/escuro
- **Navegação Intuitiva**: UX otimizada para diferentes tipos de conteúdo
- **Leitores Especializados**: Interfaces dedicadas para cada tipo de mídia

#### 🔧 **Recursos Técnicos**
- **Sistema Modular**: Módulos podem ser habilitados/desabilitados dinamicamente
- **Arquitetura SOLID**: Padrões de design modernos com injeção de dependências
- **API REST Completa**: Endpoints para integração e desenvolvimento mobile
- **Cache Inteligente**: Sistema de cache para otimização de performance
- **SEO Otimizado**: Meta tags, sitemaps e URLs amigáveis

#### 👥 **Recursos Sociais**
- **Sistema de Usuários**: Perfis completos com histórico de leitura
- **Comentários Unificados**: Sistema de comentários para todos os tipos de conteúdo
- **Favoritos e Bookmarks**: Salvar e organizar conteúdo preferido
- **Progresso de Leitura**: Acompanhamento automático do progresso
- **Recomendações**: Sugestões baseadas no histórico do usuário

#### ⚙️ **Administração**
- **Painel Administrativo**: Interface completa de gerenciamento
- **Setup Wizard**: Configuração inicial guiada passo a passo
- **Moderação de Conteúdo**: Ferramentas para moderação e controle de qualidade
- **Analytics**: Estatísticas de uso e engagement
- **Backup Automático**: Sistema de backup e recuperação

## 📋 Pré-requisitos

- Python 3.11+
- PostgreSQL 12+
- Redis (opcional, para cache)
- Git

## 🛠️ Instalação Rápida

### 1. Clone o repositório
```bash
git clone <repository-url>
cd project-nix
```

### 2. Configurar ambiente virtual
```bash
python3.11 -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate     # Windows
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

### 5. Configurar banco de dados
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 6. Criar superusuário
```bash
python manage.py createsuperuser
```

### 7. Executar servidor
```bash
python manage.py runserver
```

## 🌍 Ambientes

### Development
```bash
# Configurar para desenvolvimento
export ENVIRONMENT=development
export DEBUG=True
python manage.py runserver
```

### Production
```bash
# Configurar para produção
export ENVIRONMENT=production
export DEBUG=False
python manage.py runserver
```

## 📁 Estrutura do Projeto

```
project-nix/
├── apps/                    # Aplicações Django
│   ├── accounts/           # Sistema de usuários e autenticação
│   ├── articles/           # Sistema de artigos e comentários
│   ├── config/             # Configurações e módulos
│   └── pages/              # Páginas estáticas e navegação
├── core/                   # Configurações Django
│   ├── factories.py        # Factory pattern para injeção de dependências
│   ├── observers.py        # Observer pattern para eventos
│   ├── settings.py         # Configurações principais
│   └── urls.py            # URLs principais
├── static/                 # Arquivos estáticos
├── media/                  # Uploads
├── docs/                   # Documentação
├── scripts/                # Scripts de deploy
└── requirements.txt        # Dependências Python
```

## 🏗️ Arquitetura

### Padrões SOLID Implementados

#### 1. Service Factory (Injeção de Dependências)
```python
from core.factories import service_factory

# Obter serviços com dependências injetadas
article_service = service_factory.create_article_service()
user_service = service_factory.create_user_service()
```

#### 2. Observer Pattern (Eventos)
```python
from core.observers import event_dispatcher

def on_article_created(article):
    print(f"Novo artigo: {article.title}")

# Inscrever para eventos
event_dispatcher.subscribe('article_created', on_article_created)

# Disparar eventos
event_dispatcher.notify('article_created', article)
```

### Módulos do Sistema

#### Accounts (Sistema de Usuários)
- Autenticação e registro
- Perfis de usuário
- Controle de permissões
- Middleware de segurança

#### Articles (Sistema de Conteúdo)
- Gestão de artigos
- Categorias e tags
- Sistema de comentários
- SEO otimizado

#### Config (Painel Administrativo)
- Setup wizard
- Gerenciamento de módulos
- Configurações de email
- Monitoramento do sistema

#### Pages (Páginas Estáticas)
- Páginas dinâmicas
- Sistema de navegação
- SEO e meta tags
- Templates flexíveis

## 🔧 Configuração

### Variáveis de Ambiente (.env)
```env
# Ambiente
ENVIRONMENT=development
DEBUG=True

# Banco de dados
DB_ENGINE=django.db.backends.postgresql
DB_NAME=project_nix
DB_USER=project_nix_user
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu_email@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_de_app

# Segurança
SECRET_KEY=sua_chave_secreta
ALLOWED_HOSTS=localhost,127.0.0.1

# Módulos ativos
ACTIVE_MODULES=accounts,config,pages,articles
```

### Configuração de Módulos
```python
# Habilitar/desabilitar módulos
python manage.py shell -c "
from apps.config.models.app_module_config import AppModuleConfiguration
AppModuleConfiguration.objects.filter(app_name='articles').update(is_enabled=True)
"
```

## 🧪 Testes

### Executando Testes
```bash
# Executar todos os testes
python manage.py test

# Executar testes de um app específico
python manage.py test apps.accounts

# Executar testes com cobertura
coverage run --source='.' manage.py test
coverage report -m

# Executar testes de integração
pytest tests/integration/
```

### Boas Práticas de Testes
1. **Testes Unitários**: Teste cada função/método isoladamente
2. **Testes de Integração**: Teste a interação entre componentes
3. **Testes de API**: Use o Django REST Framework test client
4. **Fixtures**: Use fixtures para dados de teste consistentes
5. **Mocks**: Use mocks para dependências externas

## 🚀 Deploy em Produção

### Deploy Manual
```bash
# 1. Configurar servidor
sudo apt update
sudo apt install python3.11 python3.11-venv postgresql nginx

# 2. Configurar banco
sudo -u postgres createdb project_nix
sudo -u postgres createuser project_nix_user

# 3. Deploy da aplicação
git clone <repository>
cd project-nix
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configurar Django
python manage.py migrate
python manage.py collectstatic --noinput

# 5. Configurar Gunicorn
pip install gunicorn
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

### Deploy Automatizado (Google Cloud)
```bash
# Conectar via SSH na VM
ssh usuario@IP_DA_VM

# Executar script de deploy
bash scripts/deploy_gcp.sh

# Configuração avançada
bash scripts/post_deploy_setup.sh
```

## 📊 Monitoramento

### Health Checks
```bash
# Verificar saúde da aplicação
curl http://localhost:8000/health/

# Verificar readiness
curl http://localhost:8000/health/ready/

# Verificar liveness
curl http://localhost:8000/health/live/
```

### Logs
```bash
# Logs do Django
tail -f /var/log/fireflies/django.log

# Logs do sistema
sudo journalctl -u fireflies -f

# Logs do Nginx
sudo tail -f /var/log/nginx/error.log
```

## 🔒 Segurança

### Configurações de Segurança
- Middleware de segurança configurado
- Rate limiting implementado
- Controle de acesso por módulos
- Validação de formulários
- Proteção CSRF ativa

### Backup
```bash
# Backup do banco
pg_dump fireflies > backup.sql

# Backup dos arquivos
tar -czf media_backup.tar.gz media/

# Restore
psql fireflies < backup.sql
```

## 🧪 Testes

```bash
# Executar todos os testes
python manage.py test

# Testes com cobertura
python -m pytest --cov

# Testes específicos
python manage.py test apps.accounts
python manage.py test apps.articles
```

## 🛠️ Comandos Úteis

### Desenvolvimento
```bash
# Rodar servidor
python manage.py runserver

# Shell do Django
python manage.py shell

# Criar migrações
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Coletar estáticos
python manage.py collectstatic --noinput
```

### Administração
```bash
# Criar superusuário
python manage.py createsuperuser

# Setup wizard
python manage.py setup_wizard

# Inicializar módulos
python manage.py init_modules

# Verificar configurações
python manage.py check
```

### Deploy
```bash
# Deploy completo
make deploy

# Verificar status
make status

# Logs
make logs

# Backup
make backup
```

## 🔍 Troubleshooting

### Problemas Comuns

1. **Módulos não carregam**
   ```bash
   python manage.py init_modules
   ```

2. **Erro de permissões**
   ```bash
   sudo chown -R www-data:www-data /path/to/fireflies
   ```

3. **Banco não conecta**
   ```bash
   python manage.py check --database default
   ```

4. **Arquivos estáticos não carregam**
   ```bash
   python manage.py collectstatic --noinput
   ```

### Diagnóstico Completo
```bash
# Executar script de troubleshooting
bash scripts/troubleshooting.sh
```

## 📚 Documentação

### 📖 **Documentação Principal**
- [**📚 Documentação Completa**](docs/README.md) - Guia completo da plataforma
- [🚀 Início Rápido](docs/README.md#-início-rápido) - Instalação e configuração
- [🔧 Configuração Avançada](docs/README.md#-configuração-avançada) - Personalização e otimização
- [🔌 API REST](docs/README.md#-api-rest) - Documentação da API
- [🧪 Testes](docs/README.md#-testes) - Guia de testes e qualidade
- [🚀 Deploy](docs/README.md#-deploy) - Guias de implantação

### 🎯 **Guias Específicos**
- [👥 Sistema de Usuários](docs/README.md#para-administradores) - Gerenciamento de usuários
- [📝 Criação de Conteúdo](docs/README.md#para-criadores-de-conteúdo) - Guias para criadores
- [🔧 Desenvolvimento](docs/README.md#para-desenvolvedores) - Extensão e customização
- [🎨 Personalização](docs/README.md#-personalização) - Temas e estilos
- [🔒 Segurança](docs/README.md#-segurança) - Configurações de segurança

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Suporte

Para suporte, por favor abra uma issue no nosso [repositório](https://github.com/seu-usuario/project-nix).

### 🌟 **Visão e Missão**

**Missão**: Democratizar o acesso a conteúdo digital de qualidade através de uma plataforma unificada, moderna e acessível.

**Visão**: Ser a principal plataforma de referência para criadores e consumidores de conteúdo digital diversificado.

### 🎯 **Roadmap 2024-2025**

#### **Q1 2024 - Fundação Sólida** ✅
- ✅ Arquitetura modular SOLID
- ✅ Sistema de usuários completo
- ✅ Leitores especializados (livros, mangás, artigos)
- ✅ API REST funcional
- ✅ Interface responsiva

#### **Q2 2024 - Recursos Sociais**
- [ ] Sistema de seguir usuários e criadores
- [ ] Feed personalizado de conteúdo
- [ ] Notificações em tempo real
- [ ] Sistema de reputação e badges
- [ ] Grupos e comunidades temáticas

#### **Q3 2024 - Performance e Escala**
- [ ] Cache avançado com Redis
- [ ] CDN para arquivos estáticos
- [ ] Otimização de queries e performance
- [ ] Compressão automática de imagens
- [ ] Sistema de backup automático

#### **Q4 2024 - Integrações**
- [ ] API de terceiros (Goodreads, MyAnimeList)
- [ ] Importação automática de conteúdo
- [ ] Sincronização com cloud storage
- [ ] Webhooks para eventos
- [ ] Sistema de plugins

#### **2025 - Mobile e Expansão**
- [ ] Progressive Web App (PWA)
- [ ] Aplicativo mobile nativo
- [ ] Sincronização offline
- [ ] Push notifications
- [ ] Marketplace de conteúdo

---

<div align="center">

**Project Nix** - *Democratizando o acesso ao conteúdo digital* 📚✨

*Uma plataforma. Todo o conteúdo. Experiência unificada.*

[🏠 Acessar Plataforma](http://localhost:8000) • [📖 Documentação](docs/README.md) • [🐛 Reportar Bug](https://github.com/seu-usuario/project-nix/issues) • [💬 Comunidade](https://github.com/seu-usuario/project-nix/discussions)

</div>
