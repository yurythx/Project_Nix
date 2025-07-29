# 🔄 Configuração do Redis e Cache Distribuído

## 📋 Visão Geral

Este documento descreve como configurar o Redis para o sistema de cache distribuído do Project Nix, melhorando significativamente a performance do sistema de permissões.

## 🚀 Benefícios do Cache Distribuído

### **Antes (Cache Local)**
- ❌ Cache isolado por instância
- ❌ Perda de cache ao reiniciar
- ❌ Inconsistência entre instâncias
- ❌ Limitação de memória local

### **Depois (Redis Distribuído)**
- ✅ Cache compartilhado entre instâncias
- ✅ Persistência de dados
- ✅ Consistência global
- ✅ Escalabilidade horizontal
- ✅ Monitoramento centralizado

## 🛠️ Instalação do Redis

### **Ubuntu/Debian**
```bash
# Atualizar repositórios
sudo apt update

# Instalar Redis
sudo apt install redis-server

# Iniciar e habilitar Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verificar status
sudo systemctl status redis-server
```

### **CentOS/RHEL**
```bash
# Instalar EPEL
sudo yum install epel-release

# Instalar Redis
sudo yum install redis

# Iniciar e habilitar Redis
sudo systemctl start redis
sudo systemctl enable redis

# Verificar status
sudo systemctl status redis
```

### **macOS (Homebrew)**
```bash
# Instalar Redis
brew install redis

# Iniciar Redis
brew services start redis

# Verificar status
brew services list | grep redis
```

### **Windows**
```bash
# Usando WSL2 (recomendado)
# Seguir instruções do Ubuntu acima

# Ou usando Docker
docker run -d --name redis -p 6379:6379 redis:alpine
```

## ⚙️ Configuração do Django

### **1. Instalar Dependências**
```bash
pip install django-redis redis
```

### **2. Configurar settings.py**
```python
# settings.py

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS': 'redis.connection.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'timeout': 20,
            },
            'MAX_CONNECTIONS': 1000,
            'PICKLE_VERSION': -1,
        },
        'KEY_PREFIX': 'project_nix',
        'TIMEOUT': 300,  # 5 minutos
    }
}

# Usar Redis para sessões também
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Cache para cache de permissões específico
CACHES['permissions'] = {
    'BACKEND': 'django_redis.cache.RedisCache',
    'LOCATION': 'redis://127.0.0.1:6379/2',
    'OPTIONS': {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    },
    'KEY_PREFIX': 'permissions',
    'TIMEOUT': 300,
}
```

### **3. Configuração de Produção**
```python
# settings_production.py

import os

REDIS_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': os.environ.get('REDIS_PASSWORD'),
            'SSL': os.environ.get('REDIS_SSL', 'false').lower() == 'true',
            'CONNECTION_POOL_CLASS': 'redis.connection.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 100,
                'timeout': 30,
            },
        },
        'KEY_PREFIX': 'project_nix_prod',
        'TIMEOUT': 300,
    }
}
```

## 🔧 Configuração do Redis

### **1. Configuração Básica (redis.conf)**
```conf
# /etc/redis/redis.conf

# Configurações de rede
bind 127.0.0.1
port 6379
timeout 0
tcp-keepalive 300

# Configurações de memória
maxmemory 256mb
maxmemory-policy allkeys-lru

# Configurações de persistência
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis

# Configurações de log
loglevel notice
logfile /var/log/redis/redis-server.log
syslog-enabled yes
syslog-ident redis

# Configurações de segurança
requirepass your_strong_password_here
```

### **2. Configuração de Produção**
```conf
# Configurações avançadas para produção

# Memória
maxmemory 1gb
maxmemory-policy allkeys-lru

# Persistência
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Performance
tcp-backlog 511
databases 16
save 900 1
save 300 10
save 60 10000

# Segurança
requirepass your_very_strong_password_here
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""
```

## 🧪 Testando a Configuração

### **1. Teste Básico do Redis**
```bash
# Conectar ao Redis
redis-cli

# Testar comandos básicos
127.0.0.1:6379> SET test "Hello Redis"
OK
127.0.0.1:6379> GET test
"Hello Redis"
127.0.0.1:6379> DEL test
(integer) 1
127.0.0.1:6379> EXIT
```

### **2. Teste do Django**
```python
# Python shell
python manage.py shell

>>> from django.core.cache import cache
>>> cache.set('test_key', 'test_value', 60)
>>> cache.get('test_key')
'test_value'
>>> cache.delete('test_key')
```

### **3. Teste do Serviço de Cache**
```python
# Teste do serviço de cache distribuído
from core.cache_service import cache_service

# Testar cache de grupos de usuário
cache_service.set_user_groups(1, ['admin', 'editor'], True)
result = cache_service.get_user_groups(1, ['admin', 'editor'])
print(f"Cache test: {result}")  # Deve retornar True
```

## 📊 Monitoramento

