# FireFlies - Deploy no Ubuntu

Este guia fornece instruções completas para instalar e fazer deploy do FireFlies no Ubuntu/Debian.

## 🎯 Pré-requisitos

- Ubuntu 20.04+ ou Debian 11+
- Acesso sudo
- Conexão com internet
- Mínimo 2GB RAM
- Mínimo 10GB espaço em disco

## 🚀 Instalação Rápida

### 1. Clone o repositório
```bash
git clone <seu-repositorio>
cd fireflies
```

### 2. Execute o script de instalação
```bash
chmod +x install_ubuntu.sh
./install_ubuntu.sh
```

### 3. Faça logout e login novamente
```bash
# Para aplicar as mudanças do Docker
exit
# Faça login novamente
```

### 4. Execute o deploy
```bash
./deploy.sh
```

## 🌐 Detecção Automática de IP

O sistema detecta automaticamente o IP da sua máquina e configura:

- ✅ **ALLOWED_HOSTS** - Permite acesso via IP local
- ✅ **CSRF_TRUSTED_ORIGINS** - Configuração de segurança
- ✅ **Firewall** - Regras específicas para o IP detectado
- ✅ **Health Checks** - Testa múltiplos endereços

### Métodos de Detecção

1. **Comando `ip route`** (mais moderno)
2. **Comando `hostname -I`** (Ubuntu/Debian)
3. **Comando `ifconfig`** (fallback)
4. **Serviços externos** (apenas se necessário)

### Endereços de Acesso

Após o deploy, a aplicação estará disponível em:
- **Local**: `http://localhost:8000`
- **IP Local**: `http://SEU_IP:8000`
- **Hostname**: `http://SEU_HOSTNAME:8000`

## 📋 Instalação Manual

Se preferir instalar manualmente, siga estes passos:

### 1. Atualizar sistema
```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Instalar Python
```bash
sudo apt install -y python3 python3-pip python3-venv python3-dev
python3 -m pip install --upgrade pip
```

### 3. Instalar Docker
```bash
# Instalar dependências
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Adicionar repositório oficial do Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Iniciar e habilitar Docker
sudo systemctl start docker
sudo systemctl enable docker
```

### 4. Instalar Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 5. Instalar ferramentas adicionais
```bash
sudo apt install -y lsof curl git htop tree jq vim unzip wget net-tools iproute2
```

### 6. Configurar firewall (opcional)
```bash
sudo ufw allow ssh
sudo ufw allow 8000/tcp
sudo ufw allow 8001/tcp
sudo ufw allow 5432/tcp
sudo ufw allow 6379/tcp
echo "y" | sudo ufw enable
```

## 🚀 Deploy

### Deploy Automático
```bash
# Deploy em desenvolvimento (padrão)
./deploy.sh

# Deploy em produção
./deploy.sh --env production

# Verificar pré-requisitos apenas
./deploy.sh --check-only

# Forçar deploy mesmo com erros
./deploy.sh --force
```

### Deploy Manual
```bash
# 1. Instalar dependências Python
pip3 install -r requirements.txt

# 2. Executar migrations
python3 manage.py migrate

# 3. Coletar arquivos estáticos
python3 manage.py collectstatic --noinput

# 4. Inicializar módulos
python3 manage.py shell -c "
from apps.config.models.app_module_config import AppModuleConfiguration
AppModuleConfiguration.initialize_core_modules()
"

# 5. Deploy com Docker
docker-compose -f docker-compose.dev.yml up -d --build
```

## 🔧 Configuração

### Variáveis de Ambiente
O script criará automaticamente um arquivo `.env` com configurações básicas:

```bash
# FireFlies Environment Configuration
ENVIRONMENT=development
DEBUG=true
DJANGO_SETTINGS_MODULE=core.settings

# Machine Information
MACHINE_IP=<detectado-automaticamente>
MACHINE_HOSTNAME=<detectado-automaticamente>

# Database Configuration
DATABASE_ENGINE=sqlite
DATABASE_NAME=db.sqlite3
DEBUG_DATABASE=True

# Security
DJANGO_SECRET_KEY=<gerado-automaticamente>

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Static Files
STATIC_URL=/static/
MEDIA_URL=/media/
STATIC_ROOT=staticfiles/
MEDIA_ROOT=media/

# Network Configuration
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,<SEU_IP>,<SEU_HOSTNAME>
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,http://<SEU_IP>:8000,http://<SEU_HOSTNAME>:8000

# Docker Configuration
DOCKER_COMPOSE_PROJECT_NAME=fireflies
DOCKER_HOST_IP=<SEU_IP>

# Development Server
DJANGO_HOST=0.0.0.0
DJANGO_PORT=8000

# Production Server (Gunicorn)
GUNICORN_BIND=0.0.0.0:8000
GUNICORN_WORKERS=auto
GUNICORN_WORKER_CLASS=sync
GUNICORN_TIMEOUT=30
GUNICORN_LOG_LEVEL=info
```

### Configuração de Banco de Dados

#### SQLite (Padrão)
```bash
# Já configurado automaticamente
```

#### PostgreSQL
```bash
# Instalar PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Criar banco e usuário
sudo -u postgres createdb fireflies
sudo -u postgres createuser fireflies_user
sudo -u postgres psql -c "ALTER USER fireflies_user PASSWORD 'sua_senha';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE fireflies TO fireflies_user;"

# Atualizar .env
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=fireflies
DATABASE_USER=fireflies_user
DATABASE_PASSWORD=sua_senha
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

