# 📚 Scripts de Deploy - FireFlies CMS

Este diretório contém scripts automatizados para deploy e configuração do FireFlies CMS na VM Google Cloud.

## 🎯 Visão Geral

Os scripts assumem que você já tem:
- ✅ VM criada no Google Cloud
- ✅ Conexão SSH estabelecida
- ✅ Acesso root/sudo na VM

## 📁 Scripts Disponíveis

### 1. `deploy_gcp.sh` - Deploy Principal
**Função**: Deploy completo do FireFlies CMS na VM

**O que faz**:
- Atualiza o sistema
- Instala Python 3.11, PostgreSQL, Redis, Nginx
- Configura usuário deploy
- Clona e configura a aplicação
- Configura Gunicorn e systemd
- Configura Nginx e SSL
- Configura monitoramento e backup básico

**Como usar**:
```bash
# Conectar via SSH na VM
ssh usuario@IP_DA_VM

# Executar o script
bash deploy_gcp.sh
```

### 2. `post_deploy_setup.sh` - Configuração Avançada
**Função**: Configurações avançadas após o deploy inicial

**O que faz**:
- Monitoramento avançado com sysstat
- Backup avançado com metadados
- SSL avançado com configurações de segurança
- Configuração de email
- Configuração de domínio
- Segurança com fail2ban e auditoria
- Logs estruturados
- Otimizações de performance
- Backup na nuvem (rclone)
- Notificações automáticas

**Como usar**:
```bash
# Executar após o deploy principal
bash post_deploy_setup.sh
```

### 3. `troubleshooting.sh` - Diagnóstico e Reparo
**Função**: Menu interativo para diagnóstico e reparo

**O que faz**:
- Verificar status dos serviços
- Verificar logs de erro
- Verificar conectividade
- Verificar recursos do sistema
- Verificar configurações
- Verificar banco de dados
- Verificar SSL/HTTPS
- Verificar firewall
- Verificar backup
- Verificar monitoramento
- Reparar problemas comuns
- Reiniciar serviços
- Verificar atualizações
- Diagnóstico completo

**Como usar**:
```bash
# Executar para diagnóstico
bash troubleshooting.sh
```

## 🚀 Fluxo de Deploy Recomendado

### Passo 1: Preparação
```bash
# 1. Criar VM no Google Cloud Console
# 2. Conectar via SSH
ssh usuario@IP_DA_VM

# 3. Baixar scripts (se necessário)
wget https://raw.githubusercontent.com/seu-usuario/fireflies/main/scripts/deploy_gcp.sh
wget https://raw.githubusercontent.com/seu-usuario/fireflies/main/scripts/post_deploy_setup.sh
wget https://raw.githubusercontent.com/seu-usuario/fireflies/main/scripts/troubleshooting.sh
```

### Passo 2: Deploy Principal
```bash
# Executar deploy principal
bash deploy_gcp.sh
```

### Passo 3: Configuração Avançada
```bash
# Executar configuração avançada
bash post_deploy_setup.sh
```

### Passo 4: Verificação
```bash
# Executar troubleshooting para verificar
bash troubleshooting.sh
```

## 📋 Pré-requisitos

### VM Google Cloud
- **Sistema**: Ubuntu 22.04 LTS
- **Recursos**: e2-medium (2 vCPU, 4 GB RAM)
- **Disco**: 20 GB SSD
- **Rede**: IP público configurado

### Informações Necessárias
- IP da VM
- Domínio (opcional)
- Email para notificações
- Senha do banco de dados
- Credenciais do admin

## 🔧 Configurações

### Variáveis de Ambiente
Os scripts solicitam as seguintes informações:

**Deploy Principal**:
- IP da VM
- Domínio
- Senha do banco de dados
- Email para notificações
- Senha do email (App Password)

**Configuração Avançada**:
- Domínio configurado
- Email para notificações
- Senha do email
- Nome do usuário admin
- Email do admin
- Senha do admin

## 📊 Monitoramento

### Scripts de Monitoramento
- `/home/deploy/monitor.sh` - Monitoramento básico
- `/home/deploy/advanced_monitor.sh` - Monitoramento avançado
- `/home/deploy/notifications.sh` - Notificações automáticas

