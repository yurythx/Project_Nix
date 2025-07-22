# 🌟 Project Nix

Um sistema de gerenciamento de conteúdo moderno, modular e responsivo, com design elegante em paleta roxa. Desenvolvido com Django e arquitetura SOLID.

## 🚀 Características

- **Sistema Modular**: Módulos dinâmicos que podem ser habilitados/desabilitados
- **Arquitetura SOLID**: Padrões de design modernos com injeção de dependências
- **Tema Responsivo**: Interface moderna com suporte a temas claro/escuro
- **Painel Administrativo**: Sistema completo de configuração e gerenciamento
- **Sistema de Usuários**: Autenticação, perfis e controle de permissões
- **Gestão de Conteúdo**: Artigos, páginas estáticas e comentários
- **Setup Wizard**: Configuração inicial guiada
- **Health Checks**: Monitoramento de saúde da aplicação
- **Deploy Automatizado**: Scripts para deploy em produção

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
├── templates/              # Templates globais
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

- [Guia de Deploy](docs/DEPLOY_GCP_GUIDE.md)
- [Arquitetura SOLID](docs/SOLID_PATTERNS_GUIDE.md)
- [Sistema de Módulos](docs/INTERFACES_DOCUMENTATION.md)
- [Setup Wizard](docs/SETUP_WIZARD_GUIDE.md)
- [Factory e Observer](docs/FACTORY_OBSERVER_GUIDE.md)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🆘 Suporte

- **Issues**: [GitHub Issues](https://github.com/seu-usuario/fireflies/issues)
- **Documentação**: [Wiki](https://github.com/seu-usuario/fireflies/wiki)
- **Email**: suporte@fireflies.com

## 🎯 Roadmap

- [ ] Sistema de notificações em tempo real
- [ ] API REST completa
- [ ] Integração com CDN
- [ ] Sistema de plugins
- [ ] Dashboard de analytics
- [ ] Backup automático para cloud
- [ ] Integração com Kubernetes

---

**Project Nix** - Gerenciamento de conteúdo com design elegante e moderno ✨
