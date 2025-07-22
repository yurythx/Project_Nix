# 🚀 Guia de Deploy - FireFlies CMS na VM Google Cloud

## 📋 Índice
1. [Pré-requisitos](#pré-requisitos)
2. [Preparação da VM](#preparação-da-vm)
3. [Instalação do Sistema](#instalação-do-sistema)
4. [Configuração do Banco de Dados](#configuração-do-banco-de-dados)
5. [Deploy da Aplicação](#deploy-da-aplicação)
6. [Configuração do Nginx](#configuração-do-nginx)
7. [Configuração do SSL](#configuração-do-ssl)
8. [Monitoramento e Logs](#monitoramento-e-logs)
9. [Backup e Manutenção](#backup-e-manutenção)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Pré-requisitos

### VM Google Cloud
- ✅ VM criada e funcionando
- ✅ Conexão SSH estabelecida
- ✅ IP da VM conhecido
- ✅ Acesso root/sudo disponível

### Recursos Mínimos Recomendados
- **VM**: e2-medium (2 vCPU, 4 GB RAM)
- **Disco**: 20 GB SSD
- **Sistema**: Ubuntu 22.04 LTS

---

## ⚙️ Preparação da VM

### 1. Conectar via SSH
```bash
# Você já deve estar conectado via SSH
# Se não estiver, use:
ssh usuario@IP_DA_VM
# ou
gcloud compute ssh NOME_DA_VM --zone=ZONA
```

### 2. Atualizar Sistema
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git unzip software-properties-common netcat
```

### 3. Configurar Usuário Deploy
```bash
# Criar usuário para deploy
sudo adduser --disabled-password --gecos '' deploy
sudo usermod -aG sudo deploy

# Configurar SSH para deploy
sudo mkdir -p /home/deploy/.ssh
sudo cp ~/.ssh/authorized_keys /home/deploy/.ssh/
sudo chown -R deploy:deploy /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh
sudo chmod 600 /home/deploy/.ssh/authorized_keys
```

### 4. Configurar Hostname
```bash
# Editar hostname
sudo hostnamectl set-hostname fireflies-prod

# Adicionar ao /etc/hosts
echo "127.0.1.1 fireflies-prod" | sudo tee -a /etc/hosts
```

---

## 🔧 Instalação do Sistema

### 1. Instalar Python 3.11
```bash
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
```

### 2. Instalar PostgreSQL
```bash
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
```

### 3. Instalar Redis
```bash
# Instalar Redis
sudo apt install -y redis-server

# Configurar Redis
sudo sed -i 's/bind 127.0.0.1/bind 127.0.0.1 ::1/' /etc/redis/redis.conf
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 4. Instalar Nginx
```bash
# Instalar Nginx
sudo apt install -y nginx

# Configurar Nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 5. Configurar Firewall
```bash
# Configurar UFW
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

---

## 🗄️ Configuração do Banco de Dados

### 1. Configurar PostgreSQL
```bash
# Editar configuração do PostgreSQL
sudo nano /etc/postgresql/*/main/postgresql.conf

# Adicionar/modificar:
listen_addresses = 'localhost'
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
```

### 2. Configurar pg_hba.conf
```bash
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Adicionar:
local   all             deploy                                  md5
host    fireflies       deploy          127.0.0.1/32           md5
host    fireflies       deploy          ::1/128                 md5
```

### 3. Reiniciar PostgreSQL
```bash
sudo systemctl restart postgresql
```

### 4. Testar Conexão
```bash
# Testar conexão
psql -h localhost -U deploy -d fireflies
# Digite a senha quando solicitado
```

---

## 🚀 Deploy da Aplicação

### 1. Mudar para Usuário Deploy
```bash
sudo su - deploy
```

### 2. Clonar Repositório
```bash
# Clonar repositório
git clone https://github.com/seu-usuario/fireflies.git
cd fireflies

# Configurar git
git config --global user.name "Deploy User"
git config --global user.email "deploy@fireflies.com"
```

### 3. Configurar Ambiente Virtual
```bash
# Criar ambiente virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Instalar dependências adicionais para produção
pip install gunicorn psycopg2-binary whitenoise
```

### 4. Configurar Variáveis de Ambiente
```bash
# Criar arquivo .env
nano .env

# Conteúdo do .env:
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=sua_chave_secreta_muito_longa_e_aleatoria
DATABASE_URL=postgresql://deploy:sua_senha_forte@localhost:5432/fireflies
DB_ENGINE=django.db.backends.postgresql
DB_NAME=fireflies
DB_USER=deploy
DB_PASSWORD=sua_senha_forte
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com,IP_DA_VM
CSRF_TRUSTED_ORIGINS=https://seu-dominio.com,https://www.seu-dominio.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_de_app
```

### 5. Configurar Settings de Produção
```bash
# Criar settings de produção
nano core/settings_production.py

# Conteúdo:
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
```

### 6. Executar Migrações
```bash
# Configurar variável de ambiente
export DJANGO_SETTINGS_MODULE=core.settings_production

# Executar migrações
python manage.py migrate

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Criar superusuário
python manage.py createsuperuser
```

### 7. Configurar Gunicorn
```bash
# Criar arquivo de configuração do Gunicorn
nano gunicorn.conf.py

# Conteúdo:
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
preload_app = True
```

### 8. Configurar Systemd Service
```bash
# Sair do usuário deploy
exit

# Criar arquivo de serviço
sudo nano /etc/systemd/system/fireflies.service

# Conteúdo:
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
```

### 9. Habilitar e Iniciar Serviço
```bash
# Criar diretório de logs
sudo mkdir -p /var/log/fireflies
sudo chown deploy:deploy /var/log/fireflies

# Habilitar e iniciar serviço
sudo systemctl daemon-reload
sudo systemctl enable fireflies
sudo systemctl start fireflies

# Verificar status
sudo systemctl status fireflies
```

---

## 🌐 Configuração do Nginx

### 1. Configurar Nginx
```bash
# Criar configuração do Nginx
sudo nano /etc/nginx/sites-available/fireflies

# Conteúdo:
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com IP_DA_VM;

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
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
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
```

### 2. Habilitar Site
```bash
# Remover configuração padrão
sudo rm /etc/nginx/sites-enabled/default

# Habilitar configuração do FireFlies
sudo ln -s /etc/nginx/sites-available/fireflies /etc/nginx/sites-enabled/

# Testar configuração
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

---

## 🔒 Configuração do SSL

### 1. Instalar Certbot
```bash
# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obter certificado SSL
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com

# Configurar renovação automática
sudo crontab -e

# Adicionar linha:
0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. Configurar HTTPS no Nginx
```bash
# O Certbot já configura automaticamente, mas você pode personalizar:
sudo nano /etc/nginx/sites-available/fireflies

# Adicionar configurações de segurança:
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options DENY always;
add_header X-Content-Type-Options nosniff always;
add_header X-XSS-Protection "1; mode=block" always;
```

---

## 📊 Monitoramento e Logs

### 1. Configurar Logrotate
```bash
# Criar configuração do logrotate
sudo nano /etc/logrotate.d/fireflies

# Conteúdo:
/home/deploy/fireflies/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 deploy deploy
    postrotate
        systemctl reload fireflies
    endscript
}
```

### 2. Configurar Monitoramento
```bash
# Instalar htop para monitoramento
sudo apt install -y htop

# Configurar monitoramento de disco
sudo apt install -y iotop

# Configurar monitoramento de rede
sudo apt install -y iftop
```

### 3. Script de Monitoramento
```bash
# Criar script de monitoramento
sudo nano /home/deploy/monitor.sh

# Conteúdo:
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
```

### 4. Configurar Crontab
```bash
# Adicionar ao crontab do deploy
sudo su - deploy
crontab -e

# Adicionar linhas:
# Monitoramento a cada 5 minutos
*/5 * * * * /home/deploy/monitor.sh >> /home/deploy/monitor.log 2>&1

# Limpeza de logs antigos
0 2 * * * find /home/deploy/fireflies/logs -name "*.log" -mtime +30 -delete
```

---

## 💾 Backup e Manutenção

### 1. Script de Backup
```bash
# Criar script de backup
sudo nano /home/deploy/backup.sh

# Conteúdo:
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
```

### 2. Configurar Backup Automático
```bash
# Tornar script executável
chmod +x /home/deploy/backup.sh

# Adicionar ao crontab
crontab -e

# Adicionar linha:
0 3 * * * /home/deploy/backup.sh >> /home/deploy/backup.log 2>&1
```

### 3. Script de Deploy
```bash
# Criar script de deploy
sudo nano /home/deploy/deploy.sh

# Conteúdo:
#!/bin/bash
set -e

echo "Iniciando deploy do FireFlies..."

# Ir para diretório do projeto
cd /home/deploy/fireflies

# Atualizar código
git pull origin main

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Executar migrações
python manage.py migrate

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Reiniciar serviço
sudo systemctl restart fireflies

# Verificar status
sudo systemctl status fireflies

echo "Deploy concluído com sucesso!"
```

---

## 🔧 Troubleshooting

### 1. Verificar Logs
```bash
# Logs do Django
tail -f /var/log/fireflies/django.log

# Logs do Gunicorn
sudo journalctl -u fireflies -f

# Logs do Nginx
sudo tail -f /var/log/nginx/fireflies_error.log

# Logs do PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### 2. Comandos Úteis
```bash
# Verificar status dos serviços
sudo systemctl status fireflies nginx postgresql redis-server

# Verificar portas em uso
sudo netstat -tlnp

# Verificar uso de disco
df -h

# Verificar uso de memória
free -h

# Verificar processos
ps aux | grep fireflies
```

### 3. Problemas Comuns

#### Aplicação não inicia
```bash
# Verificar logs
sudo journalctl -u fireflies -n 50

# Verificar permissões
ls -la /home/deploy/fireflies/

# Verificar variáveis de ambiente
echo $DJANGO_SETTINGS_MODULE
```

#### Nginx não funciona
```bash
# Testar configuração
sudo nginx -t

# Verificar logs
sudo tail -f /var/log/nginx/error.log

# Verificar se o proxy está funcionando
curl -I http://127.0.0.1:8000
```

#### Banco de dados não conecta
```bash
# Testar conexão
psql -h localhost -U deploy -d fireflies

# Verificar configuração
sudo nano /etc/postgresql/*/main/postgresql.conf

# Reiniciar PostgreSQL
sudo systemctl restart postgresql
```

---

## ✅ Checklist Final

### Antes do Deploy
- [ ] VM criada e funcionando
- [ ] Conexão SSH estabelecida
- [ ] IP da VM conhecido
- [ ] Acesso root/sudo disponível

### Durante o Deploy
- [ ] Sistema atualizado
- [ ] Usuário deploy criado
- [ ] Python 3.11 instalado
- [ ] PostgreSQL configurado
- [ ] Redis configurado
- [ ] Nginx instalado
- [ ] Aplicação clonada
- [ ] Ambiente virtual criado
- [ ] Dependências instaladas
- [ ] Migrações executadas
- [ ] Arquivos estáticos coletados
- [ ] Serviço configurado e iniciado
- [ ] Nginx configurado
- [ ] SSL configurado (se necessário)

### Após o Deploy
- [ ] Aplicação acessível via HTTP/HTTPS
- [ ] Health check funcionando
- [ ] Logs sendo gerados
- [ ] Backup configurado
- [ ] Monitoramento ativo
- [ ] Documentação atualizada

---

## 📞 Suporte

### Contatos
- **Email**: suporte@fireflies.com
- **Documentação**: https://docs.fireflies.com
- **Issues**: https://github.com/seu-usuario/fireflies/issues

### Recursos Úteis
- [Google Cloud Documentation](https://cloud.google.com/docs)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

**🎉 Parabéns! Seu FireFlies CMS está rodando em produção!**

Lembre-se de:
- Monitorar regularmente os logs
- Fazer backups frequentes
- Manter o sistema atualizado
- Documentar mudanças importantes 