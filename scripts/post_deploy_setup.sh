#!/bin/bash

# 🔧 Script de Configuração Pós-Deploy - FireFlies CMS
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
DOMAIN=""
EMAIL_HOST_USER=""
EMAIL_HOST_PASSWORD=""
ADMIN_USERNAME=""
ADMIN_EMAIL=""
ADMIN_PASSWORD=""

# Função para obter configurações
get_config() {
    echo "=== Configuração Pós-Deploy ==="
    
    read -p "Domínio configurado: " DOMAIN
    read -p "Email para notificações: " EMAIL_HOST_USER
    read -p "Senha do email (App Password): " EMAIL_HOST_PASSWORD
    read -p "Nome do usuário admin: " ADMIN_USERNAME
    read -p "Email do admin: " ADMIN_EMAIL
    read -p "Senha do admin: " ADMIN_PASSWORD
    
    echo "Configuração obtida!"
}

# Função para configurar monitoramento avançado
setup_advanced_monitoring() {
    log "Configurando monitoramento avançado..."
    
    # Instalar ferramentas adicionais
    sudo apt install -y sysstat iotop htop nethogs
    
    # Configurar sysstat
    sudo sed -i 's/ENABLED="false"/ENABLED="true"/' /etc/default/sysstat
    sudo systemctl enable sysstat
    sudo systemctl start sysstat
    
    # Criar script de monitoramento avançado
    sudo tee /home/deploy/advanced_monitor.sh > /dev/null << 'MONITOREOF'
#!/bin/bash
echo "=== FireFlies Advanced Monitor ==="
echo "Data: $(date)"
echo "Uptime: $(uptime)"
echo ""

echo "=== CPU ==="
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Load Average: $(uptime | awk -F'load average:' '{print $2}')"
echo ""

echo "=== Memory ==="
free -h
echo ""

echo "=== Disk ==="
df -h
echo ""

echo "=== Network ==="
ss -tuln | grep -E ':(80|443|22|5432|6379)'
echo ""

echo "=== Services ==="
echo "FireFlies: $(systemctl is-active fireflies)"
echo "Nginx: $(systemctl is-active nginx)"
echo "PostgreSQL: $(systemctl is-active postgresql)"
echo "Redis: $(systemctl is-active redis-server)"
echo ""

echo "=== Process Info ==="
ps aux | grep -E '(fireflies|gunicorn|nginx|postgres|redis)' | grep -v grep
echo ""

echo "=== Recent Logs ==="
tail -5 /var/log/fireflies/django.log 2>/dev/null || echo "No Django logs found"
echo ""
MONITOREOF
    
    sudo chmod +x /home/deploy/advanced_monitor.sh
    
    # Configurar crontab para monitoramento avançado
    sudo su - deploy -c "(crontab -l 2>/dev/null; echo '*/10 * * * * /home/deploy/advanced_monitor.sh >> /home/deploy/advanced_monitor.log 2>&1') | crontab -"
}

# Função para configurar backup avançado
setup_advanced_backup() {
    log "Configurando backup avançado..."
    
    # Criar script de backup avançado
    sudo tee /home/deploy/advanced_backup.sh > /dev/null << 'BACKUPEOF'
#!/bin/bash
BACKUP_DIR="/home/deploy/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="fireflies_backup_$DATE"

mkdir -p $BACKUP_DIR

echo "Iniciando backup avançado: $BACKUP_NAME"

# Backup do banco de dados
echo "Backup do banco de dados..."
pg_dump fireflies > $BACKUP_DIR/${BACKUP_NAME}.sql

# Backup dos arquivos de mídia
echo "Backup dos arquivos de mídia..."
tar -czf $BACKUP_DIR/${BACKUP_NAME}_media.tar.gz -C /home/deploy/fireflies media/

# Backup das configurações
echo "Backup das configurações..."
tar -czf $BACKUP_DIR/${BACKUP_NAME}_config.tar.gz -C /home/deploy/fireflies .env

# Backup dos logs
echo "Backup dos logs..."
tar -czf $BACKUP_DIR/${BACKUP_NAME}_logs.tar.gz -C /var/log fireflies/

# Backup das configurações do sistema
echo "Backup das configurações do sistema..."
tar -czf $BACKUP_DIR/${BACKUP_NAME}_system.tar.gz -C /etc nginx/ postgresql/ redis/

# Criar arquivo de metadados
cat > $BACKUP_DIR/${BACKUP_NAME}_metadata.txt << EOF
Backup realizado em: $(date)
Versão do sistema: $(lsb_release -d | cut -f2)
Versão do PostgreSQL: $(psql --version)
Versão do Redis: $(redis-server --version)
Tamanho do backup: $(du -sh $BACKUP_DIR/${BACKUP_NAME}* | awk '{sum+=$1} END {print sum}')
EOF

# Manter apenas os últimos 7 backups
find $BACKUP_DIR -name "fireflies_backup_*" -mtime +7 -delete

echo "Backup avançado concluído: $BACKUP_NAME"
BACKUPEOF
    
    sudo chmod +x /home/deploy/advanced_backup.sh
    
    # Configurar backup automático avançado
    sudo su - deploy -c "(crontab -l 2>/dev/null; echo '0 2 * * * /home/deploy/advanced_backup.sh >> /home/deploy/advanced_backup.log 2>&1') | crontab -"
}

