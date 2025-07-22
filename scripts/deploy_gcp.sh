#!/bin/bash

# 🚀 Script de Deploy Automatizado - FireFlies CMS
# Assumindo que a VM já está criada e SSH estabelecido

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERRO] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[AVISO] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Verificar se estamos conectados via SSH
if [ -z "$SSH_CLIENT" ] && [ -z "$SSH_TTY" ]; then
    error "Este script deve ser executado via SSH na VM"
fi

# Variáveis de configuração
VM_IP=""
DOMAIN=""
DB_PASSWORD=""
EMAIL_HOST_USER=""
EMAIL_HOST_PASSWORD=""
SECRET_KEY=""

# Função para obter configurações
get_config() {
    echo "=== Configuração do Deploy ==="
    
    read -p "IP da VM: " VM_IP
    read -p "Domínio (ex: fireflies.com): " DOMAIN
    read -p "Senha do banco de dados: " DB_PASSWORD
    read -p "Email para notificações: " EMAIL_HOST_USER
    read -p "Senha do email (App Password): " EMAIL_HOST_PASSWORD
    
    # Gerar SECRET_KEY
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
    
    echo "Configuração obtida!"
}

# Função para atualizar sistema
update_system() {
    log "Atualizando sistema..."
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y curl wget git unzip software-properties-common netcat
}

# Função para configurar usuário deploy
setup_deploy_user() {
    log "Configurando usuário deploy..."
    
    # Criar usuário deploy
    sudo adduser --disabled-password --gecos '' deploy
    sudo usermod -aG sudo deploy
    
    # Configurar SSH para deploy
    sudo mkdir -p /home/deploy/.ssh
    sudo cp ~/.ssh/authorized_keys /home/deploy/.ssh/
    sudo chown -R deploy:deploy /home/deploy/.ssh
    sudo chmod 700 /home/deploy/.ssh
    sudo chmod 600 /home/deploy/.ssh/authorized_keys
}

# Função para instalar Python
install_python() {
    log "Instalando Python 3.11..."
    
    # Adicionar repositório deadsnakes
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update
    
    # Instalar Python 3.11
    sudo apt install -y python3.11 python3.11-venv python3.11-dev
    
    # Configurar como padrão
    sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
    sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1
    
    # Instalar pip
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11
}

