# 🚀 Sistema de Deploy Atual - FireFlies CMS

## 📋 Visão Geral

O FireFlies CMS possui um sistema de deploy robusto e automatizado, preparado para diferentes ambientes (desenvolvimento, staging e produção). O sistema inclui scripts automatizados, configurações de ambiente e monitoramento completo.

## 🎯 Características do Deploy

### ✅ Funcionalidades Implementadas

- **Deploy Automatizado**: Scripts para Google Cloud VM
- **Configuração de Ambiente**: Detecção automática de ambiente
- **Health Checks**: Verificação de saúde da aplicação
- **SSL Automático**: Configuração com Certbot
- **Monitoramento**: Logs estruturados e métricas
- **Backup**: Sistema de backup automático
- **Segurança**: Configurações de segurança otimizadas
- **Performance**: Otimizações para produção

## 🏗️ Arquitetura de Deploy

### Stack Tecnológica

```
┌─────────────────────────────────────┐
│           Nginx (Proxy)             │
│         Porta 80/443               │
├─────────────────────────────────────┤
│         Gunicorn (WSGI)            │
│         Porta 8000                 │
├─────────────────────────────────────┤
│         Django (Application)        │
│         FireFlies CMS              │
├─────────────────────────────────────┤
│         PostgreSQL (Database)       │
│         Porta 5432                 │
├─────────────────────────────────────┤
│         Redis (Cache)               │
│         Porta 6379                 │
└─────────────────────────────────────┘
```

### Componentes do Sistema

#### 1. Servidor Web (Nginx)
- Proxy reverso
- Servir arquivos estáticos
- Compressão gzip
- SSL/TLS
- Rate limiting

#### 2. Servidor WSGI (Gunicorn)
- Múltiplos workers
- Timeout configurado
- Logs estruturados
- Process management

#### 3. Aplicação Django
- Configurações otimizadas
- Cache Redis
- Logs estruturados
- Health checks

#### 4. Banco de Dados (PostgreSQL)
- Conexões persistentes
- Backup automático
- Otimizações de performance

#### 5. Cache (Redis)
- Cache de sessões
- Cache de consultas
- Cache de templates

## 📁 Scripts de Deploy

### 1. Deploy Principal (Google Cloud)

```bash
# scripts/deploy_gcp.sh
#!/bin/bash

# Configurações
PROJECT_NAME="fireflies"
DB_NAME="fireflies"
DB_USER="fireflies_user"
DB_PASSWORD="$(openssl rand -base64 32)"

echo "🚀 Iniciando deploy do FireFlies CMS..."

# 1. Atualizar sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar dependências
sudo apt install -y python3.11 python3.11-venv python3.11-dev \
    postgresql postgresql-contrib nginx redis-server \
    certbot python3-certbot-nginx curl git

# 3. Configurar PostgreSQL
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# 4. Configurar usuário deploy
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG sudo deploy

# 5. Clonar repositório
sudo mkdir -p /var/www
cd /var/www
sudo git clone <repository-url> $PROJECT_NAME
sudo chown -R deploy:deploy $PROJECT_NAME

# 6. Configurar ambiente virtual
cd $PROJECT_NAME
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 7. Configurar variáveis de ambiente
cat > .env << EOF
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=$(openssl rand -base64 50)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
ALLOWED_HOSTS=localhost,127.0.0.1
ACTIVE_MODULES=accounts,config,pages,articles
EOF

# 8. Configurar Django
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser --noinput

# 9. Configurar Gunicorn
sudo tee /etc/systemd/system/project-nix.service > /dev/null << EOF
[Unit]
Description=Project Nix CMS
After=network.target

[Service]
User=deploy
Group=deploy
WorkingDirectory=/var/www/$PROJECT_NAME
Environment=PATH=/var/www/$PROJECT_NAME/venv/bin
ExecStart=/var/www/$PROJECT_NAME/venv/bin/gunicorn core.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile /var/log/fireflies/access.log \
    --error-logfile /var/log/fireflies/error.log

[Install]
WantedBy=multi-user.target
EOF

# 10. Configurar Nginx
sudo tee /etc/nginx/sites-available/fireflies > /dev/null << EOF
server {
    listen 80;
    server_name _;

    client_max_body_size 100M;

    location /static/ {
        alias /var/www/$PROJECT_NAME/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/$PROJECT_NAME/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }
}
EOF

# 11. Ativar configuração
sudo ln -sf /etc/nginx/sites-available/fireflies /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 12. Criar diretórios de log
sudo mkdir -p /var/log/fireflies
sudo chown -R deploy:deploy /var/log/fireflies

# 13. Iniciar serviços
sudo systemctl daemon-reload
sudo systemctl enable fireflies
sudo systemctl start fireflies
sudo systemctl restart nginx

# 14. Configurar SSL (se domínio configurado)
if [ ! -z "$DOMAIN" ]; then
    sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL
fi

echo "✅ Deploy concluído com sucesso!"
echo "🌐 Acesse: http://$(curl -s ifconfig.me)"
echo "🔧 Painel admin: http://$(curl -s ifconfig.me)/admin/"
```