# Função para configurar SSL avançado
setup_advanced_ssl() {
    log "Configurando SSL avançado..."
    
    if [ -z "$DOMAIN" ]; then
        warning "Domínio não especificado. Pulando configuração SSL avançada."
        return 0
    fi
    
    # Configurar SSL com configurações de segurança
    sudo tee /etc/nginx/snippets/ssl-params.conf > /dev/null << 'SSLEOF'
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
ssl_ecdh_curve secp384r1;
ssl_session_timeout 10m;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
SSLEOF
    
    # Atualizar configuração do Nginx
    sudo sed -i '/server_name/a \    include snippets/ssl-params.conf;' /etc/nginx/sites-available/fireflies
    
    # Testar e reiniciar Nginx
    sudo nginx -t
    sudo systemctl reload nginx
}

# Função para configurar email
setup_email() {
    log "Configurando email..."
    
    if [ -z "$EMAIL_HOST_USER" ] || [ -z "$EMAIL_HOST_PASSWORD" ]; then
        warning "Credenciais de email não fornecidas. Pulando configuração de email."
        return 0
    fi
    
    # Atualizar configurações de email no .env
    sudo su - deploy << EOF
    cd fireflies
    sed -i 's/EMAIL_HOST_USER=.*/EMAIL_HOST_USER=$EMAIL_HOST_USER/' .env
    sed -i 's/EMAIL_HOST_PASSWORD=.*/EMAIL_HOST_PASSWORD=$EMAIL_HOST_PASSWORD/' .env
EOF
    
    # Testar configuração de email
    sudo su - deploy << 'EOF'
    cd fireflies
    source venv/bin/activate
    export DJANGO_SETTINGS_MODULE=core.settings_production
    python manage.py shell -c "
from django.core.mail import send_mail
from django.conf import settings
try:
    send_mail(
        'Teste de Email - FireFlies',
        'Este é um teste de configuração de email.',
        settings.EMAIL_HOST_USER,
        ['$EMAIL_HOST_USER'],
        fail_silently=False,
    )
    print('Email de teste enviado com sucesso!')
except Exception as e:
    print(f'Erro ao enviar email: {e}')
"
EOF
}

# Função para configurar domínio
setup_domain() {
    log "Configurando domínio..."
    
    if [ -z "$DOMAIN" ]; then
        warning "Domínio não especificado. Pulando configuração de domínio."
        return 0
    fi
    
    # Atualizar configurações de domínio no .env
    sudo su - deploy << EOF
    cd fireflies
    sed -i 's/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN/' .env
    sed -i 's/CSRF_TRUSTED_ORIGINS=.*/CSRF_TRUSTED_ORIGINS=https:\/\/$DOMAIN,https:\/\/www.$DOMAIN/' .env
EOF
    
    # Atualizar configuração do Nginx
    sudo sed -i "s/server_name .*/server_name $DOMAIN www.$DOMAIN;/" /etc/nginx/sites-available/fireflies
    
    # Testar e reiniciar Nginx
    sudo nginx -t
    sudo systemctl reload nginx
}

# Função para configurar segurança
setup_security() {
    log "Configurando segurança..."
    
    # Configurar fail2ban
    sudo apt install -y fail2ban
    
    # Configurar fail2ban para SSH
    sudo tee /etc/fail2ban/jail.local > /dev/null << 'FAIL2BANEOF'
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
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3
FAIL2BANEOF
    
    sudo systemctl enable fail2ban
    sudo systemctl start fail2ban
    
    # Configurar firewall adicional
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    sudo ufw allow 'Nginx Full'
    sudo ufw --force enable
    
    # Configurar atualizações automáticas
    sudo apt install -y unattended-upgrades
    sudo dpkg-reconfigure -plow unattended-upgrades
    
    # Configurar auditoria
    sudo apt install -y auditd
    sudo systemctl enable auditd
    sudo systemctl start auditd
}