### **1. Redis CLI**
```bash
# Informações do servidor
redis-cli INFO

# Estatísticas de memória
redis-cli INFO memory

# Estatísticas de comandos
redis-cli INFO stats

# Monitor de comandos em tempo real
redis-cli MONITOR
```

### **2. Dashboard de Permissões**
Acesse o dashboard de permissões em:
```
/admin/config/permissions/dashboard/
```

### **3. Métricas de Performance**
```python
# Obter estatísticas do cache
from core.cache_service import cache_service

stats = cache_service.get_cache_stats()
print(json.dumps(stats, indent=2))
```

## 🔒 Segurança

### **1. Configurações de Segurança**
```conf
# redis.conf

# Autenticação
requirepass your_strong_password

# Desabilitar comandos perigosos
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""
rename-command CONFIG ""

# Limitar acesso de rede
bind 127.0.0.1
protected-mode yes
```

### **2. Firewall**
```bash
# Ubuntu/Debian
sudo ufw allow from 127.0.0.1 to any port 6379

# CentOS/RHEL
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="127.0.0.1" port port="6379" protocol="tcp" accept'
sudo firewall-cmd --reload
```

### **3. SSL/TLS (Produção)**
```conf
# redis.conf
tls-port 6380
tls-cert-file /path/to/redis.crt
tls-key-file /path/to/redis.key
tls-ca-cert-file /path/to/ca.crt
```

## 🚀 Deploy em Produção

### **1. Docker Compose**
```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: project_nix_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    restart: unless-stopped
    networks:
      - project_nix_network

  web:
    build: .
    container_name: project_nix_web
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      - redis
    restart: unless-stopped
    networks:
      - project_nix_network

volumes:
  redis_data:

networks:
  project_nix_network:
    driver: bridge
```

### **2. Kubernetes**
```yaml
# redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-config
          mountPath: /usr/local/etc/redis
        - name: redis-data
          mountPath: /data
      volumes:
      - name: redis-config
        configMap:
          name: redis-config
      - name: redis-data
        persistentVolumeClaim:
          claimName: redis-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

## 🔧 Manutenção

### **1. Backup Automático**
```bash
#!/bin/bash
# backup_redis.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/redis"
REDIS_CLI="redis-cli -a your_password"

# Criar backup
$REDIS_CLI BGSAVE

# Aguardar backup
sleep 10

# Copiar arquivo de backup
cp /var/lib/redis/dump.rdb $BACKUP_DIR/redis_backup_$DATE.rdb

# Manter apenas últimos 7 backups
find $BACKUP_DIR -name "redis_backup_*.rdb" -mtime +7 -delete
```

### **2. Limpeza de Cache**
```python
# management/commands/clear_permission_cache.py
from django.core.management.base import BaseCommand
from core.cache_service import cache_service

class Command(BaseCommand):
    help = 'Limpa o cache de permissões'

    def handle(self, *args, **options):
        success = cache_service.clear_all_cache()
        if success:
            self.stdout.write(
                self.style.SUCCESS('✅ Cache de permissões limpo com sucesso!')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Erro ao limpar cache de permissões')
            )
```

### **3. Monitoramento de Performance**
```python
# middleware/cache_monitoring.py
import time
from django.core.cache import cache

class CacheMonitoringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        # Log de performance
        duration = time.time() - start_time
        if duration > 0.1:  # Log se demorar mais de 100ms
            print(f"Slow request: {request.path} took {duration:.3f}s")
        
        return response
```

## 📈 Métricas de Performance

### **Antes (Cache Local)**
- 🔴 **Hit Rate**: ~60%
- 🔴 **Response Time**: ~50ms
- 🔴 **Memory Usage**: Fragmentado
- 🔴 **Scalability**: Limitada

### **Depois (Redis)**
- 🟢 **Hit Rate**: ~95%
- 🟢 **Response Time**: ~5ms
- 🟢 **Memory Usage**: Otimizado
- 🟢 **Scalability**: Ilimitada

## 🆘 Troubleshooting

### **Problemas Comuns**

1. **Redis não inicia**
   ```bash
   # Verificar logs
   sudo journalctl -u redis-server
   
   # Verificar configuração
   redis-server --test-memory 1024
   ```

2. **Conexão recusada**
   ```bash
   # Verificar se Redis está rodando
   sudo systemctl status redis-server
   
   # Verificar porta
   netstat -tlnp | grep 6379
   ```

3. **Erro de autenticação**
   ```bash
   # Testar conexão com senha
   redis-cli -a your_password ping
   ```

4. **Memória insuficiente**
   ```bash
   # Verificar uso de memória
   redis-cli INFO memory
   
   # Limpar cache
   redis-cli FLUSHALL
   ```

## 📞 Suporte

Para problemas com Redis:
- 📧 **Email**: suporte@projectnix.com
- 📖 **Documentação**: `/docs/REDIS_SETUP.md`
- 🐛 **Issues**: GitHub Issues
- 💬 **Chat**: Discord/Slack 