#!/bin/bash

# FireFlies - Script de Instalação para Ubuntu/Debian
# Instala todos os pré-requisitos necessários para o deploy
# Inclui detecção automática de IP e configuração de rede

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

# Função para detectar IP da máquina
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

# Função para verificar se é root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "❌ Este script não deve ser executado como root"
        error "   Execute como usuário normal e use sudo quando necessário"
        exit 1
    fi
}

# Função para verificar distribuição
check_distribution() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
            warn "⚠️ Este script foi testado em Ubuntu/Debian"
            warn "   Sua distribuição: $PRETTY_NAME"
            read -p "Continuar mesmo assim? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
        log "✅ Distribuição detectada: $PRETTY_NAME"
    else
        warn "⚠️ Não foi possível detectar a distribuição"
    fi
}

# Função para atualizar sistema
update_system() {
    log "🔄 Atualizando sistema..."
    sudo apt update
    sudo apt upgrade -y
    log "✅ Sistema atualizado"
}

# Função para instalar Python
install_python() {
    log "🐍 Instalando Python..."
    
    # Verificar se Python já está instalado
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        log "✅ Python $PYTHON_VERSION já está instalado"
        return 0
    fi
    
    # Instalar Python 3.12 ou versão mais recente
    sudo apt install -y python3 python3-pip python3-venv python3-dev
    
    # Verificar instalação
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    log "✅ Python $PYTHON_VERSION instalado"
    
    # Atualizar pip
    python3 -m pip install --upgrade pip
    log "✅ pip atualizado"
}

# Função para instalar Docker
install_docker() {
    log "🐳 Instalando Docker..."
    
    # Verificar se Docker já está instalado
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        log "✅ Docker $DOCKER_VERSION já está instalado"
    else
        # Instalar Docker
        sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release
        
        # Adicionar repositório oficial do Docker
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        sudo apt update
        sudo apt install -y docker-ce docker-ce-cli containerd.io
        
        # Verificar instalação
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        log "✅ Docker $DOCKER_VERSION instalado"
    fi
    
    # Adicionar usuário ao grupo docker
    if ! groups $USER | grep -q docker; then
        sudo usermod -aG docker $USER
        log "✅ Usuário adicionado ao grupo docker"
        warn "⚠️ Faça logout e login novamente para aplicar as mudanças"
    fi
    
    # Iniciar e habilitar Docker
    sudo systemctl start docker
    sudo systemctl enable docker
    log "✅ Docker iniciado e habilitado"
}

# Função para instalar Docker Compose
install_docker_compose() {
    log "🐙 Instalando Docker Compose..."
    
    # Verificar se Docker Compose já está instalado
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
        log "✅ Docker Compose $COMPOSE_VERSION já está instalado"
        return 0
    fi
    
    # Instalar Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Verificar instalação
    COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
    log "✅ Docker Compose $COMPOSE_VERSION instalado"
}

# Função para instalar ferramentas adicionais
install_tools() {
    log "🔧 Instalando ferramentas adicionais..."
    
    # Lista de ferramentas úteis
    tools=(
        "lsof"           # Para detecção de portas
        "curl"           # Para health checks
        "git"            # Para controle de versão
        "htop"           # Monitor de sistema
        "tree"           # Visualização de diretórios
        "jq"             # Processamento JSON
        "vim"            # Editor de texto
        "unzip"          # Descompactação
        "wget"           # Download de arquivos
        "net-tools"      # ifconfig, netstat
        "iproute2"       # Comandos ip modernos
    )
    
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            sudo apt install -y "$tool"
            log "✅ $tool instalado"
        else
            log "ℹ️ $tool já está instalado"
        fi
    done
}

# Função para configurar firewall
configure_firewall() {
    log "🔥 Configurando firewall..."

    # --- Bloco seguro para firewall ---
    echo "[🔐] Configurando firewall com UFW..."

    sudo ufw allow 22       # SSH
    sudo ufw allow 80       # HTTP
    sudo ufw allow 443      # HTTPS

    # Só libera a porta 8000 se ainda não estiver liberada
    if ! sudo ufw status | grep -q "8000"; then
      sudo ufw allow 8000   # Django local
    fi

    sudo ufw --force enable
    sudo ufw status verbose
    # --- Fim do bloco seguro ---
}

# Função para criar diretórios do projeto
create_project_dirs() {
    log "📁 Criando diretórios do projeto..."
    
    # Diretórios necessários
    dirs=(
        "logs"
        "media"
        "staticfiles"
        "backups"
        "temp"
    )
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log "✅ Diretório $dir criado"
        else
            log "ℹ️ Diretório $dir já existe"
        fi
    done
}

# Função para configurar permissões
setup_permissions() {
    log "🔐 Configurando permissões..."
    
    # Dar permissão de execução aos scripts
    chmod +x deploy.sh
    chmod +x docker/entrypoint.sh
    chmod +x docker/start.sh
    
    log "✅ Permissões configuradas"
}

