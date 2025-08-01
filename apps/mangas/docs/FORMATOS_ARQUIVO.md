# Formatos de Arquivo Suportados

Este documento detalha os formatos de arquivo suportados pelo módulo de processamento de volumes de mangá, suas limitações e exemplos de estrutura de diretórios.

## Índice

1. [Formatos Suportados](#formatos-suportados)
2. [Limitações por Formato](#limitações-por-formato)
3. [Estrutura de Diretórios Recomendada](#estrutura-de-diretórios-recomendada)
4. [Exemplos Práticos](#exemplos-práticos)
5. [Boas Práticas](#boas-práticas)

## Formatos Suportados

O módulo suporta os seguintes formatos de arquivo:

1. **ZIP** (`.zip`)
2. **RAR** (`.rar`, `.cbr`)
3. **7Z** (`.7z`, `.cb7`)
4. **PDF** (`.pdf`, `.cbz`)

## Limitações por Formato

### 1. ZIP (`.zip`)

**Vantagens:**
- Amplamente suportado
- Boa taxa de compressão
- Suporte nativo na maioria dos sistemas operacionais

**Limitações:**
- Tamanho máximo de arquivo: 4GB (limitação do formato)
- Não suporta compressão de arquivos maiores que 4GB
- Metadados limitados

**Recomendações:**
- Use compressão normal (nível 6) para equilíbrio entre tamanho e desempenho
- Evite senhas nos arquivos ZIP

### 2. RAR (`.rar`, `.cbr`)

**Vantagens:**
- Melhor taxa de compressão que ZIP
- Suporte a arquivos grandes (>4GB)
- Recuperação de erros

**Limitações:**
- Requer biblioteca adicional (`rarfile` e `unrar`)
- Pode ser mais lento para extração
- Menos suporte nativo em alguns sistemas

**Recomendações:**
- Use a versão mais recente do formato RAR
- Evite usar recursos avançados como volumes divididos

### 3. 7Z (`.7z`, `.cb7`)

**Vantagens:**
- Melhor taxa de compressão entre os formatos suportados
- Suporte a arquivos grandes
- Metadados avançados

**Limitações:**
- Consome mais memória durante a extração
- Pode ser mais lento para extrair
- Requer biblioteca adicional (`py7zr`)

**Recomendações:**
- Use o método de compressão LZMA2
- Evite usar criptografia

### 4. PDF (`.pdf`, `.cbz`)

**Vantagens:**
- Padrão amplamente aceito
- Bom para documentos digitalizados
- Preserva qualidade de imagem

**Limitações:**
- Tamanho de arquivo maior que formatos compactados
- Pode ter problemas com PDFs protegidos
- Requer biblioteca adicional (`PyMuPDF`)

**Recomendações:**
- Use resolução de 300 DPI para digitalizações
- Evite PDFs com camadas ou formulários interativos
- Certifique-se de que as imagens esteham no espaço de cores RGB

## Estrutura de Diretórios Recomendada

### Estrutura Básica

```
manga/
├── volume_01.cbz
├── volume_02.cbz
└── volume_03.cbz
```

### Estrutura com Capítulos

```
manga/
├── Volume 1/
│   ├── cap_001.cbz
│   ├── cap_002.cbz
│   └── cap_003.cbz
└── Volume 2/
    ├── cap_004.cbz
    └── cap_005.cbz
```

### Estrutura com Metadados

```
manga/
├── info.json
├── covers/
│   ├── volume_01.jpg
│   └── volume_02.jpg
└── volumes/
    ├── volume_01/
    │   ├── pages/
    │   │   ├── 001.jpg
    │   │   └── 002.jpg
    │   └── metadata.json
    └── volume_02.cbz
```

## Exemplos Práticos

### 1. Volume Único em ZIP

**Arquivo:** `manga_volume_01.zip`

**Conteúdo:**
```
page_001.jpg
page_002.jpg
...
page_200.jpg
```

### 2. Volume com Capítulos em RAR

**Arquivo:** `manga_volume_02.rar`

**Conteúdo:**
```
cap_01/
  page_001.jpg
  page_002.jpg
  ...
cap_02/
  page_001.jpg
  ...
```

### 3. PDF com Capa Separada

**Arquivos:**
- `manga_03_cover.jpg`
- `manga_03.pdf`

## Boas Práticas

1. **Nomenclatura de Arquivos:**
   - Use números com zeros à esquerda (001, 002, ...) para ordenação correta
   - Evite caracteres especiais ou espaços nos nomes dos arquivos
   - Mantenha um padrão consistente em todos os volumes

2. **Organização de Páginas:**
   - Inclua todas as páginas em ordem sequencial
   - Não pule números de página
   - Use o mesmo formato de imagem em todo o volume

3. **Metadados:**
   - Inclua um arquivo `metadata.json` com informações como título, autor e número do volume
   - Use o formato UTF-8 para arquivos de texto
   - Inclua a capa como um arquivo separado quando possível

4. **Qualidade de Imagem:**
   - Use formato JPG para fotos e PNG para imagens com transparência
   - Mantenha uma resolução mínima de 1200px na maior dimensão
   - Evite compressão excessiva que possa prejudicar a qualidade

5. **Tamanho de Arquivo:**
   - Divida volumes grandes em múltiplos arquivos (máx. 500MB cada)
   - Considere a qualidade vs. tamanho para otimização de armazenamento
   - Documente o conteúdo de cada arquivo em um README.txt quando apropriado
