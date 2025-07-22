# Estrutura da Sidebar do Config

## 📋 Visão Geral

A sidebar do painel de administração foi completamente refatorada para eliminar repetições e melhorar a organização. A nova estrutura é modular, responsiva e inclui estatísticas em tempo real.

## 🏗️ Nova Estrutura

### 1. **Dashboard**
- **URL**: `/config/`
- **Função**: Visão geral com métricas do sistema
- **Estilo**: Destaque especial com gradiente verde Django

### 2. **Usuários & Permissões**
- **URLs**: 
  - `/config/usuarios/` - Lista de usuários
  - `/config/usuarios/criar/` - Criar usuário
- **Badge**: Mostra usuários ativos/total
- **Função**: Gerenciamento completo de usuários

### 3. **Email**
- **URLs**:
  - `/config/email/` - Configurações
  - `/config/email/teste/` - Teste de envio
  - `/config/email/templates/` - Templates
  - `/config/email/estatisticas/` - Estatísticas
- **Badge**: Número de configurações de email
- **Função**: Sistema completo de email

### 4. **Módulos**
- **URLs**:
  - `/config/modulos/` - Gerenciar módulos
  - `/config/modulos/sync/` - Sincronizar
- **Badge**: Módulos ativos/total
- **Função**: Controle de módulos do sistema

### 5. **Sistema**
- **URLs**:
  - `/config/sistema/` - Configurações gerais
  - `/config/sistema/variaveis-ambiente/` - Variáveis de ambiente
- **Função**: Configurações do sistema

### 6. **Ferramentas**
- **URLs**:
  - `/config/sistema/export/` - Exportar configurações
  - `/config/sistema/import/` - Importar configurações
- **Função**: Ferramentas avançadas

### 7. **Monitoramento**
- **URLs**:
  - `/config/logs/` - Logs do sistema
  - `/config/cache/` - Gerenciar cache
  - `/config/backup/` - Backup & restauração
- **Função**: Monitoramento e manutenção

## 🎨 Melhorias Implementadas

### **Template Tags Personalizados**
- `{% sidebar_item %}` - Renderiza item da sidebar
- `{% get_config_stats %}` - Obtém estatísticas
- `{% is_config_section_active %}` - Verifica seção ativa

### **Badges com Estatísticas**
- Usuários: Ativos/Total
- Email: Número de configurações
- Módulos: Ativos/Total

### **Estilos Aprimorados**
- Dashboard com destaque especial
- Seções com bordas e espaçamento
- Suporte completo a tema escuro
- Animações suaves

### **Acessibilidade**
- Tooltips descritivos
- ARIA labels
- Navegação por teclado
- Contraste adequado

## 🔧 Arquivos Modificados

### **Templates**
- `apps/config/templates/config/base_config.html` - Template base
- `apps/config/templates/config/includes/sidebar.html` - Sidebar modular
- `apps/config/templates/config/includes/sidebar_item.html` - Item da sidebar

### **Template Tags**
- `apps/config/templatetags/config_extras.py` - Tags personalizados

### **Estilos**
- CSS integrado no template base com suporte a temas

## 📊 Estatísticas Exibidas

```python
stats = {
    'total_users': User.objects.count(),
    'active_users': User.objects.filter(is_active=True).count(),
    'email_configs': EmailConfiguration.objects.count(),
    'active_modules': AppModuleConfiguration.objects.filter(is_enabled=True).count(),
    'total_modules': AppModuleConfiguration.objects.count(),
}
```

## 🎯 Benefícios

1. **Eliminação de Repetições**: Navbar simplificada, sidebar centralizada
2. **Melhor Organização**: Agrupamento lógico por funcionalidade
3. **Informações Úteis**: Badges com estatísticas em tempo real
4. **Manutenibilidade**: Código modular e reutilizável
5. **Acessibilidade**: Melhor suporte a leitores de tela
6. **Performance**: Template tags otimizados

## 🔮 Próximos Passos

1. Implementar funcionalidades TODO (backup, cache, logs)
2. Adicionar mais estatísticas nos badges
3. Criar sistema de notificações na sidebar
4. Implementar busca rápida
5. Adicionar atalhos de teclado

## 🚀 Como Usar

A nova sidebar é carregada automaticamente em todas as páginas do config através do template base. Os template tags são carregados automaticamente e as estatísticas são atualizadas a cada carregamento da página.

Para adicionar novos itens, use o template tag `{% sidebar_item %}`:

```django
{% sidebar_item 'url_name' 'fas fa-icon' 'Título' 'Descrição para tooltip' %}
```