### 2. Configuração Pós-Deploy

```bash
# scripts/post_deploy_setup.sh
#!/bin/bash

echo "🔧 Configurando sistema pós-deploy..."

# 1. Monitoramento avançado
sudo apt install -y sysstat htop iotop

# 2. Backup avançado
sudo mkdir -p /var/backups/fireflies
sudo tee /etc/cron.daily/fireflies-backup > /dev/null << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/fireflies"
PROJECT_DIR="/var/www/fireflies"

# Backup do banco
sudo -u postgres pg_dump fireflies > $BACKUP_DIR/db_backup_$DATE.sql

# Backup dos arquivos
tar -czf $BACKUP_DIR/files_backup_$DATE.tar.gz -C $PROJECT_DIR media/

# Limpar backups antigos (manter últimos 7 dias)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup realizado: $DATE" >> /var/log/fireflies/backup.log
EOF

sudo chmod +x /etc/cron.daily/fireflies-backup

# 3. Segurança avançada
sudo apt install -y fail2ban ufw

# Configurar firewall
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# Configurar fail2ban
sudo tee /etc/fail2ban/jail.local > /dev/null << EOF
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3
EOF

sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# 4. Logs estruturados
sudo tee /etc/logrotate.d/fireflies > /dev/null << EOF
/var/log/fireflies/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 deploy deploy
    postrotate
        systemctl reload fireflies
    endscript
}
EOF

# 5. Otimizações de performance
sudo tee /etc/sysctl.conf > /dev/null << EOF
# Otimizações de rede
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 65535

# Otimizações de memória
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
EOF

sudo sysctl -p

echo "✅ Configuração pós-deploy concluída!"
```

### 3. Script de Troubleshooting

```bash
# scripts/troubleshooting.sh
#!/bin/bash

echo "🔍 Iniciando diagnóstico do sistema..."

# Funções de verificação
check_service() {
    local service=$1
    if systemctl is-active --quiet $service; then
        echo "✅ $service: ATIVO"
    else
        echo "❌ $service: INATIVO"
        systemctl status $service --no-pager
    fi
}

check_port() {
    local port=$1
    local service=$2
    if netstat -tuln | grep -q ":$port "; then
        echo "✅ Porta $port ($service): ABERTA"
    else
        echo "❌ Porta $port ($service): FECHADA"
    fi
}

check_file() {
    local file=$1
    local description=$2
    if [ -f "$file" ]; then
        echo "✅ $description: EXISTE"
    else
        echo "❌ $description: NÃO EXISTE"
    fi
}

# Verificações do sistema
echo "📊 Status dos Serviços:"
check_service fireflies
check_service nginx
check_service postgresql
check_service redis-server

echo ""
echo "🌐 Verificação de Portas:"
check_port 80 "HTTP"
check_port 443 "HTTPS"
check_port 8000 "Gunicorn"
check_port 5432 "PostgreSQL"
check_port 6379 "Redis"

echo ""
echo "📁 Verificação de Arquivos:"
check_file "/var/www/fireflies/manage.py" "Aplicação Django"
check_file "/var/www/fireflies/.env" "Variáveis de ambiente"
check_file "/etc/nginx/sites-enabled/fireflies" "Configuração Nginx"
check_file "/etc/systemd/system/fireflies.service" "Serviço systemd"

echo ""
echo "🔍 Verificação de Logs:"
if [ -f "/var/log/fireflies/error.log" ]; then
    echo "Últimos erros do Gunicorn:"
    tail -5 /var/log/fireflies/error.log
else
    echo "❌ Log de erros não encontrado"
fi

if [ -f "/var/log/nginx/error.log" ]; then
    echo "Últimos erros do Nginx:"
    tail -5 /var/log/nginx/error.log
else
    echo "❌ Log de erros do Nginx não encontrado"
fi

echo ""
echo "💾 Verificação do Banco de Dados:"
if sudo -u postgres psql -d fireflies -c "SELECT version();" > /dev/null 2>&1; then
    echo "✅ Conexão com PostgreSQL: OK"
    echo "📊 Tabelas do Django:"
    sudo -u postgres psql -d fireflies -c "\dt" 2>/dev/null || echo "❌ Erro ao listar tabelas"
else
    echo "❌ Conexão com PostgreSQL: FALHOU"
fi

echo ""
echo "🌐 Teste de Conectividade:"
if curl -s http://localhost/health/ > /dev/null; then
    echo "✅ Health check: OK"
else
    echo "❌ Health check: FALHOU"
fi

echo ""
echo "📈 Informações do Sistema:"
echo "CPU: $(nproc) cores"
echo "RAM: $(free -h | grep Mem | awk '{print $2}')"
echo "Disco: $(df -h / | tail -1 | awk '{print $4}') livre"
echo "Uptime: $(uptime -p)"

echo ""
echo "🔧 Comandos Úteis:"
echo "Ver logs em tempo real: sudo journalctl -u fireflies -f"
echo "Reiniciar aplicação: sudo systemctl restart fireflies"
echo "Verificar configuração: sudo nginx -t"
echo "Acessar logs: sudo tail -f /var/log/fireflies/error.log"
```