# Função para instalar PostgreSQL
install_postgresql() {
    log "Instalando PostgreSQL..."
    
    # Adicionar repositório oficial
    sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
    sudo apt update
    
    # Instalar PostgreSQL
    sudo apt install -y postgresql postgresql-contrib
    
    # Configurar PostgreSQL
    sudo -u postgres createuser --interactive --pwprompt deploy
    sudo -u postgres createdb fireflies
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE fireflies TO deploy;"
    
    # Configurar pg_hba.conf
    sudo sed -i '/local.*all.*all.*peer/a local   all             deploy                                  md5' /etc/postgresql/*/main/pg_hba.conf
    sudo sed -i '/host.*all.*all.*127.0.0.1\/32.*md5/a host    fireflies       deploy          127.0.0.1/32           md5' /etc/postgresql/*/main/pg_hba.conf
    sudo sed -i '/host.*all.*all.*::1\/128.*md5/a host    fireflies       deploy          ::1/128                 md5' /etc/postgresql/*/main/pg_hba.conf
    
    # Reiniciar PostgreSQL
    sudo systemctl restart postgresql
}

# Função para instalar Redis
install_redis() {
    log "Instalando Redis..."
    
    sudo apt install -y redis-server
    
    # Configurar Redis
    sudo sed -i 's/bind 127.0.0.1/bind 127.0.0.1 ::1/' /etc/redis/redis.conf
    sudo systemctl enable redis-server
    sudo systemctl start redis-server
}

# Função para instalar Nginx
install_nginx() {
    log "Instalando Nginx..."
    
    sudo apt install -y nginx
    sudo systemctl enable nginx
    sudo systemctl start nginx
}

# Função para configurar firewall
setup_firewall() {
    log "Configurando firewall..."
    
    sudo ufw allow ssh
    sudo ufw allow 'Nginx Full'
    sudo ufw --force enable
}

# Função para clonar aplicação
clone_application() {
    log "Clonando aplicação..."
    
    sudo su - deploy << 'EOF'
    git clone https://github.com/seu-usuario/project-nix.git
    cd project-nix
    
    # Configurar git
    git config --global user.name "Deploy User"
    git config --global user.email "deploy@projectnix.com"
EOF
}

# Função para configurar ambiente virtual
setup_virtual_env() {
    log "Configurando ambiente virtual..."
    
    sudo su - deploy << 'EOF'
    cd project-nix
    python3.11 -m venv venv
    source venv/bin/activate
    
    # Instalar dependências
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install gunicorn psycopg2-binary whitenoise
EOF
}

# Função para configurar variáveis de ambiente
setup_env() {
    log "Configurando variáveis de ambiente..."
    
    sudo su - deploy << EOF
    cd fireflies
    
    # Criar arquivo .env
    cat > .env << 'ENVEOF'
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=$SECRET_KEY
DATABASE_URL=postgresql://deploy:$DB_PASSWORD@localhost:5432/fireflies
DB_ENGINE=django.db.backends.postgresql
DB_NAME=fireflies
DB_USER=deploy
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,$VM_IP
CSRF_TRUSTED_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=$EMAIL_HOST_USER
EMAIL_HOST_PASSWORD=$EMAIL_HOST_PASSWORD
ENVEOF
EOF
}

# Função para configurar settings de produção
setup_production_settings() {
    log "Configurando settings de produção..."
    
    sudo su - deploy << 'EOF'
    cd fireflies
    
    # Criar settings de produção
    cat > core/settings_production.py << 'SETTINGSEOF'
from .settings import *

DEBUG = False
ENVIRONMENT = 'production'

# Configurações de segurança
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Configurações de sessão
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Configurações de cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# Configurações de logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/fireflies/django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
SETTINGSEOF
EOF
}

# Função para executar migrações
run_migrations() {
    log "Executando migrações..."
    
    sudo su - deploy << 'EOF'
    cd fireflies
    source venv/bin/activate
    
    # Configurar variável de ambiente
    export DJANGO_SETTINGS_MODULE=core.settings_production
    
    # Executar migrações
    python manage.py migrate
    
    # Coletar arquivos estáticos
    python manage.py collectstatic --noinput
EOF
}

# Função para configurar Gunicorn
setup_gunicorn() {
    log "Configurando Gunicorn..."
    
    sudo su - deploy << 'EOF'
    cd fireflies
    
    # Criar arquivo de configuração do Gunicorn
    cat > gunicorn.conf.py << 'GUNICORNEOF'
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
preload_app = True
GUNICORNEOF
EOF
}

# Função para configurar systemd service
setup_systemd() {
    log "Configurando systemd service..."
    
    # Sair do usuário deploy
    exit
    
    # Criar arquivo de serviço
    sudo tee /etc/systemd/system/fireflies.service > /dev/null << 'SERVICEEOF'
[Unit]
Description=FireFlies CMS
After=network.target postgresql.service redis-server.service

[Service]
Type=notify
User=deploy
Group=deploy
WorkingDirectory=/home/deploy/fireflies
Environment=DJANGO_SETTINGS_MODULE=core.settings_production
Environment=PATH=/home/deploy/fireflies/venv/bin
ExecStart=/home/deploy/fireflies/venv/bin/gunicorn --config gunicorn.conf.py core.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
SERVICEEOF
    
    # Criar diretório de logs
    sudo mkdir -p /var/log/fireflies
    sudo chown deploy:deploy /var/log/fireflies
    
    # Habilitar e iniciar serviço
    sudo systemctl daemon-reload
    sudo systemctl enable fireflies
    sudo systemctl start fireflies
}

# Função para configurar Nginx
setup_nginx() {
    log "Configurando Nginx..."
    
    # Remover configuração padrão
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Criar configuração do Nginx
    sudo tee /etc/nginx/sites-available/fireflies > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN $VM_IP;

    # Logs
    access_log /var/log/nginx/fireflies_access.log;
    error_log /var/log/nginx/fireflies_error.log;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Arquivos estáticos
    location /static/ {
        alias /home/deploy/fireflies/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Arquivos de mídia
    location /media/ {
        alias /home/deploy/fireflies/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Proxy para aplicação
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Health check
    location /health/ {
        proxy_pass http://127.0.0.1:8000;
        access_log off;
    }
}
EOF
    
    # Habilitar configuração
    sudo ln -sf /etc/nginx/sites-available/fireflies /etc/nginx/sites-enabled/
    
    # Testar configuração
    sudo nginx -t
    
    # Reiniciar Nginx
    sudo systemctl restart nginx
}

# Função para configurar SSL
setup_ssl() {
    log "Configurando SSL..."
    
    # Instalar Certbot
    sudo apt install -y certbot python3-certbot-nginx
    
    # Obter certificado SSL
    sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email $EMAIL_HOST_USER
    
    # Configurar renovação automática
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
}

# Função para configurar monitoramento
setup_monitoring() {
    log "Configurando monitoramento..."
    
    # Instalar ferramentas de monitoramento
    sudo apt install -y htop iotop iftop
    
    # Criar script de monitoramento
    sudo tee /home/deploy/monitor.sh > /dev/null << 'MONITOREOF'
#!/bin/bash
echo "=== FireFlies Monitor ==="
echo "Data: $(date)"
echo "Uptime: $(uptime)"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory: $(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2}')"
echo "Disk: $(df -h | awk '$NF=="/"{printf "%s", $5}')"
echo "FireFlies Status: $(systemctl is-active fireflies)"
echo "Nginx Status: $(systemctl is-active nginx)"
echo "PostgreSQL Status: $(systemctl is-active postgresql)"
echo "Redis Status: $(systemctl is-active redis-server)"
MONITOREOF
    
    sudo chmod +x /home/deploy/monitor.sh
    
    # Configurar crontab para monitoramento
    sudo su - deploy -c "(crontab -l 2>/dev/null; echo '*/5 * * * * /home/deploy/monitor.sh >> /home/deploy/monitor.log 2>&1') | crontab -"
}

