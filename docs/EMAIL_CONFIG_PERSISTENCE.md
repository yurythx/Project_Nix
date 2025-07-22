# 📧 Configuração de Email - Persistência

## 🔍 **Problema Identificado**

As configurações de email no FireFlies CMS são salvas corretamente no banco de dados e aplicadas dinamicamente, mas **não persistem após reinicializar o servidor Django**.

### **Por que isso acontece?**

1. **Carregamento único do settings.py**: O Django carrega as configurações do `settings.py` apenas na inicialização
2. **Variáveis de ambiente**: Mesmo que o `.env` seja atualizado, as variáveis já foram carregadas na memória
3. **Aplicação dinâmica temporária**: Mudanças no `settings.py` em tempo de execução são perdidas na reinicialização

## ✅ **Soluções Implementadas**

### **1. Melhorias no Serviço de Email**

O `DynamicEmailConfigService` foi aprimorado para:

- **Salvar no banco**: Configurações são persistidas no repositório
- **Aplicar dinamicamente**: Configurações são aplicadas em tempo real
- **Atualizar .env**: Arquivo `.env` é atualizado automaticamente
- **Recarregar configurações**: Força recarregamento do `.env` após salvar

### **2. Interface Melhorada**

- **Alerta informativo**: Explica sobre a necessidade de reinicialização
- **Botão de sincronização**: Permite sincronizar configurações manualmente
- **Feedback visual**: Mostra status das operações

### **3. Comando de Gerenciamento**

```bash
# Sincronizar configurações do banco para .env
python manage.py sync_email_config

# Com usuário específico
python manage.py sync_email_config --user admin

# Forçar sincronização
python manage.py sync_email_config --force
```

## 🛠️ **Como Usar**

### **Opção 1: Reinicialização Manual (Recomendada)**
1. Configure o email na interface
2. Salve as configurações
3. **Reinicie o servidor Django**:
   ```bash
   # Parar servidor (Ctrl+C)
   python manage.py runserver
   ```

### **Opção 2: Sincronização Automática**
1. Configure o email na interface
2. Salve as configurações
3. Clique no botão **"Sincronizar"** na interface
4. Reinicie o servidor Django

### **Opção 3: Comando de Linha**
```bash
# Após configurar via interface
python manage.py sync_email_config
python manage.py runserver
```

## 🔧 **Fluxo de Funcionamento**

```
1. Usuário configura email na interface
   ↓
2. Configurações são validadas
   ↓
3. Dados são salvos no banco de dados
   ↓
4. Configurações são aplicadas dinamicamente
   ↓
5. Arquivo .env é atualizado
   ↓
6. Configurações funcionam imediatamente
   ↓
7. Após reinicialização: .env é carregado automaticamente
```

## 📋 **Configurações Suportadas**

- **EMAIL_BACKEND**: Backend de email (SMTP, Console, etc.)
- **EMAIL_HOST**: Servidor SMTP
- **EMAIL_PORT**: Porta do servidor
- **EMAIL_HOST_USER**: Usuário SMTP
- **EMAIL_HOST_PASSWORD**: Senha SMTP
- **EMAIL_USE_TLS**: Usar TLS
- **EMAIL_USE_SSL**: Usar SSL
- **DEFAULT_FROM_EMAIL**: Email padrão de envio
- **EMAIL_TIMEOUT**: Timeout da conexão

## 🚨 **Limitações Técnicas**

### **Por que a reinicialização é necessária?**

1. **Django Settings**: Carregados apenas na inicialização
2. **Variáveis de Ambiente**: Carregadas uma vez na memória
3. **Segurança**: Evita mudanças dinâmicas não autorizadas

### **Alternativas Futuras**

- **Hot Reload**: Implementar recarregamento automático de configurações
- **Signal-based**: Usar signals do Django para recarregar configurações
- **Middleware**: Middleware para interceptar e aplicar configurações

## 🔍 **Troubleshooting**

### **Configurações não persistem**
```bash
# Verificar se o .env foi atualizado
cat .env | grep EMAIL

# Sincronizar manualmente
python manage.py sync_email_config

# Verificar configurações atuais
python manage.py shell -c "
from django.conf import settings
print(f'EMAIL_HOST: {settings.EMAIL_HOST}')
print(f'EMAIL_PORT: {settings.EMAIL_PORT}')
"
```

### **Erro ao sincronizar**
```bash
# Verificar permissões do arquivo .env
ls -la .env

# Verificar logs
tail -f logs/django.log

# Testar configuração
python manage.py shell -c "
from apps.config.services.email_config_service import DynamicEmailConfigService
service = DynamicEmailConfigService()
print(service.get_active_config())
"
```

### **Email não funciona após configuração**
1. Verificar se o servidor foi reiniciado
2. Testar conexão via interface
3. Verificar logs de erro
4. Validar configurações do provedor de email

## 📚 **Referências**

- [Django Email Settings](https://docs.djangoproject.com/en/5.2/topics/email/)
- [Python-dotenv](https://github.com/theskumar/python-dotenv)
- [Django Management Commands](https://docs.djangoproject.com/en/5.2/howto/custom-management-commands/)

---

**Nota**: Este é um comportamento esperado do Django. As configurações são aplicadas corretamente, mas a reinicialização garante que todas as configurações sejam carregadas adequadamente do arquivo `.env`. 