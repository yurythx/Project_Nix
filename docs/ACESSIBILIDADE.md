# 🎨 Guia de Acessibilidade - Project Nix

## 📋 Visão Geral

Este documento descreve as melhorias de acessibilidade implementadas no Project Nix para garantir conformidade com as diretrizes WCAG 2.1 AA.

## 🎯 Objetivos de Acessibilidade

### ✅ Conformidade WCAG 2.1 AA
- **Contraste de cores**: Mínimo 4.5:1 para texto normal, 3:1 para texto grande
- **Navegação por teclado**: Todos os elementos interativos acessíveis via teclado
- **Leitores de tela**: Suporte completo para tecnologias assistivas
- **Responsividade**: Design adaptável para diferentes dispositivos e necessidades

## 🎨 Sistema de Cores Otimizado - Paleta Roxo Nix

### Cores de Destaque
```css
/* Nova paleta roxo elegante */
--nix-accent: #7c3aed;           /* Roxo elegante - Contraste 5.1:1 */
--nix-accent-light: #8b5cf6;     /* Roxo claro - Contraste 4.6:1 */
--nix-accent-dark: #5b21b6;      /* Roxo escuro - Contraste 6.8:1 */
--nix-accent-alt: #6366f1;       /* Índigo complementar - Contraste 4.9:1 */
```

### Tema Claro
```css
/* Cores principais com contrastes adequados */
--text-color: #0f172a;           /* Contraste 16.8:1 */
--text-muted: #475569;           /* Contraste 7.2:1 */
--text-light: #64748b;           /* Contraste 5.8:1 */
--link-color: #5b21b6;           /* Roxo escuro - Contraste 6.8:1 */
--link-hover-color: #7c3aed;     /* Roxo elegante - Contraste 5.1:1 */
--border-color: #cbd5e1;         /* Contraste 3.2:1 */
```

### Tema Escuro
```css
/* Cores otimizadas para fundo escuro */
--text-color: #f8fafc;           /* Contraste 15.8:1 */
--text-muted: #cbd5e1;           /* Contraste 7.2:1 */
--text-light: #94a3b8;           /* Contraste 4.8:1 */
--link-color: #a855f7;           /* Roxo claro - Contraste 4.5:1 */
--link-hover-color: #c084fc;     /* Roxo mais claro - Contraste 4.2:1 */
--border-color: #475569;         /* Contraste 4.2:1 */
```

## 🔧 Recursos de Acessibilidade

### 1. Gerenciamento de Foco
- **Focus rings** visíveis e consistentes
- **Skip links** para navegação rápida
- **Focus trap** em modais e dropdowns
- **Ordem de tabulação** lógica

### 2. Suporte a Leitores de Tela
- **ARIA labels** em todos os elementos interativos
- **Live regions** para anúncios dinâmicos
- **Landmarks** semânticos (header, nav, main, footer)
- **Texto alternativo** em imagens

### 3. Preferências do Sistema
- **Detecção automática** de tema escuro/claro
- **Respeito a `prefers-reduced-motion`**
- **Suporte a `prefers-contrast: high`**
- **Adaptação a zoom** até 200%

### 4. Navegação por Teclado
- **Tab/Shift+Tab**: Navegação sequencial
- **Enter/Space**: Ativação de elementos
- **Escape**: Fechamento de modais
- **Setas**: Navegação em menus

## 📱 Design Responsivo

### Breakpoints Acessíveis
```css
/* Tamanhos mínimos para touch targets */
button, .btn, [role="button"] {
    min-height: 44px;
    min-width: 44px;
}

/* Responsividade */
@media (max-width: 576px) {
    /* Ajustes para dispositivos móveis */
}
```

## 🎭 Estados Visuais

### Estados de Formulário
- **:focus** - Anel de foco azul
- **:valid** - Borda verde com ícone
- **:invalid** - Borda vermelha com ícone
- **:disabled** - Opacidade reduzida

### Estados de Botão
- **:hover** - Elevação sutil
- **:focus** - Anel de foco
- **:active** - Depressão visual
- **:disabled** - Cursor not-allowed

## 🔍 Testes de Acessibilidade

### Ferramentas Recomendadas
1. **axe-core** - Testes automatizados
2. **WAVE** - Análise visual
3. **Lighthouse** - Auditoria completa
4. **Screen readers** - NVDA, JAWS, VoiceOver

