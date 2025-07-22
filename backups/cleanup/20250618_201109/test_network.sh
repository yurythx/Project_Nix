#!/bin/bash

# FireFlies - Teste de Configuração de Rede
# Testa a detecção de IP e mostra configurações de rede

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log colorido
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Função para detectar IP da máquina (igual ao deploy.sh)
detect_machine_ip() {
    log "🔍 Detectando IP da máquina..."
    
    local ip_addresses=()
    
    # Tentar diferentes métodos de detecção de IP
    if command -v ip &> /dev/null; then
        # Usar comando ip (mais moderno)
        local ip_cmd_result=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' | head -1)
        if [[ -n "$ip_cmd_result" ]]; then
            ip_addresses+=("$ip_cmd_result")
            log "✅ IP detectado via 'ip route': $ip_cmd_result"
        fi
    fi
    
    if command -v hostname &> /dev/null; then
        # Usar hostname -I
        local hostname_result=$(hostname -I 2>/dev/null | awk '{print $1}')
        if [[ -n "$hostname_result" ]]; then
            ip_addresses+=("$hostname_result")
            log "✅ IP detectado via 'hostname -I': $hostname_result"
        fi
    fi
    
    if command -v ifconfig &> /dev/null; then
        # Usar ifconfig (fallback)
        local ifconfig_result=$(ifconfig 2>/dev/null | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -1)
        if [[ -n "$ifconfig_result" ]]; then
            ip_addresses+=("$ifconfig_result")
            log "✅ IP detectado via 'ifconfig': $ifconfig_result"
        fi
    fi
    
    # Tentar detectar IP via serviços externos (apenas se necessário)
    if [[ ${#ip_addresses[@]} -eq 0 ]]; then
        warn "⚠️ Não foi possível detectar IP local, tentando serviços externos..."
        
        # Tentar diferentes serviços
        local external_services=(
            "ifconfig.me"
            "icanhazip.com"
            "ipinfo.io/ip"
            "ipecho.net/plain"
        )
        
        for service in "${external_services[@]}"; do
            if command -v curl &> /dev/null; then
                local external_ip=$(curl -s --max-time 5 "$service" 2>/dev/null | tr -d '\n\r')
                if [[ -n "$external_ip" ]] && [[ "$external_ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
                    ip_addresses+=("$external_ip")
                    log "✅ IP externo detectado via $service: $external_ip"
                    break
                fi
            fi
        done
    fi
    
    # Se ainda não encontrou, usar localhost
    if [[ ${#ip_addresses[@]} -eq 0 ]]; then
        warn "⚠️ Não foi possível detectar IP, usando localhost"
        ip_addresses+=("127.0.0.1")
    fi
    
    # Retornar o primeiro IP encontrado
    echo "${ip_addresses[0]}"
}

# Função para detectar hostname da máquina
detect_machine_hostname() {
    log "🏷️ Detectando hostname da máquina..."
    
    local hostname=""
    
    # Tentar diferentes métodos
    if command -v hostname &> /dev/null; then
        hostname=$(hostname 2>/dev/null)
    fi
    
    # Se não encontrou, usar um padrão
    if [[ -z "$hostname" ]]; then
        hostname="fireflies-server"
        warn "⚠️ Hostname não detectado, usando padrão: $hostname"
    fi
    
    echo "$hostname"
}

# Função para testar conectividade
test_connectivity() {
    local ip=$1
    local port=$2
    local description=$3
    
    log "🔗 Testando conectividade para $description..."
    
    if command -v nc &> /dev/null; then
        if nc -z -w5 "$ip" "$port" 2>/dev/null; then
            log "✅ Porta $port está aberta em $ip"
            return 0
        else
            warn "⚠️ Porta $port está fechada em $ip"
            return 1
        fi
    elif command -v telnet &> /dev/null; then
        if timeout 5 bash -c "</dev/tcp/$ip/$port" 2>/dev/null; then
            log "✅ Porta $port está aberta em $ip"
            return 0
        else
            warn "⚠️ Porta $port está fechada em $ip"
            return 1
        fi
    else
        warn "⚠️ Não foi possível testar conectividade (nc/telnet não disponível)"
        return 1
    fi
}

# Função para verificar configurações do .env
check_env_config() {
    log "📋 Verificando configurações do .env..."
    
    if [[ ! -f .env ]]; then
        error "❌ Arquivo .env não encontrado"
        return 1
    fi
    
    echo ""
    echo "=== CONFIGURAÇÕES DE REDE ==="
    
    # Verificar MACHINE_IP
    if grep -q "MACHINE_IP=" .env; then
        local env_ip=$(grep "MACHINE_IP=" .env | cut -d'=' -f2)
        log "🌐 MACHINE_IP: $env_ip"
    else
        warn "⚠️ MACHINE_IP não configurado"
    fi
    
    # Verificar MACHINE_HOSTNAME
    if grep -q "MACHINE_HOSTNAME=" .env; then
        local env_hostname=$(grep "MACHINE_HOSTNAME=" .env | cut -d'=' -f2)
        log "🏷️ MACHINE_HOSTNAME: $env_hostname"
    else
        warn "⚠️ MACHINE_HOSTNAME não configurado"
    fi
    
    # Verificar ALLOWED_HOSTS
    if grep -q "ALLOWED_HOSTS=" .env; then
        local allowed_hosts=$(grep "ALLOWED_HOSTS=" .env | cut -d'=' -f2)
        log "✅ ALLOWED_HOSTS: $allowed_hosts"
    else
        warn "⚠️ ALLOWED_HOSTS não configurado"
    fi
    
    # Verificar CSRF_TRUSTED_ORIGINS
    if grep -q "CSRF_TRUSTED_ORIGINS=" .env; then
        local csrf_origins=$(grep "CSRF_TRUSTED_ORIGINS=" .env | cut -d'=' -f2)
        log "🔒 CSRF_TRUSTED_ORIGINS: $csrf_origins"
    else
        warn "⚠️ CSRF_TRUSTED_ORIGINS não configurado"
    fi
    
    # Verificar DJANGO_PORT
    if grep -q "DJANGO_PORT=" .env; then
        local django_port=$(grep "DJANGO_PORT=" .env | cut -d'=' -f2)
        log "🚀 DJANGO_PORT: $django_port"
    else
        warn "⚠️ DJANGO_PORT não configurado"
    fi
    
    echo ""
}

# Função para verificar status dos containers
check_containers() {
    log "🐳 Verificando status dos containers..."
    
    if ! command -v docker &> /dev/null; then
        error "❌ Docker não está instalado"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        error "❌ Docker não está rodando"
        return 1
    fi
    
    echo ""
    echo "=== CONTAINERS DOCKER ==="
    
    # Verificar containers rodando
    local running_containers=$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null)
    if [[ -n "$running_containers" ]]; then
        echo "$running_containers"
    else
        warn "⚠️ Nenhum container rodando"
    fi
    
    echo ""
}

# Função para testar acesso à aplicação
test_application_access() {
    local machine_ip=$1
    local machine_hostname=$2
    
    log "🌐 Testando acesso à aplicação..."
    
    local endpoints=(
        "http://localhost:8000"
        "http://127.0.0.1:8000"
        "http://$machine_ip:8000"
        "http://$machine_hostname:8000"
    )
    
    echo ""
    echo "=== TESTE DE ACESSO ==="
    
    for endpoint in "${endpoints[@]}"; do
        log "🔗 Testando: $endpoint"
        
        if command -v curl &> /dev/null; then
            if curl -f -s -o /dev/null -w "Status: %{http_code}, Tempo: %{time_total}s\n" "$endpoint" 2>/dev/null; then
                log "✅ Acessível: $endpoint"
            else
                warn "⚠️ Inacessível: $endpoint"
            fi
        else
            warn "⚠️ curl não disponível para testar $endpoint"
        fi
    done
    
    echo ""
}

# Função para mostrar informações de rede do sistema
show_network_info() {
    log "🌐 Informações de rede do sistema..."
    
    echo ""
    echo "=== INFORMAÇÕES DE REDE ==="
    
    # Informações de rede
    if command -v ip &> /dev/null; then
        echo "📡 Interfaces de rede:"
        ip addr show | grep -E "inet " | grep -v "127.0.0.1" | awk '{print "  " $2 " (" $7 ")"}'
    fi
    
    # Rota padrão
    if command -v ip &> /dev/null; then
        echo ""
        echo "🛣️ Rota padrão:"
        ip route | grep default | awk '{print "  " $0}'
    fi
    
    # DNS
    if [[ -f /etc/resolv.conf ]]; then
        echo ""
        echo "🔍 Servidores DNS:"
        grep "nameserver" /etc/resolv.conf | awk '{print "  " $2}'
    fi
    
    echo ""
}

# Função para verificar firewall
check_firewall() {
    log "🔥 Verificando configuração de firewall..."
    
    echo ""
    echo "=== FIREWALL ==="
    
    # Verificar ufw
    if command -v ufw &> /dev/null; then
        local ufw_status=$(sudo ufw status 2>/dev/null | head -1)
        if [[ "$ufw_status" == *"active"* ]]; then
            log "✅ UFW ativo"
            echo "📋 Regras UFW:"
            sudo ufw status numbered 2>/dev/null | grep -E "(8000|8001|5432|6379)" || echo "  Nenhuma regra específica encontrada"
        else
            warn "⚠️ UFW inativo"
        fi
    else
        warn "⚠️ UFW não instalado"
    fi
    
    # Verificar iptables
    if command -v iptables &> /dev/null; then
        echo ""
        echo "📋 Regras iptables (portas 8000, 8001):"
        sudo iptables -L -n | grep -E "(8000|8001)" || echo "  Nenhuma regra específica encontrada"
    fi
    
    echo ""
}

# Função para gerar relatório
generate_report() {
    local machine_ip=$1
    local machine_hostname=$2
    
    log "📊 Gerando relatório de rede..."
    
    echo ""
    echo "=========================================="
    echo "           RELATÓRIO DE REDE"
    echo "=========================================="
    echo ""
    
    echo "🖥️ Informações da Máquina:"
    echo "  IP Detectado: $machine_ip"
    echo "  Hostname: $machine_hostname"
    echo "  Sistema: $(uname -a)"
    echo ""
    
    echo "🌐 Endereços de Acesso:"
    echo "  Local: http://localhost:8000"
    echo "  IP Local: http://$machine_ip:8000"
    echo "  Hostname: http://$machine_hostname:8000"
    echo ""
    
    echo "🔧 Configurações Recomendadas:"
    echo "  ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,$machine_ip,$machine_hostname"
    echo "  CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,http://$machine_ip:8000,http://$machine_hostname:8000"
    echo ""
    
    echo "🚀 Comandos Úteis:"
    echo "  ./deploy.sh --check-only    # Verificar pré-requisitos"
    echo "  ./deploy.sh                 # Fazer deploy"
    echo "  docker ps                   # Ver containers"
    echo "  docker-compose logs -f      # Ver logs"
    echo ""
    
    echo "=========================================="
}

# Função principal
main() {
    log "🎯 Iniciando teste de configuração de rede..."
    
    # Detectar informações da máquina
    local machine_ip=$(detect_machine_ip)
    local machine_hostname=$(detect_machine_hostname)
    
    echo ""
    log "🌐 IP da máquina: $machine_ip"
    log "🏷️ Hostname: $machine_hostname"
    echo ""
    
    # Verificar configurações do .env
    check_env_config
    
    # Verificar status dos containers
    check_containers
    
    # Mostrar informações de rede
    show_network_info
    
    # Verificar firewall
    check_firewall
    
    # Testar conectividade
    test_connectivity "localhost" "8000" "localhost:8000"
    test_connectivity "$machine_ip" "8000" "$machine_ip:8000"
    
    # Testar acesso à aplicação
    test_application_access "$machine_ip" "$machine_hostname"
    
    # Gerar relatório final
    generate_report "$machine_ip" "$machine_hostname"
    
    log "✅ Teste de rede concluído!"
}

# Executar função principal
main "$@" 