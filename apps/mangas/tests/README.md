# Testes do app Mangás

Este diretório contém os testes automatizados para o app `mangas`.

## Como rodar os testes

Execute todos os testes do app mangas:

```
python manage.py test apps.mangas
```

Ou rode um arquivo específico:

```
python manage.py test apps.mangas.tests.test_models
```

## Principais cenários cobertos

- **Models:**
  - Criação de mangá, volume, capítulo, página
  - Geração e atualização de slug
  - Relacionamentos e métodos utilitários
  - Casos de borda (títulos vazios, duplicados, números duplicados)
- **Views:**
  - CRUD completo para todas as entidades
  - Permissões (criador, staff, superuser, usuário comum)
  - Navegação por slug
  - Performance (uso de select_related/prefetch_related)
- **Services:**
  - Processamento de arquivos (ZIP, PDF, CBZ, RAR)
  - Validação e extração de imagens
- **Mixins de permissão:**
  - MangaOwnerOrStaffMixin, ChapterOwnerOrStaffMixin, PageOwnerOrStaffMixin, VolumeOwnerOrStaffMixin
  - Testes positivos e negativos para todos os perfis
- **Integração:**
  - Fluxo completo: criar mangá → volume → capítulo → página → permissões e navegação

## Como contribuir com novos testes

- Siga o padrão dos arquivos existentes (use TestCase do Django)
- Prefira nomes de métodos descritivos (ex: `test_slug_generation_with_duplicate_titles`)
- Cubra casos positivos e negativos
- Use fixtures e o `setUp` para criar dados de teste
- Para performance, use `assertNumQueriesLessThan` quando relevante

---

Dúvidas ou sugestões? Abra uma issue ou contribua diretamente! 