# Função para configurar backup
setup_backup() {
    log "Configurando backup..."
    
    # Criar script de backup
    sudo tee /home/deploy/backup.sh > /dev/null << 'BACKUPEOF'
#!/bin/bash
BACKUP_DIR="/home/deploy/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="fireflies_backup_$DATE"

mkdir -p $BACKUP_DIR

# Backup do banco de dados
pg_dump fireflies > $BACKUP_DIR/${BACKUP_NAME}.sql

# Backup dos arquivos de mídia
tar -czf $BACKUP_DIR/${BACKUP_NAME}_media.tar.gz -C /home/deploy/fireflies media/

# Backup das configurações
tar -czf $BACKUP_DIR/${BACKUP_NAME}_config.tar.gz -C /home/deploy/fireflies .env

# Manter apenas os últimos 7 backups
find $BACKUP_DIR -name "fireflies_backup_*" -mtime +7 -delete

echo "Backup concluído: $BACKUP_NAME"
BACKUPEOF
    
    sudo chmod +x /home/deploy/backup.sh
    
    # Configurar backup automático
    sudo su - deploy -c "(crontab -l 2>/dev/null; echo '0 3 * * * /home/deploy/backup.sh >> /home/deploy/backup.log 2>&1') | crontab -"
}

# Função para criar script de deploy
create_deploy_script() {
    log "Criando script de deploy..."
    
    sudo tee /home/deploy/deploy.sh > /dev/null << 'DEPLOYEOF'
#!/bin/bash
set -e

echo "Iniciando deploy do Project Nix..."

# Ir para diretório do projeto
cd /home/deploy/project-nix

# Atualizar código
git pull origin main

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Executar migrações
export DJANGO_SETTINGS_MODULE=core.settings_production
python manage.py migrate

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Reiniciar serviço
sudo systemctl restart project-nix

# Verificar status
sudo systemctl status project-nix

echo "Deploy concluído com sucesso!"
DEPLOYEOF
    
    sudo chmod +x /home/deploy/deploy.sh
}

# Função para verificar status
check_status() {
    log "Verificando status dos serviços..."
    
    echo "=== Status dos Serviços ==="
    sudo systemctl status fireflies --no-pager -l
    echo ""
    sudo systemctl status nginx --no-pager -l
    echo ""
    sudo systemctl status postgresql --no-pager -l
    echo ""
    sudo systemctl status redis-server --no-pager -l
    echo ""
    
    echo "=== Teste de Conexão ==="
    curl -I http://localhost/health/ || echo "Health check falhou"
    echo ""
    
    echo "=== Informações do Sistema ==="
    echo "IP: $VM_IP"
    echo "Domínio: $DOMAIN"
    echo "Uptime: $(uptime)"
    echo "Disco: $(df -h /)"
    echo "Memória: $(free -h)"
}

# Função principal
main() {
    echo "🚀 Script de Deploy Automatizado - Project Nix CMS"
    echo "Assumindo que a VM já está criada e SSH estabelecido"
    echo ""
    
    # Obter configurações
    get_config
    
    # Executar etapas
    update_system
    setup_deploy_user
    install_python
    install_postgresql
    install_redis
    install_nginx
    setup_firewall
    clone_application
    setup_virtual_env
    setup_env
    setup_production_settings
    run_migrations
    setup_gunicorn
    setup_systemd
    setup_nginx
    setup_ssl
    setup_monitoring
    setup_backup
    create_deploy_script
    
    # Verificar status final
    check_status
    
    log "Deploy concluído com sucesso!"
    echo ""
    echo "🎉 FireFlies CMS está rodando em produção!"
    echo ""
    echo "📋 Próximos passos:"
    echo "1. Acesse http://$DOMAIN"
    echo "2. Configure o superusuário: sudo su - deploy && cd fireflies && source venv/bin/activate && python manage.py createsuperuser"
    echo "3. Configure o domínio no DNS"
    echo "4. Monitore os logs: tail -f /var/log/fireflies/django.log"
    echo ""
    echo "📚 Scripts disponíveis:"
    echo "- /home/deploy/deploy.sh (para futuros deploys)"
    echo "- /home/deploy/backup.sh (backup manual)"
    echo "- /home/deploy/monitor.sh (monitoramento)"
}

# Executar função principal
main "$@" 