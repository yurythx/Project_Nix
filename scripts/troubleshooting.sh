#!/bin/bash

# 🔧 Script de Troubleshooting - FireFlies CMS
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
    exit 1
fi

# Função para mostrar menu
show_menu() {
    echo ""
    echo "🔧 Script de Troubleshooting - FireFlies CMS"
    echo "=============================================="
    echo ""
    echo "Escolha uma opção:"
    echo ""
    echo "1.  Verificar status dos serviços"
    echo "2.  Verificar logs de erro"
    echo "3.  Verificar conectividade"
    echo "4.  Verificar recursos do sistema"
    echo "5.  Verificar configurações"
    echo "6.  Verificar banco de dados"
    echo "7.  Verificar SSL/HTTPS"
    echo "8.  Verificar firewall"
    echo "9.  Verificar backup"
    echo "10. Verificar monitoramento"
    echo "11. Reparar problemas comuns"
    echo "12. Reiniciar serviços"
    echo "13. Verificar atualizações"
    echo "14. Diagnóstico completo"
    echo "15. Sair"
    echo ""
}

# Função para verificar status dos serviços
check_services() {
    log "Verificando status dos serviços..."
    echo ""
    
    local services=("fireflies" "nginx" "postgresql" "redis-server" "fail2ban")
    local all_ok=true
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet $service; then
            echo "✅ $service: ATIVO"
        else
            echo "❌ $service: INATIVO"
            all_ok=false
        fi
    done
    
    echo ""
    if $all_ok; then
        log "Todos os serviços estão ativos!"
    else
        warning "Alguns serviços estão inativos. Use a opção 12 para reiniciar."
    fi
}

# Função para verificar logs de erro
check_logs() {
    log "Verificando logs de erro..."
    echo ""
    
    echo "=== Logs do FireFlies ==="
    if [ -f "/var/log/fireflies/django.log" ]; then
        echo "Últimas 10 linhas do log do Django:"
        tail -10 /var/log/fireflies/django.log
    else
        warning "Arquivo de log do Django não encontrado"
    fi
    echo ""
    
    echo "=== Logs do Gunicorn ==="
    sudo journalctl -u fireflies --no-pager -n 10
    echo ""
    
    echo "=== Logs do Nginx ==="
    if [ -f "/var/log/nginx/error.log" ]; then
        echo "Últimas 10 linhas do log de erro do Nginx:"
        tail -10 /var/log/nginx/error.log
    else
        warning "Arquivo de log do Nginx não encontrado"
    fi
    echo ""
    
    echo "=== Logs do PostgreSQL ==="
    sudo journalctl -u postgresql --no-pager -n 5
    echo ""
    
    echo "=== Logs do Redis ==="
    sudo journalctl -u redis-server --no-pager -n 5
    echo ""
}

# Função para verificar conectividade
check_connectivity() {
    log "Verificando conectividade..."
    echo ""
    
    echo "=== Teste de Portas ==="
    local ports=("22" "80" "443" "5432" "6379" "8000")
    
    for port in "${ports[@]}"; do
        if nc -z localhost $port 2>/dev/null; then
            echo "✅ Porta $port: ABERTA"
        else
            echo "❌ Porta $port: FECHADA"
        fi
    done
    echo ""
    
    echo "=== Teste de HTTP ==="
    if curl -s -o /dev/null -w "%{http_code}" http://localhost/health/ | grep -q "200\|302"; then
        echo "✅ Health check: OK"
    else
        echo "❌ Health check: FALHOU"
    fi
    
    if curl -s -o /dev/null -w "%{http_code}" http://localhost/ | grep -q "200\|302"; then
        echo "✅ Site principal: OK"
    else
        echo "❌ Site principal: FALHOU"
    fi
    echo ""
    
    echo "=== Teste de DNS ==="
    if nslookup google.com >/dev/null 2>&1; then
        echo "✅ DNS: OK"
    else
        echo "❌ DNS: FALHOU"
    fi
    echo ""
}

# Função para verificar recursos do sistema
check_resources() {
    log "Verificando recursos do sistema..."
    echo ""
    
    echo "=== Uso de CPU ==="
    top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1
    echo ""
    
    echo "=== Uso de Memória ==="
    free -h
    echo ""
    
    echo "=== Uso de Disco ==="
    df -h
    echo ""
    
    echo "=== Load Average ==="
    uptime
    echo ""
    
    echo "=== Processos do FireFlies ==="
    ps aux | grep -E "(fireflies|gunicorn)" | grep -v grep
    echo ""
    
    echo "=== Uso de Rede ==="
    ss -tuln | grep -E ':(80|443|22|5432|6379)'
    echo ""
}

