from django.core.management.base import BaseCommand
from apps.config.models.app_module_config import AppModuleConfiguration
from django.db import transaction

class Command(BaseCommand):
    help = 'Padroniza nomes de módulos no banco, deixando apenas o nome do app (ex: accounts, articles, etc)'

    def handle(self, *args, **options):
        self.stdout.write('🔎 Corrigindo nomes de módulos no banco...')
        with transaction.atomic():
            seen = set()
            to_delete = []
            for module in AppModuleConfiguration.objects.all():
                original = module.app_name
                # Extrai só o nome final do app (ex: apps.articles -> articles)
                fixed = original.split('.')[-1]
                if fixed in seen:
                    to_delete.append(module)
                    self.stdout.write(f'  🗑️ Removendo duplicata: {original}')
                else:
                    if original != fixed:
                        self.stdout.write(f'  ✏️ Corrigindo {original} -> {fixed}')
                        module.app_name = fixed
                        module.save()
                    seen.add(fixed)
            for module in to_delete:
                module.delete()
        self.stdout.write(self.style.SUCCESS('✅ Nomes de módulos padronizados com sucesso!')) 