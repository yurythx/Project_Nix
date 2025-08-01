# Módulo de Mangás

Este módulo é responsável pelo gerenciamento de mangás, incluindo volumes, capítulos e páginas.

## Processamento de Volumes

O módulo inclui um serviço para processamento de arquivos de volumes de mangá, suportando vários formatos de arquivo.

### Funcionalidades

- Extração de imagens de arquivos compactados (ZIP, RAR, 7Z)
- Extração de imagens de arquivos PDF
- Criação automática de capítulos e páginas
- Ordenação automática de páginas
- Suporte a metadados

### Formatos Suportados

- **ZIP**: Arquivos compactados no formato ZIP
- **RAR**: Arquivos compactados no formato RAR
- **7Z**: Arquivos compactados no formato 7-Zip
- **PDF**: Arquivos PDF contendo imagens

Para informações detalhadas sobre as limitações de cada formato e exemplos de estrutura de diretórios, consulte a [documentação de formatos de arquivo](docs/FORMATOS_ARQUIVO.md).

### Uso Básico

```python
from mangas.services.volume_processor_service import VolumeFileProcessorService

# Cria uma instância do processador
processor = VolumeFileProcessorService()

# Processa um arquivo para um volume existente
success, message = processor.process_volume_file(volume, caminho_do_arquivo)

if success:
    print("Arquivo processado com sucesso!")
else:
    print(f"Erro ao processar o arquivo: {message}")
```

### Configuração

O serviço de processamento de volumes requer as seguintes dependências:

- `PyMuPDF` (para PDF)
- `py7zr` (para 7Z)
- `rarfile` (para RAR)
- `Pillow` (para processamento de imagens)

### Testes

Os testes do módulo podem ser executados com:

```bash
python -m pytest apps/mangas/tests/ -v
```

### Fluxo de Processamento

1. O arquivo é validado quanto ao formato e tamanho
2. As imagens são extraídas para um diretório temporário
3. As imagens são processadas e salvas no diretório de mídia
4. Os metadados são extraídos e salvos
5. Os capítulos e páginas são criados no banco de dados
6. O volume é marcado como processado

### Tratamento de Erros

O serviço inclui tratamento de erros detalhado, com mensagens claras para ajudar na depuração de problemas comuns, como arquivos corrompidos ou formatos não suportados.
