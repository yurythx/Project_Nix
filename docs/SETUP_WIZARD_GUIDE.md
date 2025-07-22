# Setup Wizard Guide - FireFlies

## Visão Geral

O Setup Wizard do FireFlies é um sistema de configuração pós-deploy inspirado no Zabbix e GLPI, que permite configurar o sistema após a primeira instalação. O wizard foi implementado seguindo os princípios SOLID para garantir manutenibilidade e extensibilidade.

## Arquitetura SOLID

### Estrutura de Arquivos

```
apps/config/views/setup_wizard/
├── __init__.py              # Configuração do orchestrator e steps
├── base.py                  # Interface base WizardStepHandler
├── orchestrator.py          # SetupWizardOrchestrator (coordenação)
├── utils.py                 # Utilitários compartilhados
└── steps/
    ├── __init__.py
    ├── database.py          # DatabaseStepHandler
    ├── admin.py             # AdminStepHandler
    ├── email.py             # EmailStepHandler
    ├── security.py          # SecurityStepHandler
    └── finalize.py          # FinalizeStepHandler
```

### Princípios SOLID Aplicados

#### 1. Single Responsibility Principle (SRP)
- Cada step handler tem uma única responsabilidade
- O orchestrator coordena, mas não implementa lógica específica
- Utilitários são separados em módulos específicos

#### 2. Open/Closed Principle (OCP)
- Novos steps podem ser adicionados sem modificar código existente
- Interface base permite extensão sem alteração

#### 3. Liskov Substitution Principle (LSP)
- Todos os step handlers implementam a mesma interface
- Podem ser substituídos sem quebrar o sistema

#### 4. Interface Segregation Principle (ISP)
- Interface base minimalista e focada
- Cada step implementa apenas o que precisa

#### 5. Dependency Inversion Principle (DIP)
- Orchestrator depende de abstrações (interface)
- Steps são injetados via dicionário

## Componentes Principais

### 1. WizardStepHandler (Interface Base)
```python
class WizardStepHandler:
    def process(self, request, orchestrator):
        """Processa o passo do wizard"""
        raise NotImplementedError
```

### 2. SetupWizardOrchestrator
- Coordena a execução dos steps
- Gerencia o progresso no cache
- Aplica configurações finais

### 3. Step Handlers
- **DatabaseStepHandler**: Configuração de banco de dados
- **AdminStepHandler**: Criação do usuário administrador
- **EmailStepHandler**: Configuração de email
- **SecurityStepHandler**: Configurações de segurança
- **FinalizeStepHandler**: Finalização e aplicação das configurações

## Como Usar

### 1. Acessar o Wizard
```python
# URL: /config/wizard/
# Redirecionamento automático se .first_install existe
```

### 2. Processar um Step
```python
# Via POST para /config/wizard/
step = request.POST.get('step', 'database')
orchestrator.process_step(step, request)
```

### 3. Adicionar um Novo Step
```python
# 1. Criar novo handler em steps/
class NewStepHandler(WizardStepHandler):
    def process(self, request, orchestrator):
        # Implementar lógica do step
        pass

# 2. Registrar no __init__.py
wizard_steps = {
    'database': DatabaseStepHandler(),
    'new_step': NewStepHandler(),  # Adicionar aqui
    # ...
}
```

## Templates

### Estrutura de Templates
```
templates/config/
├── setup_wizard_loader.html      # Template principal
└── partials/
    └── _wizard_steps.html        # Conteúdo dos steps
```

### Características do UI
- Design inspirado no Zabbix
- Sidebar com progresso visual
- Responsivo e moderno
- Feedback visual em tempo real

## Configurações Suportadas

### Banco de Dados
- SQLite (padrão)
- PostgreSQL
- MySQL

### Email
- Console (desenvolvimento)
- SMTP (produção)

### Segurança
- Modo desenvolvimento (aberto)
- Modo produção (restrito)
- Configurações HTTPS

## Cache e Progresso

O wizard usa o cache do Django para salvar o progresso:
```python
# Salvar progresso
orchestrator.save_progress('database', config_data)

# Recuperar progresso
progress = cache.get('setup_wizard_progress', {})
```

## Finalização

Ao finalizar, o wizard:
1. Aplica todas as configurações ao arquivo `.env`
2. Cria o usuário administrador
3. Remove o arquivo `.first_install`
4. Redireciona para o dashboard

## Troubleshooting

### Problemas Comuns

1. **Erro de CSRF**: Verificar se o middleware está configurado corretamente
2. **Cache não funcionando**: Verificar configuração do cache no settings
3. **Permissões de arquivo**: Verificar permissões para escrever no `.env`

### Logs
```python
import logging
logger = logging.getLogger(__name__)
logger.error("Erro no wizard: %s", str(e))
```

## Extensibilidade

Para adicionar funcionalidades:

1. **Novos Steps**: Implementar `WizardStepHandler`
2. **Novos Tipos de Banco**: Adicionar lógica no orchestrator
3. **Novas Configurações**: Estender os step handlers existentes
4. **Customização de UI**: Modificar templates

## Para dúvidas sobre o wizard, consulte o código em `apps/config/views/setup_wizard/` ou abra uma issue no repositório. 