# Função para criar arquivo de configuração de rede
create_network_config() {
    log "🌐 Criando configuração de rede..."
    
    local machine_ip=$(detect_machine_ip)
    local machine_hostname=$(detect_machine_hostname)
    
    # Criar arquivo .env se não existir
    if [[ ! -f .env ]]; then
        cat > .env << EOF
# FireFlies Network Configuration
# Gerado automaticamente pelo install_ubuntu.sh

# Machine Information
MACHINE_IP=$machine_ip
MACHINE_HOSTNAME=$machine_hostname

# Network Configuration
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,$machine_ip,$machine_hostname
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,http://$machine_ip:8000,http://$machine_hostname:8000

# Development Server
DJANGO_HOST=0.0.0.0
DJANGO_PORT=8000

# Docker Configuration
DOCKER_COMPOSE_PROJECT_NAME=fireflies
DOCKER_HOST_IP=$machine_ip

# Production Server (Gunicorn)
GUNICORN_BIND=0.0.0.0:8000
GUNICORN_WORKERS=auto
GUNICORN_WORKER_CLASS=sync
GUNICORN_TIMEOUT=30
GUNICORN_LOG_LEVEL=info
EOF
        log "✅ Arquivo .env criado com configurações de rede"
    else
        log "ℹ️ Arquivo .env já existe, mantendo configurações"
    fi
}

# Função para verificar instalação
verify_installation() {
    log "🔍 Verificando instalação..."
    
    local all_good=true
    
    # Verificar Python
    if command -v python3 &> /dev/null; then
        log "✅ Python: OK"
    else
        error "❌ Python: FALHOU"
        all_good=false
    fi
    
    # Verificar Docker
    if command -v docker &> /dev/null; then
        log "✅ Docker: OK"
    else
        error "❌ Docker: FALHOU"
        all_good=false
    fi
    
    # Verificar Docker Compose
    if command -v docker-compose &> /dev/null; then
        log "✅ Docker Compose: OK"
    else
        error "❌ Docker Compose: FALHOU"
        all_good=false
    fi
    
    # Verificar lsof
    if command -v lsof &> /dev/null; then
        log "✅ lsof: OK"
    else
        error "❌ lsof: FALHOU"
        all_good=false
    fi
    
    # Verificar curl
    if command -v curl &> /dev/null; then
        log "✅ curl: OK"
    else
        error "❌ curl: FALHOU"
        all_good=false
    fi
    
    # Verificar IP
    local machine_ip=$(detect_machine_ip)
    if [[ -n "$machine_ip" ]]; then
        log "✅ Detecção de IP: OK ($machine_ip)"
    else
        error "❌ Detecção de IP: FALHOU"
        all_good=false
    fi
    
    if [[ "$all_good" == "true" ]]; then
        log "🎉 Todas as verificações passaram!"
        return 0
    else
        error "❌ Algumas verificações falharam"
        return 1
    fi
}

# Função para mostrar próximos passos
show_next_steps() {
    log "🎯 Próximos passos:"
    echo ""
    
    # Detectar IP para mostrar informações de acesso
    local machine_ip=$(detect_machine_ip)
    local machine_hostname=$(detect_machine_hostname)
    
    echo "1. 🔄 Faça logout e login novamente para aplicar as mudanças do Docker"
    echo "2. 🚀 Execute o deploy: ./deploy.sh"
    echo "3. 🌐 Acesse a aplicação:"
    echo "   - Local: http://localhost:8000"
    echo "   - IP Local: http://$machine_ip:8000"
    echo "   - Hostname: http://$machine_hostname:8000"
    echo ""
    echo "📚 Comandos úteis:"
    echo "   ./deploy.sh --help          # Ver opções"
    echo "   ./deploy.sh --check-only    # Verificar pré-requisitos"
    echo "   docker ps                   # Ver containers"
    echo "   docker-compose logs -f      # Ver logs"
    echo ""
    echo "🔧 Configurações de rede:"
    echo "   IP da máquina: $machine_ip"
    echo "   Hostname: $machine_hostname"
    echo "   ALLOWED_HOSTS: localhost,127.0.0.1,0.0.0.0,$machine_ip,$machine_hostname"
    echo ""
    echo "📖 Documentação:"
    echo "   https://docs.docker.com/"
    echo "   https://docs.djangoproject.com/"
    echo ""
}

# Função principal
main() {
    log "🎯 Iniciando instalação do FireFlies no Ubuntu..."
    
    # Verificações iniciais
    check_root
    check_distribution
    
    # Instalação
    update_system
    install_python
    install_docker
    install_docker_compose
    install_tools
    configure_firewall
    create_project_dirs
    setup_permissions
    create_network_config
    
    # Verificação final
    if verify_installation; then
        log "🎉 Instalação concluída com sucesso!"
        show_next_steps
    else
        error "❌ Instalação falhou"
        exit 1
    fi
}

# Executar função principal
main "$@" 