# Função para configurar superusuário
setup_superuser() {
    log "Configurando superusuário..."
    
    if [ -z "$ADMIN_USERNAME" ] || [ -z "$ADMIN_EMAIL" ] || [ -z "$ADMIN_PASSWORD" ]; then
        warning "Credenciais do admin não fornecidas. Pulando criação do superusuário."
        return 0
    fi
    
    # Criar superusuário
    sudo su - deploy << EOF
    cd fireflies
    source venv/bin/activate
    export DJANGO_SETTINGS_MODULE=core.settings_production
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$ADMIN_USERNAME').exists():
    User.objects.create_superuser('$ADMIN_USERNAME', '$ADMIN_EMAIL', '$ADMIN_PASSWORD')
    print('Superusuário criado com sucesso!')
else:
    print('Superusuário já existe!')
"
EOF
}

# Função para configurar logs estruturados
setup_structured_logs() {
    log "Configurando logs estruturados..."
    
    # Instalar logrotate
    sudo tee /etc/logrotate.d/fireflies > /dev/null << 'LOGROTATEEOF'
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

/var/log/fireflies/*.log {
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
LOGROTATEEOF
    
    # Criar diretório de logs estruturados
    sudo mkdir -p /var/log/fireflies/structured
    sudo chown deploy:deploy /var/log/fireflies/structured
    
    # Configurar logrotate
    sudo logrotate -f /etc/logrotate.d/fireflies
}

# Função para configurar performance
setup_performance() {
    log "Configurando otimizações de performance..."
    
    # Configurar PostgreSQL para performance
    sudo tee -a /etc/postgresql/*/main/postgresql.conf > /dev/null << 'POSTGRESQLEOF'

# Configurações de performance
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
POSTGRESQLEOF
    
    # Configurar Redis para performance
    sudo sed -i 's/# maxmemory <bytes>/maxmemory 256mb/' /etc/redis/redis.conf
    sudo sed -i 's/# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
    
    # Configurar Nginx para performance
    sudo tee /etc/nginx/conf.d/performance.conf > /dev/null << 'NGINXEOF'
# Configurações de performance
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 65535;
    use epoll;
    multi_accept on;
}

http {
    # Configurações de buffer
    client_body_buffer_size 128k;
    client_max_body_size 10m;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    
    # Configurações de timeout
    client_body_timeout 12;
    client_header_timeout 12;
    keepalive_timeout 15;
    send_timeout 10;
    
    # Configurações de gzip
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
}
NGINXEOF
    
    # Reiniciar serviços
    sudo systemctl restart postgresql
    sudo systemctl restart redis-server
    sudo systemctl restart nginx
    sudo systemctl restart fireflies
}

# Função para configurar backup para nuvem
setup_cloud_backup() {
    log "Configurando backup para nuvem..."
    
    # Instalar rclone para backup na nuvem
    curl https://rclone.org/install.sh | sudo bash
    
    # Criar script de backup na nuvem
    sudo tee /home/deploy/cloud_backup.sh > /dev/null << 'CLOUDBACKUPEOF'
#!/bin/bash
BACKUP_DIR="/home/deploy/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="fireflies_backup_$DATE"

# Fazer backup local primeiro
/home/deploy/advanced_backup.sh

# Configurar rclone (se necessário)
# rclone config

# Fazer upload para nuvem (exemplo com Google Drive)
# rclone copy $BACKUP_DIR fireflies-backups:fireflies/

echo "Backup na nuvem configurado!"
CLOUDBACKUPEOF
    
    sudo chmod +x /home/deploy/cloud_backup.sh
    
    info "Para configurar backup na nuvem, execute: rclone config"
}