## 🔧 Configurações de Ambiente

### Variáveis de Ambiente (.env)

```bash
# Ambiente
ENVIRONMENT=production
DEBUG=False

# Django
SECRET_KEY=sua_chave_secreta_muito_longa
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com,localhost,127.0.0.1

# Banco de dados
DB_ENGINE=django.db.backends.postgresql
DB_NAME=project_nix
DB_USER=project_nix_user
DB_PASSWORD=sua_senha_segura
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_de_app
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

# Cache
REDIS_URL=redis://localhost:6379/1
CACHE_BACKEND=django.core.cache.backends.redis.RedisCache
CACHE_LOCATION=redis://127.0.0.1:6379/1

# Módulos
ACTIVE_MODULES=accounts,config,pages,articles

# Performance
CONN_MAX_AGE=600
STATIC_ROOT=/var/www/project-nix/staticfiles
MEDIA_ROOT=/var/www/project-nix/media

# Segurança
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS=DENY
```

### Configurações do Gunicorn

```python
# gunicorn.conf.py
import multiprocessing

# Configurações do servidor
bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 2

# Configurações de logging
accesslog = "/var/log/fireflies/access.log"
errorlog = "/var/log/fireflies/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Configurações de segurança
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Configurações de performance
preload_app = True
worker_tmp_dir = "/dev/shm"
```

### Configurações do Nginx

```nginx
# /etc/nginx/sites-available/fireflies
upstream fireflies {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;
    
    # Configurações de segurança
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Configurações de performance
    client_max_body_size 100M;
    client_body_timeout 60s;
    client_header_timeout 60s;
    
    # Arquivos estáticos
    location /static/ {
        alias /var/www/fireflies/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Arquivos de mídia
    location /media/ {
        alias /var/www/fireflies/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Health checks
    location /health/ {
        proxy_pass http://fireflies;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        access_log off;
    }
    
    # Aplicação principal
    location / {
        proxy_pass http://fireflies;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

# Configuração SSL (se aplicável)
server {
    listen 443 ssl http2;
    server_name seu-dominio.com www.seu-dominio.com;
    
    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;
    
    # Configurações SSL otimizadas
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Mesma configuração do servidor HTTP
    location /static/ {
        alias /var/www/fireflies/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    location /media/ {
        alias /var/www/fireflies/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    location /health/ {
        proxy_pass http://fireflies;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        access_log off;
    }
    
    location / {
        proxy_pass http://fireflies;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

# Redirecionamento HTTP para HTTPS
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;
    return 301 https://$server_name$request_uri;
}
```

## 📊 Monitoramento e Health Checks

### Health Checks Implementados

