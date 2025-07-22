from django.core.management.base import BaseCommand
from apps.config.models.group import Group

class Command(BaseCommand):
    help = 'Gera slugs para grupos existentes que não possuem slug'

    def handle(self, *args, **options):
        groups_without_slug = Group.objects.filter(slug='')
        
        if not groups_without_slug.exists():
            self.stdout.write(
                self.style.SUCCESS('Todos os grupos já possuem slug!')
            )
            return

        self.stdout.write(f'Gerando slugs para {groups_without_slug.count()} grupos...')
        
        for group in groups_without_slug:
            old_name = group.name
            group.save()  # Isso vai gerar o slug automaticamente
            self.stdout.write(
                self.style.SUCCESS(f'Slug gerado para "{old_name}": {group.slug}')
            )

        self.stdout.write(
            self.style.SUCCESS('Slugs gerados com sucesso!')
        ) 