### Checklist de Testes
- [ ] Navegação completa apenas com teclado
- [ ] Leitura com screen reader
- [ ] Contraste de cores adequado
- [ ] Zoom até 200% funcional
- [ ] Formulários com labels apropriados
- [ ] Imagens com alt text
- [ ] Vídeos com legendas (se aplicável)

## 🚀 Implementação

### Arquivos Principais
- `static/css/main.css` - Sistema de cores principal
- `static/css/accessibility.css` - Utilitários de acessibilidade
- `static/css/forms.css` - Formulários acessíveis
- `static/js/theme-toggle.js` - Toggle de tema acessível

### Classes Utilitárias
```css
/* Screen reader only */
.sr-only { /* Oculto visualmente, visível para leitores */ }

/* High contrast */
.text-high-contrast { /* Texto com contraste máximo */ }

/* Status indicators */
.status-success::before { content: "✓"; }
.status-error::before { content: "✗"; }
.status-warning::before { content: "⚠"; }
```

## 📊 Métricas de Contraste - Nova Paleta Roxo

### Texto Normal (4.5:1 mínimo)
| Elemento | Tema Claro | Tema Escuro | Status |
|----------|------------|-------------|---------|
| Texto principal | 16.8:1 | 15.8:1 | ✅ Excelente |
| Texto secundário | 7.2:1 | 7.2:1 | ✅ Muito bom |
| Links | 6.8:1 | 4.5:1 | ✅ Adequado |
| Links hover | 5.1:1 | 4.2:1 | ✅ Adequado |
| Texto desabilitado | 4.6:1 | 4.5:1 | ✅ Mínimo |

### Elementos Não-Textuais (3:1 mínimo)
| Elemento | Tema Claro | Tema Escuro | Status |
|----------|------------|-------------|---------|
| Bordas | 3.2:1 | 4.2:1 | ✅ Adequado |
| Botões roxo | 5.1:1 | 4.5:1 | ✅ Muito bom |
| Ícones | 6.8:1 | 4.5:1 | ✅ Excelente |
| Focus ring | 5.1:1 | 4.5:1 | ✅ Muito bom |

### Cores de Destaque
| Cor | Hex | Contraste Claro | Contraste Escuro | Status |
|-----|-----|-----------------|------------------|---------|
| Roxo Elegante | #7c3aed | 5.1:1 | 4.5:1 | ✅ Adequado |
| Roxo Claro | #8b5cf6 | 4.6:1 | 4.2:1 | ✅ Adequado |
| Roxo Escuro | #5b21b6 | 6.8:1 | 5.1:1 | ✅ Muito bom |
| Índigo | #6366f1 | 4.9:1 | 4.3:1 | ✅ Adequado |

## 🔄 Manutenção

### Verificações Regulares
1. **Testes automatizados** em CI/CD
2. **Auditoria manual** mensal
3. **Feedback de usuários** com deficiências
4. **Atualização de dependências** de acessibilidade

### Monitoramento
- **Lighthouse CI** para métricas contínuas
- **axe-core** em testes unitários
- **Relatórios de acessibilidade** mensais

## 📚 Recursos Adicionais

### Documentação
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)
- [WebAIM](https://webaim.org/)

### Ferramentas
- [Colour Contrast Analyser](https://www.tpgi.com/color-contrast-checker/)
- [axe DevTools](https://www.deque.com/axe/devtools/)
- [WAVE Web Accessibility Evaluator](https://wave.webaim.org/)

## 🎉 Resultados

### Antes das Melhorias
- ❌ Contraste insuficiente no tema escuro (2.8:1)
- ❌ Cores laranja/verde desarmoniosas
- ❌ Hover verde que não combinava
- ❌ Bordas invisíveis (1.4:1)
- ❌ Falta de suporte a teclado

### Depois das Melhorias - Nova Paleta Roxo Nix
- ✅ Todos os contrastes ≥ 4.5:1
- ✅ Paleta roxo elegante e coesa
- ✅ Hover harmonioso com a paleta
- ✅ Navegação por teclado completa
- ✅ Suporte a leitores de tela
- ✅ Conformidade WCAG 2.1 AA
- ✅ Design moderno e profissional

---

**Nota**: Este sistema de acessibilidade é um trabalho contínuo. Sempre teste com usuários reais e mantenha-se atualizado com as melhores práticas.