```python
# core/health_check.py
from django.http import JsonResponse
from django.utils import timezone
from django.db import connection
from django.core.cache import cache
import psutil
import os

def health_check(request):
    """Health check completo do sistema"""
    checks = {
        'database': check_database(),
        'cache': check_cache(),
        'static_files': check_static_files(),
        'modules': check_modules(),
        'disk_space': check_disk_space(),
        'memory': check_memory(),
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return JsonResponse({
        'status': 'healthy' if all_healthy else 'unhealthy',
        'checks': checks,
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0',
    }, status=status_code)

def check_database():
    """Verifica conexão com banco de dados"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return True
    except Exception:
        return False

def check_cache():
    """Verifica conexão com cache"""
    try:
        cache.set('health_check', 'ok', 10)
        return cache.get('health_check') == 'ok'
    except Exception:
        return False

def check_static_files():
    """Verifica se arquivos estáticos estão acessíveis"""
    static_root = settings.STATIC_ROOT
    return os.path.exists(static_root) and os.access(static_root, os.R_OK)

def check_modules():
    """Verifica se módulos principais estão ativos"""
    try:
        from apps.config.models.app_module_config import AppModuleConfiguration
        core_modules = AppModuleConfiguration.objects.filter(is_core=True)
        return all(module.is_enabled for module in core_modules)
    except Exception:
        return False

def check_disk_space():
    """Verifica espaço em disco"""
    try:
        stat = os.statvfs('/')
        free_space = stat.f_frsize * stat.f_bavail
        return free_space > 1024 * 1024 * 1024  # 1GB mínimo
    except Exception:
        return False

def check_memory():
    """Verifica uso de memória"""
    try:
        memory = psutil.virtual_memory()
        return memory.percent < 90  # Menos de 90% de uso
    except Exception:
        return True  # Se não conseguir verificar, assume OK

def readiness_check(request):
    """Verificação de readiness para Kubernetes"""
    return health_check(request)

def liveness_check(request):
    """Verificação de liveness para Kubernetes"""
    return JsonResponse({'status': 'alive'})
```

## 🔒 Segurança

### Configurações de Segurança

```python
# core/security.py
SECURITY_CONFIG = {
    'MIDDLEWARE': [
        'django.middleware.security.SecurityMiddleware',
        'apps.accounts.middleware.RateLimitMiddleware',
        'apps.accounts.middleware.AccessControlMiddleware',
    ],
    
    'SECURE_SETTINGS': {
        'SECURE_BROWSER_XSS_FILTER': True,
        'SECURE_CONTENT_TYPE_NOSNIFF': True,
        'SECURE_HSTS_INCLUDE_SUBDOMAINS': True,
        'SECURE_HSTS_SECONDS': 31536000,
        'SECURE_REDIRECT_EXEMPT': [],
        'SECURE_SSL_HOST': None,
        'SECURE_SSL_REDIRECT': True,
        'SESSION_COOKIE_SECURE': True,
        'CSRF_COOKIE_SECURE': True,
        'X_FRAME_OPTIONS': 'DENY',
    },
    
    'RATE_LIMITING': {
        'LOGIN_ATTEMPTS': 5,
        'WINDOW_MINUTES': 15,
        'API_RATE_LIMIT': 100,
        'API_WINDOW_MINUTES': 60,
    },
    
    'PASSWORD_POLICY': {
        'MIN_LENGTH': 8,
        'REQUIRE_UPPERCASE': True,
        'REQUIRE_LOWERCASE': True,
        'REQUIRE_NUMBERS': True,
        'REQUIRE_SPECIAL': True,
    },
}
```

### Firewall e Fail2ban

```bash
# Configuração do UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Configuração do Fail2ban
sudo tee /etc/fail2ban/jail.local > /dev/null << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
port = http,https
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 3
EOF
```

## 📈 Performance

### Otimizações Implementadas

```python
# core/performance.py
PERFORMANCE_CONFIG = {
    'DATABASE': {
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'MAX_CONNS': 20,
            'CONN_HEALTH_CHECKS': True,
        }
    },
    
    'CACHE': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'TIMEOUT': 300,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        }
    },
    
    'STATIC_FILES': {
        'COMPRESS': True,
        'CACHE': True,
        'CDN': False,
        'MANIFEST_STORAGE': 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage',
    },
    
    'TEMPLATES': {
        'CACHE': True,
        'OPTIMIZE': True,
        'LOADERS': [
            ('django.template.loaders.cached.Loader', [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ]),
        ],
    },
    
    'MIDDLEWARE': [
        'django.middleware.cache.UpdateCacheMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.cache.FetchFromCacheMiddleware',
    ],
}
```

