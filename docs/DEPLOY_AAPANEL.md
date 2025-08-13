# Guia de Deploy no aapanel

Este documento fornece um guia passo a passo para implantar o Project Nix em um servidor com painel de controle aapanel.

## 📋 Pré-requisitos

- Acesso ao painel aapanel
- Domínio configurado e apontando para o servidor
- Acesso SSH ao servidor (recomendado)
- Python 3.8+ instalado
- MySQL/MariaDB configurado
- Git instalado

## 🚀 Passo a Passo para Deploy

### 1. Configuração Inicial no aapanel

1. Acesse o painel aapanel
2. Vá para "Sites" > "Adicionar Site"
3. Preencha as informações do domínio
4. Selecione "Criar banco de dados" e anote as credenciais
5. Habilite SSL para o domínio (opcional, mas altamente recomendado)

### 2. Acesso ao Terminal

1. No aapanel, vá para "Terminal" ou use SSH
2. Navegue até o diretório do site:
   ```bash
   cd /www/wwwroot/seu-dominio.com
   ```

### 3. Configuração do Ambiente

```bash
# Clone o repositório (se ainda não tiver feito)
git clone URL_DO_SEU_REPOSITORIO .

# Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux
# OU
venv\Scripts\activate    # Windows

# Instale as dependências
pip install -r requirements.txt
```

### 4. Configuração do Banco de Dados

1. Crie um arquivo `.env` na raiz do projeto com:

```ini
# Configurações do Banco de Dados
DB_ENGINE=django.db.backends.mysql
DB_NAME=nome_do_banco
DB_USER=usuario_do_banco
DB_PASSWORD=senha_do_banco
DB_HOST=localhost
DB_PORT=3306

# Configurações do Django
SECRET_KEY=sua_chave_secreta_aqui
DEBUG=False
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com

# Configurações de Email (opcional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=seu.smtp.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu@email.com
EMAIL_HOST_PASSWORD=sua_senha
DEFAULT_FROM_EMAIL=seu@email.com

# Configurações do Redis (opcional)
REDIS_URL=redis://localhost:6379/0

# Configurações do Celery (opcional)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 5. Aplicando Migrações e Coletando Arquivos Estáticos

```bash
# Aplicar migrações
python manage.py migrate

# Criar superusuário (opcional)
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic --noinput
```

### 6. Configuração do Gunicorn

1. Instale o Gunicorn:
   ```bash
   pip install gunicorn
   ```

2. Crie um arquivo `gunicorn_start.sh` na raiz do projeto:

```bash
#!/bin/bash

NAME="project_nix"
DIR=/www/wwwroot/seu-dominio.com
USER=www
GROUP=www
WORKERS=3
WORKER_CLASS=gevent
WORKER_CONNECTIONS=1000
VENV=$DIR/venv
LOG_DIR=$DIR/logs

# Crie o diretório de logs se não existir
mkdir -p $LOG_DIR

# Execute a aplicação
cd $DIR
source $VENV/bin/activate
exec gunicorn core.wsgi:application \
  --name $NAME \
  --workers $WORKERS \
  --worker-class=$WORKER_CLASS \
  --worker-connections $WORKER_CONNECTIONS \
  --user=$USER \
  --group=$GROUP \
  --bind=127.0.0.1:8000 \
  --log-level=info \
  --access-logfile=$LOG_DIR/access.log \
  --error-logfile=$LOG_DIR/error.log