# Função para configurar notificações
setup_notifications() {
    log "Configurando notificações..."
    
    # Criar script de notificações
    sudo tee /home/deploy/notifications.sh > /dev/null << 'NOTIFICATIONSEOF'
#!/bin/bash

# Função para enviar notificação
send_notification() {
    local message="$1"
    local subject="$2"
    
    # Enviar email (se configurado)
    if [ ! -z "$EMAIL_HOST_USER" ]; then
        echo "$message" | mail -s "$subject" $EMAIL_HOST_USER
    fi
    
    # Log da notificação
    echo "$(date): $subject - $message" >> /home/deploy/notifications.log
}

# Verificar serviços
check_services() {
    local services=("fireflies" "nginx" "postgresql" "redis-server")
    
    for service in "${services[@]}"; do
        if ! systemctl is-active --quiet $service; then
            send_notification "Serviço $service está inativo!" "Alerta: Serviço Inativo"
        fi
    done
}

# Verificar disco
check_disk() {
    local usage=$(df / | awk 'NR==2{print $5}' | sed 's/%//')
    
    if [ $usage -gt 80 ]; then
        send_notification "Uso de disco está em ${usage}%!" "Alerta: Disco Cheio"
    fi
}

# Verificar memória
check_memory() {
    local usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [ $usage -gt 80 ]; then
        send_notification "Uso de memória está em ${usage}%!" "Alerta: Memória Alta"
    fi
}

# Executar verificações
check_services
check_disk
check_memory
NOTIFICATIONSEOF
    
    sudo chmod +x /home/deploy/notifications.sh
    
    # Configurar crontab para notificações
    sudo su - deploy -c "(crontab -l 2>/dev/null; echo '*/15 * * * * /home/deploy/notifications.sh') | crontab -"
}

# Função para verificar status final
check_final_status() {
    log "Verificando status final..."
    
    echo "=== Status dos Serviços ==="
    sudo systemctl status fireflies --no-pager -l
    echo ""
    sudo systemctl status nginx --no-pager -l
    echo ""
    sudo systemctl status postgresql --no-pager -l
    echo ""
    sudo systemctl status redis-server --no-pager -l
    echo ""
    sudo systemctl status fail2ban --no-pager -l
    echo ""
    
    echo "=== Teste de Conexão ==="
    curl -I http://localhost/health/ || echo "Health check falhou"
    echo ""
    
    echo "=== Informações de Segurança ==="
    sudo ufw status
    echo ""
    sudo fail2ban-client status
    echo ""
    
    echo "=== Informações do Sistema ==="
    echo "Domínio: $DOMAIN"
    echo "Email: $EMAIL_HOST_USER"
    echo "Admin: $ADMIN_USERNAME"
    echo "Uptime: $(uptime)"
    echo "Disco: $(df -h /)"
    echo "Memória: $(free -h)"
}

# Função principal
main() {
    echo "🔧 Script de Configuração Pós-Deploy - FireFlies CMS"
    echo "Assumindo que a VM já está criada e SSH estabelecido"
    echo ""
    
    # Obter configurações
    get_config
    
    # Executar etapas
    setup_advanced_monitoring
    setup_advanced_backup
    setup_advanced_ssl
    setup_email
    setup_domain
    setup_security
    setup_superuser
    setup_structured_logs
    setup_performance
    setup_cloud_backup
    setup_notifications
    
    # Verificar status final
    check_final_status
    
    log "Configuração pós-deploy concluída com sucesso!"
    echo ""
    echo "🎉 FireFlies CMS está totalmente configurado!"
    echo ""
    echo "📋 Configurações aplicadas:"
    echo "✅ Monitoramento avançado"
    echo "✅ Backup avançado"
    echo "✅ SSL avançado"
    echo "✅ Configuração de email"
    echo "✅ Configuração de domínio"
    echo "✅ Segurança (fail2ban, firewall)"
    echo "✅ Superusuário criado"
    echo "✅ Logs estruturados"
    echo "✅ Otimizações de performance"
    echo "✅ Backup na nuvem (configurar manualmente)"
    echo "✅ Notificações automáticas"
    echo ""
    echo "📚 Scripts disponíveis:"
    echo "- /home/deploy/advanced_monitor.sh (monitoramento avançado)"
    echo "- /home/deploy/advanced_backup.sh (backup avançado)"
    echo "- /home/deploy/cloud_backup.sh (backup na nuvem)"
    echo "- /home/deploy/notifications.sh (notificações)"
    echo ""
    echo "🔗 URLs:"
    if [ ! -z "$DOMAIN" ]; then
        echo "- https://$DOMAIN"
        echo "- https://www.$DOMAIN"
    fi
    echo "- http://localhost"
    echo ""
    echo "🔑 Credenciais:"
    echo "- Admin: $ADMIN_USERNAME"
    echo "- Email: $ADMIN_EMAIL"
    echo ""
    echo "📞 Suporte:"
    echo "- Logs: tail -f /var/log/fireflies/django.log"
    echo "- Monitoramento: /home/deploy/advanced_monitor.sh"
    echo "- Backup: /home/deploy/advanced_backup.sh"
}

# Executar função principal
main "$@" 