# Função para verificar configurações
check_configurations() {
    log "Verificando configurações..."
    echo ""
    
    echo "=== Configuração do Nginx ==="
    if sudo nginx -t 2>/dev/null; then
        echo "✅ Configuração do Nginx: OK"
    else
        echo "❌ Configuração do Nginx: ERRO"
        sudo nginx -t
    fi
    echo ""
    
    echo "=== Configuração do PostgreSQL ==="
    if sudo -u postgres psql -c "SELECT version();" >/dev/null 2>&1; then
        echo "✅ PostgreSQL: OK"
    else
        echo "❌ PostgreSQL: ERRO"
    fi
    echo ""
    
    echo "=== Configuração do Redis ==="
    if redis-cli ping >/dev/null 2>&1; then
        echo "✅ Redis: OK"
    else
        echo "❌ Redis: ERRO"
    fi
    echo ""
    
    echo "=== Configuração do Firewall ==="
    sudo ufw status
    echo ""
    
    echo "=== Configuração do Fail2ban ==="
    sudo fail2ban-client status
    echo ""
}

# Função para verificar banco de dados
check_database() {
    log "Verificando banco de dados..."
    echo ""
    
    echo "=== Status do PostgreSQL ==="
    sudo systemctl status postgresql --no-pager -l
    echo ""
    
    echo "=== Conexão com o banco ==="
    if sudo -u deploy psql -h localhost -U deploy -d fireflies -c "SELECT 1;" >/dev/null 2>&1; then
        echo "✅ Conexão com banco: OK"
    else
        echo "❌ Conexão com banco: FALHOU"
    fi
    echo ""
    
    echo "=== Tabelas do Django ==="
    sudo su - deploy << 'EOF'
    cd fireflies
    source venv/bin/activate
    export DJANGO_SETTINGS_MODULE=core.settings_production
    python manage.py showmigrations --list
EOF
    echo ""
    
    echo "=== Tamanho do banco ==="
    sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('fireflies'));"
    echo ""
}

# Função para verificar SSL/HTTPS
check_ssl() {
    log "Verificando SSL/HTTPS..."
    echo ""
    
    echo "=== Certificados SSL ==="
    if [ -d "/etc/letsencrypt/live" ]; then
        echo "Certificados encontrados:"
        ls /etc/letsencrypt/live/
        echo ""
        
        echo "Status dos certificados:"
        sudo certbot certificates
    else
        warning "Nenhum certificado SSL encontrado"
    fi
    echo ""
    
    echo "=== Teste de HTTPS ==="
    if curl -s -o /dev/null -w "%{http_code}" https://localhost/ 2>/dev/null | grep -q "200\|302"; then
        echo "✅ HTTPS: OK"
    else
        echo "❌ HTTPS: FALHOU"
    fi
    echo ""
}

# Função para verificar firewall
check_firewall() {
    log "Verificando firewall..."
    echo ""
    
    echo "=== Status do UFW ==="
    sudo ufw status verbose
    echo ""
    
    echo "=== Regras do iptables ==="
    sudo iptables -L -n
    echo ""
    
    echo "=== Status do Fail2ban ==="
    sudo fail2ban-client status
    echo ""
}

