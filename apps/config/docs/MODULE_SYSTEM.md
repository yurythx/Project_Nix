# Sistema de Módulos do Havoc

## 🎯 Visão Geral

O Sistema de Módulos do Havoc permite controlar quais funcionalidades (apps) estão disponíveis no sistema. Administradores podem habilitar/desabilitar módulos dinamicamente, controlando o acesso dos usuários a diferentes partes da aplicação.

## ✅ PROBLEMA RESOLVIDO

**Antes**: A mensagem "O módulo 'contato' não está disponível no momento" aparecia para páginas simples.

**Depois**: Sistema inteligente que:
- ✅ Reconhece corretamente URLs do app `pages` (contato, sobre, etc.)
- ✅ Permite controle granular de módulos
- ✅ Protege módulos principais (accounts, config, pages)
- ✅ Interface amigável para gerenciamento

## 🏗️ Arquitetura

### **Componentes Principais**

1. **ModuleAccessMiddleware**: Intercepta requisições e verifica permissões
2. **ModuleService**: Lógica de negócio para gerenciamento de módulos
3. **AppModuleConfiguration**: Model que armazena configurações dos módulos
4. **Interface Web**: Painel de controle em `/config/modulos/`

### **Fluxo de Funcionamento**

```
Requisição → Middleware → Verifica App → Verifica Módulo → Permite/Bloqueia
```

## 🔧 Configuração

### **Módulos Principais (Sempre Ativos)**
- `accounts` - Sistema de usuários
- `config` - Painel de administração  
- `pages` - Páginas estáticas e dinâmicas

### **Módulos Opcionais**
- `articles` - Sistema de artigos
- Outros apps personalizados

## 📋 Como Usar

### **1. Acessar Painel de Controle**
```
http://localhost:8000/config/modulos/
```

### **2. Testar Sistema**
```
http://localhost:8000/config/modulos/teste/
```

### **3. Comandos de Gerenciamento**

```bash
# Inicializar sistema de módulos
python manage.py init_modules

# Sincronizar com apps instalados
python manage.py init_modules --sync-only

# Demonstração do sistema
python manage.py demo_modules
```

## 🎮 Funcionalidades

### **Interface Web**
- ✅ Lista todos os módulos
- ✅ Habilitar/desabilitar módulos
- ✅ Visualizar dependências
- ✅ Testar acesso aos módulos
- ✅ Estatísticas em tempo real

### **Proteções**
- ✅ Módulos principais não podem ser desabilitados
- ✅ Verificação de dependências
- ✅ Logs de auditoria
- ✅ Mensagens informativas para usuários

### **Middleware Inteligente**
- ✅ Reconhece URLs do app pages corretamente
- ✅ Mapeia URLs para apps automaticamente
- ✅ Exceções para URLs críticas (login, admin, etc.)
- ✅ Redirecionamento suave com mensagens

## 🔍 Mapeamento de URLs

### **URLs Reconhecidas Automaticamente**
```python
# Apps com prefixo próprio
'/accounts/' → accounts
'/config/' → config  
'/artigos/' → articles

# URLs do app pages
'/contato/' → pages
'/sobre/' → pages
'/privacidade/' → pages
'/termos/' → pages
'/' → pages (home)
```

### **URLs Sempre Permitidas**
```python
exempt_paths = [
    '/admin/',
    '/static/',
    '/media/',
    '/accounts/login/',
    '/accounts/logout/',
    '/accounts/register/',
    '/accounts/password-reset/',
    '/config/',  # Todo o painel
]
```

## 🧪 Testando o Sistema

### **1. Teste Manual**
```bash
# 1. Desabilitar módulo articles
curl -X POST http://localhost:8000/config/modulos/toggle/ \
  -d "module_name=articles"

# 2. Tentar acessar artigos (será redirecionado)
curl http://localhost:8000/artigos/

# 3. Reabilitar módulo
curl -X POST http://localhost:8000/config/modulos/toggle/ \
  -d "module_name=articles"
```

### **2. Teste via Interface**
1. Acesse `/config/modulos/teste/`
2. Use os botões para toggle de módulos
3. Teste URLs em abas separadas
4. Observe mensagens de redirecionamento

## 📊 Monitoramento

### **Logs**
```python
# Logs automáticos em apps/config/services/module_service.py
logger.info(f"Módulo {app_name} habilitado por {user.email}")
logger.error(f"Módulo principal {app_name} está desabilitado!")
```

### **Estatísticas**
- Total de módulos
- Módulos habilitados/desabilitados
- Módulos principais vs personalizados
- Status de dependências

## 🔒 Segurança

### **Proteções Implementadas**
- ✅ Apenas staff pode gerenciar módulos
- ✅ Módulos principais protegidos contra desabilitação
- ✅ Verificação de dependências antes de desabilitar
- ✅ Logs de auditoria de todas as ações
- ✅ Validação de permissões no middleware

### **Middleware de Segurança**
```python
# Verifica se usuário tem permissão para acessar módulo
if not self.module_service.is_module_enabled(app_name):
    # Redireciona com mensagem informativa
    messages.warning(request, f'Módulo "{module_display_name}" não disponível')
    return HttpResponseRedirect(reverse('pages:home'))
```

## 🚀 Próximos Passos

### **Melhorias Planejadas**
1. **Sistema de Permissões por Grupo**: Diferentes módulos para diferentes grupos
2. **Agendamento**: Habilitar/desabilitar módulos em horários específicos
3. **API REST**: Gerenciamento via API
4. **Notificações**: Alertas quando módulos são alterados
5. **Backup/Restore**: Salvar/restaurar configurações de módulos

### **Integrações Futuras**
- Sistema de plugins
- Marketplace de módulos
- Versionamento de módulos
- Rollback automático

## 📝 Exemplos de Uso

### **Cenário 1: Manutenção**
```python
# Desabilitar artigos para manutenção
module_service.disable_module('articles', user=admin_user)
# Usuários são redirecionados com mensagem informativa
```

### **Cenário 2: Lançamento Gradual**
```python
# Habilitar novo módulo apenas para testes
module_service.enable_module('new_feature', user=admin_user)
# Testar funcionalidade antes do lançamento público
```

### **Cenário 3: Controle de Acesso**
```python
# Diferentes módulos para diferentes tipos de usuário
# (implementação futura com sistema de grupos)
```

## ✅ Status Atual

- ✅ **Middleware funcionando**: URLs reconhecidas corretamente
- ✅ **Interface completa**: Painel de controle funcional
- ✅ **Testes implementados**: Sistema de teste robusto
- ✅ **Documentação**: Guias completos
- ✅ **Comandos de gerenciamento**: Automação disponível
- ✅ **Logs e auditoria**: Rastreamento completo

O sistema está **100% funcional** e pronto para uso em produção! 🎉
