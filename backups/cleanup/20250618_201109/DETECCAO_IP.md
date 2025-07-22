# 🔍 Detecção Automática de IP - FireFlies

## Visão Geral

O sistema FireFlies agora inclui **detecção automática de IP** que garante acesso à aplicação via IP local, hostname e localhost, configurando automaticamente todas as configurações de rede necessárias.

## ✨ Funcionalidades Implementadas

### 🔍 Detecção Inteligente de IP
- **Múltiplos métodos de detecção** para máxima compatibilidade
- **Fallback automático** para serviços externos se necessário
- **Detecção de hostname** da máquina
- **Validação de IP** para garantir formato correto

### 🌐 Configuração Automática de Rede
- **ALLOWED_HOSTS** configurado automaticamente
- **CSRF_TRUSTED_ORIGINS** configurado automaticamente
- **Firewall** configurado com regras específicas
- **Health checks** em múltiplos endereços

### 🚀 Deploy Inteligente
- **Detecção automática** durante o deploy
- **Atualização de configurações** existentes
- **Verificação de saúde** em múltiplos endpoints
- **Relatórios detalhados** de configuração

## 🔧 Métodos de Detecção de IP

### 1. Comando `ip route` (Recomendado)
```bash
ip route get 1.1.1.1 | grep -oP 'src \K\S+'
```
- **Mais moderno e confiável**
- **Funciona em sistemas Linux recentes**
- **Detecta IP da interface ativa**

### 2. Comando `hostname -I`
```bash
hostname -I | awk '{print $1}'
```
- **Específico para Ubuntu/Debian**
- **Rápido e eficiente**
- **Retorna primeiro IP**

### 3. Comando `ifconfig` (Fallback)
```bash
ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'
```
- **Compatível com sistemas mais antigos**
- **Fallback quando outros métodos falham**
- **Filtra localhost automaticamente**

### 4. Serviços Externos (Último recurso)
- **ifconfig.me**
- **icanhazip.com**
- **ipinfo.io/ip**
- **ipecho.net/plain**

## 📋 Configurações Automáticas

### ALLOWED_HOSTS
```
localhost,127.0.0.1,0.0.0.0,SEU_IP,SEU_HOSTNAME
```

### CSRF_TRUSTED_ORIGINS
```
http://localhost:8000,http://127.0.0.1:8000,http://SEU_IP:8000,http://SEU_HOSTNAME:8000
```

### Firewall (UFW)
```bash
# Regras automáticas criadas
sudo ufw allow ssh
sudo ufw allow 8000/tcp
sudo ufw allow 8001/tcp
sudo ufw allow 5432/tcp
sudo ufw allow 6379/tcp
sudo ufw allow from SEU_IP to any port 8000
sudo ufw allow from SEU_IP to any port 8001
```

## 🚀 Scripts Atualizados

### 1. `deploy.sh`
- ✅ Detecção automática de IP
- ✅ Configuração automática de rede
- ✅ Health checks em múltiplos endpoints
- ✅ Atualização de configurações existentes
- ✅ Relatórios detalhados

### 2. `install_ubuntu.sh`
- ✅ Detecção de IP durante instalação
- ✅ Configuração de firewall específica
- ✅ Criação de arquivo .env com configurações de rede
- ✅ Verificação de conectividade

### 3. `test_network.sh` (Novo)
- ✅ Teste completo de configuração de rede
- ✅ Verificação de conectividade
- ✅ Relatório detalhado de rede
- ✅ Diagnóstico de problemas

## 🌐 Endereços de Acesso

Após o deploy, a aplicação estará disponível em:

```
🌐 Local: http://localhost:8000
🌐 IP Local: http://SEU_IP:8000
🌐 Hostname: http://SEU_HOSTNAME:8000
```

## 🔍 Health Checks Inteligentes

### Primeira Instalação
Testa acesso ao wizard de configuração em:
- `http://localhost:8000/config/setup/`
- `http://127.0.0.1:8000/config/setup/`
- `http://SEU_IP:8000/config/setup/`

### Instalação Normal
Testa acesso à aplicação em:
- `http://localhost:8000/health/`
- `http://127.0.0.1:8000/health/`
- `http://SEU_IP:8000/health/`

## 📊 Comandos de Teste

### Verificar Detecção de IP
```bash
./test_network.sh
```

### Verificar Pré-requisitos
```bash
./deploy.sh --check-only
```

### Deploy com Detecção Automática
```bash
./deploy.sh
```

### Deploy em Produção
```bash
./deploy.sh --env production
```

## 🔧 Configuração Manual

### Atualizar IP Manualmente
```bash
# Editar .env
MACHINE_IP=192.168.1.100
MACHINE_HOSTNAME=meu-servidor

# Atualizar ALLOWED_HOSTS
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,192.168.1.100,meu-servidor

# Atualizar CSRF_TRUSTED_ORIGINS
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,http://192.168.1.100:8000,http://meu-servidor:8000
```

### Configurar Rede Local
```bash
# Permitir acesso da rede local
sudo ufw allow from 192.168.1.0/24 to any port 8000
sudo ufw allow from 192.168.1.0/24 to any port 8001

# Adicionar rede ao ALLOWED_HOSTS
echo "ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,SEU_IP,SEU_HOSTNAME,192.168.1.0/24" >> .env
```

## 🐛 Troubleshooting

### IP Não Detectado
```bash
# Verificar métodos disponíveis
ip route get 1.1.1.1
hostname -I
ifconfig

# Testar conectividade
ping -c 3 8.8.8.8
```

### Acesso Negado
```bash
# Verificar ALLOWED_HOSTS
cat .env | grep ALLOWED_HOSTS

# Verificar firewall
sudo ufw status

# Testar conectividade
./test_network.sh
```

### Problemas de Rede
```bash
# Verificar interfaces
ip addr show

# Verificar rotas
ip route

# Verificar DNS
cat /etc/resolv.conf
```

## 📈 Benefícios

### ✅ Automatização Completa
- **Zero configuração manual** de rede
- **Detecção inteligente** de IP
- **Configuração automática** de segurança

### ✅ Compatibilidade Máxima
- **Múltiplos métodos** de detecção
- **Fallback automático** para diferentes cenários
- **Suporte a diferentes distribuições**

### ✅ Segurança Aprimorada
- **Firewall configurado** automaticamente
- **CSRF protegido** com origens corretas
- **ALLOWED_HOSTS** configurado adequadamente

### ✅ Facilidade de Uso
- **Deploy com um comando**
- **Health checks automáticos**
- **Relatórios detalhados**

## 🎯 Casos de Uso

### Desenvolvimento Local
```bash
./deploy.sh
# Acesso via localhost e IP local
```

### Servidor Local
```bash
./deploy.sh --env production
# Acesso via IP local e hostname
```

### Rede Corporativa
```bash
# Configurar rede local manualmente
# Acesso via IP da rede corporativa
```

### Cloud/Produção
```bash
./deploy.sh --env production
# Acesso via IP público e domínio
```

## 🔮 Próximas Melhorias

- [ ] Detecção automática de domínio
- [ ] Configuração automática de SSL
- [ ] Load balancer automático
- [ ] Monitoramento de rede
- [ ] Backup automático de configurações

---

**FireFlies** - Sistema de gerenciamento de conteúdo com detecção automática de IP 🚀

**Funcionalidades de Rede:**
- 🔍 Detecção automática de IP
- 🌐 Configuração automática de ALLOWED_HOSTS
- 🔒 Configuração automática de CSRF_TRUSTED_ORIGINS
- 🚀 Deploy automatizado com Docker
- 📊 Health checks em múltiplos endereços 