### Logs
- `/var/log/fireflies/django.log` - Logs do Django
- `/var/log/nginx/` - Logs do Nginx
- `/home/deploy/monitor.log` - Logs de monitoramento
- `/home/deploy/backup.log` - Logs de backup

## 💾 Backup

### Scripts de Backup
- `/home/deploy/backup.sh` - Backup básico
- `/home/deploy/advanced_backup.sh` - Backup avançado
- `/home/deploy/cloud_backup.sh` - Backup na nuvem

### Agendamento
- Backup básico: Diariamente às 3:00 AM
- Backup avançado: Diariamente às 2:00 AM
- Monitoramento: A cada 5-10 minutos

## 🔒 Segurança

### Configurações Aplicadas
- UFW (firewall)
- Fail2ban (proteção contra ataques)
- SSL/TLS com configurações seguras
- Atualizações automáticas
- Auditoria do sistema

### Verificações de Segurança
```bash
# Verificar firewall
sudo ufw status

# Verificar fail2ban
sudo fail2ban-client status

# Verificar atualizações
sudo unattended-upgrade --dry-run
```

## 🛠️ Manutenção

### Comandos Úteis
```bash
# Verificar status dos serviços
sudo systemctl status fireflies nginx postgresql redis-server

# Verificar logs
sudo journalctl -u fireflies -f

# Fazer deploy manual
sudo su - deploy
cd fireflies
./deploy.sh

# Fazer backup manual
sudo su - deploy
./advanced_backup.sh

# Verificar monitoramento
sudo su - deploy
./advanced_monitor.sh
```

### Atualizações
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Atualizar aplicação
sudo su - deploy
cd fireflies
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart fireflies
```

## 🔍 Troubleshooting

### Problemas Comuns

**1. Aplicação não inicia**
```bash
# Verificar logs
sudo journalctl -u fireflies -n 50

# Verificar configuração
sudo nginx -t

# Reiniciar serviços
sudo systemctl restart fireflies nginx
```

**2. Banco de dados não conecta**
```bash
# Verificar PostgreSQL
sudo systemctl status postgresql

# Testar conexão
sudo -u deploy psql -h localhost -U deploy -d fireflies
```

**3. SSL não funciona**
```bash
# Verificar certificados
sudo certbot certificates

# Renovar certificados
sudo certbot renew
```

**4. Backup não funciona**
```bash
# Verificar permissões
ls -la /home/deploy/backup.sh

# Executar manualmente
sudo su - deploy
./advanced_backup.sh
```

### Diagnóstico Completo
```bash
# Executar diagnóstico completo
bash troubleshooting.sh
# Escolher opção 14
```

## 📞 Suporte

### Logs Importantes
- `/var/log/fireflies/django.log` - Erros da aplicação
- `/var/log/nginx/error.log` - Erros do Nginx
- `/var/log/postgresql/` - Logs do PostgreSQL
- `/var/log/redis/` - Logs do Redis

### Comandos de Diagnóstico
```bash
# Status geral
sudo systemctl status fireflies nginx postgresql redis-server

# Logs em tempo real
sudo journalctl -u fireflies -f

# Recursos do sistema
htop
df -h
free -h

# Conectividade
curl -I http://localhost/health/
```

## 📚 Documentação Adicional

- [Guia de Deploy Completo](../docs/DEPLOY_GCP_GUIDE.md)
- [Resumo do Deploy](../docs/DEPLOY_SUMMARY.md)
- [Arquitetura do Sistema](../docs/ARQUITETURA.md)
- [Padrões SOLID](../docs/SOLID_PATTERNS_GUIDE.md)

## ⚠️ Importante

1. **Backup**: Sempre faça backup antes de atualizações
2. **Testes**: Teste em ambiente de desenvolvimento primeiro
3. **Monitoramento**: Configure alertas para problemas críticos
4. **Segurança**: Mantenha o sistema atualizado
5. **Documentação**: Documente mudanças importantes

---

**🎉 Com estes scripts, você tem um deploy completo e automatizado do FireFlies CMS!** 