#### MySQL
```bash
# Instalar MySQL
sudo apt install -y mysql-server mysql-client

# Criar banco e usuário
sudo mysql -e "CREATE DATABASE fireflies;"
sudo mysql -e "CREATE USER 'fireflies_user'@'localhost' IDENTIFIED BY 'sua_senha';"
sudo mysql -e "GRANT ALL PRIVILEGES ON fireflies.* TO 'fireflies_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

# Atualizar .env
DATABASE_ENGINE=django.db.backends.mysql
DATABASE_NAME=fireflies
DATABASE_USER=fireflies_user
DATABASE_PASSWORD=sua_senha
DATABASE_HOST=localhost
DATABASE_PORT=3306
```

## 📊 Monitoramento

### Verificar Status dos Containers
```bash
# Ver containers rodando
docker ps

# Ver logs
docker-compose -f docker-compose.dev.yml logs -f

# Ver logs de um serviço específico
docker-compose -f docker-compose.dev.yml logs -f web
```

### Comandos Úteis
```bash
# Parar todos os containers
docker-compose -f docker-compose.dev.yml down

# Reiniciar containers
docker-compose -f docker-compose.dev.yml restart

# Ver uso de recursos
docker stats

# Limpar recursos não utilizados
docker system prune -f
```

### Verificar Acesso à Aplicação
```bash
# Testar localhost
curl -I http://localhost:8000/

# Testar IP local (substitua pelo seu IP)
curl -I http://SEU_IP:8000/

# Testar hostname
curl -I http://SEU_HOSTNAME:8000/
```

## 🔍 Troubleshooting

### Problemas Comuns

#### 1. Docker não está rodando
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

#### 2. Usuário não tem permissão para Docker
```bash
sudo usermod -aG docker $USER
# Faça logout e login novamente
```

#### 3. Porta já em uso
```bash
# Verificar portas em uso
sudo lsof -i :8000
sudo lsof -i :8001

# Matar processo usando a porta
sudo kill -9 <PID>
```

#### 4. Erro de permissão
```bash
# Dar permissão aos scripts
chmod +x deploy.sh
chmod +x docker/entrypoint.sh
chmod +x docker/start.sh
```

#### 5. Erro de memória insuficiente
```bash
# Aumentar swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

#### 6. Problemas de rede/ACESSO
```bash
# Verificar se o IP foi detectado corretamente
./deploy.sh --check-only

# Verificar configurações de rede
cat .env | grep -E "(MACHINE_IP|ALLOWED_HOSTS|CSRF_TRUSTED_ORIGINS)"

# Testar conectividade
ping -c 3 SEU_IP
```

### Logs de Erro

#### Ver logs do Django
```bash
docker-compose -f docker-compose.dev.yml logs web
```

#### Ver logs do banco de dados
```bash
docker-compose -f docker-compose.dev.yml logs db
```

#### Ver logs do Redis
```bash
docker-compose -f docker-compose.dev.yml logs redis
```

## 🚀 Produção

### Configurações de Produção

1. **Alterar ambiente:**
   ```bash
   ENVIRONMENT=production
   DEBUG=false
   ```

2. **Configurar HTTPS:**
   ```bash
   SECURE_SSL_REDIRECT=true
   SECURE_HSTS_SECONDS=31536000
   ```

3. **Configurar backup:**
   ```bash
   BACKUP_ENABLED=true
   BACKUP_RETENTION_DAYS=30
   ```

4. **Configurar monitoramento:**
   ```bash
   SENTRY_DSN=sua_dsn_do_sentry
   ```

### Deploy em Produção
```bash
# Deploy em produção
./deploy.sh --env production

# Verificar saúde
curl -f http://localhost:8000/health/

# Ver logs
docker-compose logs -f
```

## 🌐 Configuração de Rede Avançada

### Acesso Externo

Para permitir acesso de outras máquinas na rede:

1. **Verificar IP da máquina:**
   ```bash
   ip route get 1.1.1.1 | grep -oP 'src \K\S+'
   ```

2. **Configurar firewall:**
   ```bash
   # Permitir acesso da rede local
   sudo ufw allow from 192.168.1.0/24 to any port 8000
   sudo ufw allow from 192.168.1.0/24 to any port 8001
   ```

3. **Atualizar ALLOWED_HOSTS:**
   ```bash
   # Adicionar IP da rede local ao .env
   echo "ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,SEU_IP,SEU_HOSTNAME,192.168.1.0/24" >> .env
   ```

### Proxy Reverso (Nginx)

Para usar com proxy reverso:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /caminho/para/staticfiles/;
    }

    location /media/ {
        alias /caminho/para/media/;
    }
}
```

## 📚 Recursos Adicionais

- [Documentação do Django](https://docs.djangoproject.com/)
- [Documentação do Docker](https://docs.docker.com/)
- [Documentação do Ubuntu](https://ubuntu.com/tutorials)
- [Guia de Segurança do Ubuntu](https://ubuntu.com/security)
- [Configuração de Rede Ubuntu](https://ubuntu.com/server/docs/network-configuration)

## 🤝 Suporte

Se encontrar problemas:

1. Verifique os logs: `docker-compose logs -f`
2. Execute verificação: `./deploy.sh --check-only`
3. Verifique configurações de rede: `cat .env | grep -E "(MACHINE_IP|ALLOWED_HOSTS)"`
4. Consulte a documentação
5. Abra uma issue no repositório

---

**FireFlies** - Sistema de gerenciamento de conteúdo moderno 🚀

**Funcionalidades de Rede:**
- 🔍 Detecção automática de IP
- 🌐 Configuração automática de ALLOWED_HOSTS
- 🔒 Configuração automática de CSRF_TRUSTED_ORIGINS
- 🚀 Deploy automatizado com Docker
- 📊 Health checks em múltiplos endereços 