```

3. Torne o script executável:
   ```bash
   chmod +x gunicorn_start.sh
   ```

### 7. Configuração do Supervisor

1. No aapanel, vá para "Supervisor"
2. Clique em "Adicionar Supervisor"
3. Preencha os campos:
   - Nome: `project_nix`
   - Executar usuário: `www`
   - Diretório de execução: `/www/wwwroot/seu-dominio.com`
   - Arquivo de inicialização: `./gunicorn_start.sh`
   - Diretório de trabalho: `/www/wwwroot/seu-dominio.com`

### 8. Configuração do Nginx

1. No aapanel, vá para "Sites"
2. Encontre seu domínio e clique em "Configuração"
3. Substitua o conteúdo pelo seguinte:

```nginx
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;
    
    # Redirecionar HTTP para HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com www.seu-dominio.com;
    
    # Configurações SSL
    ssl_certificate /www/server/panel/vhost/cert/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /www/server/panel/vhost/cert/seu-dominio.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Arquivos de log
    access_log /www/wwwlogs/seu-dominio.com.log;
    error_log /www/wwwlogs/seu-dominio.com.error.log;
    
    # Configurações do Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Arquivos estáticos
    location /static/ {
        alias /www/wwwroot/seu-dominio.com/staticfiles/;
        expires 30d;
        access_log off;
    }
    
    # Arquivos de mídia
    location /media/ {
        alias /www/wwwroot/seu-dominio.com/media/;
        expires 30d;
        access_log off;
    }
    
    # Bloquear acesso a arquivos sensíveis
    location ~ /\.(?!well-known).* {
        deny all;
    }
    
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 30d;
        add_header Cache-Control "public, no-transform";
        access_log off;
    }
}
```

### 9. Configuração do Celery (Opcional)

1. Crie um arquivo `celery_worker.sh` na raiz do projeto:

```bash
#!/bin/bash

cd /www/wwwroot/seu-dominio.com
source venv/bin/activate
celery -A core worker -l info
```

2. Torne o script executável:
   ```bash
   chmod +x celery_worker.sh
   ```

3. Adicione um novo gerenciador de processos no aapanel:
   - Nome: `celery_worker`
   - Executar usuário: `www`
   - Diretório de execução: `/www/wwwroot/seu-dominio.com`
   - Arquivo de inicialização: `./celery_worker.sh`

### 10. Configuração do Celery Beat (Opcional)

1. Crie um arquivo `celery_beat.sh` na raiz do projeto:

```bash
#!/bin/bash

cd /www/wwwroot/seu-dominio.com
source venv/bin/activate
celery -A core beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

2. Torne o script executável:
   ```bash
   chmod +x celery_beat.sh
   ```

3. Adicione um novo gerenciador de processos no aapanel:
   - Nome: `celery_beat`
   - Executar usuário: `www`
   - Diretório de execução: `/www/wwwroot/seu-dominio.com`
   - Arquivo de inicialização: `./celery_beat.sh`

## 🔧 Solução de Problemas Comuns

### Erros de Permissão

```bash
# Corrigir permissões
export SITE_PATH=/www/wwwroot/seu-dominio.com
chown -R www:www $SITE_PATH
find $SITE_PATH -type d -exec chmod 755 {} \;
find $SITE_PATH -type f -exec chmod 644 {} \;
chmod +x $SITE_PATH/gunicorn_start.sh
chmod +x $SITE_PATH/celery_*.sh
```

### Verificar Logs

- Logs do Gunicorn: `/www/wwwroot/seu-dominio.com/logs/error.log`
- Logs do Nginx: `/www/wwwlogs/seu-dominio.com.error.log`
- Logs do Celery: Verifique no Supervisor do aapanel

### Reiniciar Serviços

```bash
# Reiniciar Nginx
service nginx restart

# Reiniciar Supervisor
service supervisord restart

# Verificar status dos processos
supervisorctl status
```

## 🔄 Atualizando a Aplicação

```bash
cd /www/wwwroot/seu-dominio.com

# Atualizar o código
git pull origin main

# Atualizar dependências
source venv/bin/activate
pip install -r requirements.txt

# Aplicar migrações
python manage.py migrate

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Reiniciar os serviços
supervisorctl restart project_nix
# Se estiver usando Celery
supervisorctl restart celery_worker
supervisorctl restart celery_beat
```

## 📞 Suporte

Em caso de problemas, consulte:
- Logs da aplicação
- Documentação do Django
- Fóruns do aapanel

---

📅 Última atualização: Agosto de 2025