## 🔄 Backup e Restore

### Sistema de Backup

```bash
#!/bin/bash
# /etc/cron.daily/fireflies-backup

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/fireflies"
PROJECT_DIR="/var/www/fireflies"
RETENTION_DAYS=7

# Criar diretório de backup
mkdir -p $BACKUP_DIR

# Backup do banco de dados
echo "Backup do banco de dados..."
sudo -u postgres pg_dump fireflies > $BACKUP_DIR/db_backup_$DATE.sql

# Backup dos arquivos de mídia
echo "Backup dos arquivos de mídia..."
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz -C $PROJECT_DIR media/

# Backup das configurações
echo "Backup das configurações..."
tar -czf $BACKUP_DIR/config_backup_$DATE.tar.gz \
    $PROJECT_DIR/.env \
    /etc/nginx/sites-available/fireflies \
    /etc/systemd/system/fireflies.service

# Limpar backups antigos
echo "Limpando backups antigos..."
find $BACKUP_DIR -name "*.sql" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Log do backup
echo "Backup concluído: $DATE" >> /var/log/fireflies/backup.log

# Verificar tamanho dos backups
BACKUP_SIZE=$(du -sh $BACKUP_DIR | cut -f1)
echo "Tamanho total dos backups: $BACKUP_SIZE" >> /var/log/fireflies/backup.log
```

### Script de Restore

```bash
#!/bin/bash
# scripts/restore.sh

BACKUP_DATE=$1
BACKUP_DIR="/var/backups/fireflies"
PROJECT_DIR="/var/www/fireflies"

if [ -z "$BACKUP_DATE" ]; then
    echo "Uso: $0 YYYYMMDD_HHMMSS"
    exit 1
fi

echo "🔄 Iniciando restore do backup $BACKUP_DATE..."

# Verificar se backup existe
if [ ! -f "$BACKUP_DIR/db_backup_$BACKUP_DATE.sql" ]; then
    echo "❌ Backup não encontrado: $BACKUP_DIR/db_backup_$BACKUP_DATE.sql"
    exit 1
fi

# Parar serviços
echo "Parando serviços..."
sudo systemctl stop fireflies
sudo systemctl stop nginx

# Restore do banco de dados
echo "Restaurando banco de dados..."
sudo -u postgres psql -d fireflies -c "DROP SCHEMA public CASCADE;"
sudo -u postgres psql -d fireflies -c "CREATE SCHEMA public;"
sudo -u postgres psql -d fireflies < $BACKUP_DIR/db_backup_$BACKUP_DATE.sql

# Restore dos arquivos de mídia
echo "Restaurando arquivos de mídia..."
tar -xzf $BACKUP_DIR/media_backup_$BACKUP_DATE.tar.gz -C $PROJECT_DIR

# Restore das configurações
echo "Restaurando configurações..."
tar -xzf $BACKUP_DIR/config_backup_$BACKUP_DATE.tar.gz -C /

# Aplicar migrações
echo "Aplicando migrações..."
cd $PROJECT_DIR
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput

# Reiniciar serviços
echo "Reiniciando serviços..."
sudo systemctl start fireflies
sudo systemctl start nginx

echo "✅ Restore concluído com sucesso!"
```

## 🎯 Próximos Passos

### Melhorias Planejadas

1. **Containerização**
   - Docker Compose para desenvolvimento
   - Kubernetes para produção
   - Helm charts para deploy

2. **CI/CD Avançado**
   - GitHub Actions
   - Deploy automático
   - Testes automatizados

3. **Monitoramento Avançado**
   - Prometheus + Grafana
   - Alertas automáticos
   - Métricas customizadas

4. **Backup na Nuvem**
   - Integração com AWS S3
   - Backup incremental
   - Restore rápido

5. **Auto-scaling**
   - Load balancer
   - Múltiplas instâncias
   - Health checks avançados

---

**FireFlies CMS** - Deploy robusto e escalável ✨ 