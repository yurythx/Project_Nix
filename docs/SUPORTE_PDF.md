# Suporte a PDF no Sistema de Mangás

## Visão Geral

O sistema de mangás agora suporta upload e processamento de arquivos PDF. Quando um PDF é enviado, ele é automaticamente convertido em imagens individuais (uma por página) e organizado como um capítulo normal.

## Funcionalidades

### ✅ Formatos Suportados
- **PDF** - Arquivos PDF padrão
- **ZIP/CBZ** - Arquivos compactados com imagens
- **RAR/CBR** - Arquivos RAR com imagens
- **7Z/CB7** - Arquivos 7-Zip com imagens
- **TAR/CBT** - Arquivos TAR com imagens
- **Imagens individuais** - JPG, PNG, WebP, GIF, BMP, TIFF

### 🔧 Processamento de PDF
- **Conversão automática**: PDFs são convertidos em imagens PNG
- **Qualidade otimizada**: DPI de 150 para boa qualidade
- **Numeração automática**: Páginas são numeradas sequencialmente
- **Limpeza automática**: Arquivos temporários são removidos após processamento

## Como Usar

### 1. Upload de PDF
1. Acesse a página de criação de capítulo
2. Selecione um arquivo PDF
3. O sistema processará automaticamente o PDF
4. Cada página do PDF será convertida em uma imagem
5. As imagens serão organizadas como páginas do capítulo

### 2. Limitações
- **Tamanho máximo**: 100MB por arquivo PDF
- **PDFs protegidos**: Não são suportados (com senha)
- **PDFs corrompidos**: Serão rejeitados com mensagem de erro
- **Qualidade**: DPI fixo de 150 (pode ser ajustado no código)

## Dependências

### Bibliotecas Python
```bash
pip install PyPDF2 pdf2image
```

### Dependências do Sistema (para pdf2image)
- **Windows**: Instalação automática via pip
- **Linux**: `sudo apt-get install poppler-utils`
- **macOS**: `brew install poppler`

## Configuração

### Ajustar Qualidade
Para modificar a qualidade das imagens extraídas, edite o arquivo:
```python
# apps/mangas/services/file_processor_service.py
# Linha ~220
images = convert_from_bytes(
    open(temp_pdf.name, 'rb').read(),
    dpi=150,  # Ajuste este valor (150 = boa qualidade)
    fmt='PNG',  # Formato de saída
    output_folder=extract_dir,
    output_file='page_'
)
```

### Ajustar Tamanho Máximo
Para modificar o tamanho máximo de PDFs:
```python
# apps/mangas/constants/__init__.py
MAX_ARCHIVE_SIZE = 100 * 1024 * 1024  # 100MB
```

## Tratamento de Erros

### Erros Comuns
1. **PDF protegido por senha**: "PDF protegido por senha não é suportado"
2. **Arquivo corrompido**: "Arquivo não é um PDF válido"
3. **Arquivo muito grande**: "Arquivo muito grande. Tamanho máximo permitido: 100MB"
4. **Dependências ausentes**: "Bibliotecas PyPDF2 e pdf2image são necessárias"

### Logs
Os logs de processamento são salvos em:
- **Sucesso**: `INFO: PDF processado com sucesso: X páginas extraídas`
- **Erro**: `ERROR: Erro ao processar PDF: [detalhes do erro]`

## Vantagens do Suporte a PDF

### Para Usuários
- **Facilidade**: Upload direto de PDFs sem conversão manual
- **Qualidade**: Conversão automática com qualidade otimizada
- **Organização**: Páginas automaticamente numeradas e organizadas

### Para Administradores
- **Flexibilidade**: Suporte a múltiplos formatos
- **Automação**: Processamento automático sem intervenção manual
- **Consistência**: Mesma interface para todos os formatos

## Troubleshooting

### Problema: PDF não é processado
**Solução**: Verifique se as dependências estão instaladas:
```bash
pip install PyPDF2 pdf2image
```

### Problema: Erro de conversão
**Solução**: Verifique se o PDF não está protegido por senha ou corrompido

### Problema: Qualidade baixa
**Solução**: Aumente o DPI no código (linha ~220 do file_processor_service.py)

## Arquivos Modificados

1. **`apps/mangas/constants/__init__.py`** - Adicionado `.pdf` aos formatos suportados
2. **`apps/mangas/forms/manga_form.py`** - Atualizado formulário para aceitar PDFs
3. **`apps/mangas/services/file_processor_service.py`** - Adicionado processamento de PDF

## Testes

Para testar o suporte a PDF:
1. Crie um capítulo novo
2. Faça upload de um arquivo PDF
3. Verifique se as páginas foram criadas corretamente
4. Teste a visualização do capítulo

## Notas Técnicas

- **Formato de saída**: PNG (melhor qualidade para quadrinhos)
- **DPI padrão**: 150 (equilibra qualidade e tamanho)
- **Numeração**: Páginas numeradas de 001, 002, 003...
- **Limpeza**: Arquivos temporários removidos automaticamente 