# Função para verificar backup
check_backup() {
    log "Verificando backup..."
    echo ""
    
    echo "=== Backups disponíveis ==="
    if [ -d "/home/deploy/backups" ]; then
        ls -la /home/deploy/backups/
        echo ""
        
        echo "Tamanho dos backups:"
        du -sh /home/deploy/backups/*
    else
        warning "Diretório de backups não encontrado"
    fi
    echo ""
    
    echo "=== Último backup ==="
    if [ -f "/home/deploy/backup.log" ]; then
        tail -5 /home/deploy/backup.log
    else
        warning "Log de backup não encontrado"
    fi
    echo ""
}

# Função para verificar monitoramento
check_monitoring() {
    log "Verificando monitoramento..."
    echo ""
    
    echo "=== Scripts de monitoramento ==="
    if [ -f "/home/deploy/monitor.sh" ]; then
        echo "✅ Script de monitoramento: OK"
    else
        echo "❌ Script de monitoramento: NÃO ENCONTRADO"
    fi
    
    if [ -f "/home/deploy/advanced_monitor.sh" ]; then
        echo "✅ Script de monitoramento avançado: OK"
    else
        echo "❌ Script de monitoramento avançado: NÃO ENCONTRADO"
    fi
    echo ""
    
    echo "=== Logs de monitoramento ==="
    if [ -f "/home/deploy/monitor.log" ]; then
        echo "Últimas 5 linhas do log de monitoramento:"
        tail -5 /home/deploy/monitor.log
    else
        warning "Log de monitoramento não encontrado"
    fi
    echo ""
    
    echo "=== Crontab do deploy ==="
    sudo su - deploy -c "crontab -l" 2>/dev/null || echo "Nenhum crontab configurado"
    echo ""
}

# Função para reparar problemas comuns
repair_common_issues() {
    log "Reparando problemas comuns..."
    echo ""
    
    echo "=== Verificando permissões ==="
    sudo chown -R deploy:deploy /home/deploy/project-nix
    sudo chmod -R 755 /home/deploy/project-nix
    echo "✅ Permissões corrigidas"
    echo ""
    
    echo "=== Verificando arquivos estáticos ==="
    sudo su - deploy << 'EOF'
    cd project-nix
    source venv/bin/activate
    export DJANGO_SETTINGS_MODULE=core.settings_production
    python manage.py collectstatic --noinput
EOF
    echo "✅ Arquivos estáticos atualizados"
    echo ""
    
    echo "=== Verificando migrações ==="
    sudo su - deploy << 'EOF'
    cd project-nix
    source venv/bin/activate
    export DJANGO_SETTINGS_MODULE=core.settings_production
    python manage.py migrate
EOF
    echo "✅ Migrações aplicadas"
    echo ""
    
    echo "=== Limpando cache ==="
    sudo systemctl restart redis-server
    echo "✅ Cache limpo"
    echo ""
    
    echo "=== Verificando configurações ==="
    sudo nginx -t && sudo systemctl reload nginx
    echo "✅ Nginx reconfigurado"
    echo ""
}

# Função para reiniciar serviços
restart_services() {
    log "Reiniciando serviços..."
    echo ""
    
    local services=("postgresql" "redis-server" "nginx" "fireflies")
    
    for service in "${services[@]}"; do
        echo "Reiniciando $service..."
        sudo systemctl restart $service
        sleep 2
        
        if systemctl is-active --quiet $service; then
            echo "✅ $service: REINICIADO COM SUCESSO"
        else
            echo "❌ $service: FALHA AO REINICIAR"
        fi
        echo ""
    done
}

# Função para verificar atualizações
check_updates() {
    log "Verificando atualizações..."
    echo ""
    
    echo "=== Atualizações do sistema ==="
    sudo apt update
    local updates=$(apt list --upgradable 2>/dev/null | wc -l)
    echo "Pacotes com atualizações disponíveis: $((updates - 1))"
    echo ""
    
    echo "=== Atualizações de segurança ==="
    sudo unattended-upgrade --dry-run
    echo ""
    
    echo "=== Status dos serviços ==="
    sudo systemctl status unattended-upgrades --no-pager -l
    echo ""
}

# Função para diagnóstico completo
full_diagnostic() {
    log "Executando diagnóstico completo..."
    echo ""
    
    check_services
    check_resources
    check_connectivity
    check_configurations
    check_database
    check_ssl
    check_firewall
    check_backup
    check_monitoring
    check_updates
    
    echo "=== Resumo do Diagnóstico ==="
    echo "Data: $(date)"
    echo "Uptime: $(uptime)"
    echo "Load: $(uptime | awk -F'load average:' '{print $2}')"
    echo "Memória: $(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
    echo "Disco: $(df -h / | awk 'NR==2{print $5}')"
    echo ""
    
    log "Diagnóstico completo concluído!"
}

# Função principal
main() {
    while true; do
        show_menu
        read -p "Digite sua opção (1-15): " choice
        
        case $choice in
            1)
                check_services
                ;;
            2)
                check_logs
                ;;
            3)
                check_connectivity
                ;;
            4)
                check_resources
                ;;
            5)
                check_configurations
                ;;
            6)
                check_database
                ;;
            7)
                check_ssl
                ;;
            8)
                check_firewall
                ;;
            9)
                check_backup
                ;;
            10)
                check_monitoring
                ;;
            11)
                repair_common_issues
                ;;
            12)
                restart_services
                ;;
            13)
                check_updates
                ;;
            14)
                full_diagnostic
                ;;
            15)
                log "Saindo do script de troubleshooting..."
                exit 0
                ;;
            *)
                error "Opção inválida. Digite um número de 1 a 15."
                ;;
        esac
        
        echo ""
        read -p "Pressione Enter para continuar..."
    done
}

# Executar função principal
main "$@" 