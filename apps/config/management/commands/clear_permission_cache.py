"""
Comando para limpar o cache de permissões do sistema.
"""
from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache
from core.cache_service import cache_service


class Command(BaseCommand):
    help = 'Limpa o cache de permissões do sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=int,
            help='ID do usuário para limpar cache específico'
        )
        parser.add_argument(
            '--object',
            type=str,
            help='Modelo e ID do objeto (ex: manga:123)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Limpar todo o cache de permissões'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar o que seria limpo sem executar'
        )

    def handle(self, *args, **options):
        """Executa o comando de limpeza de cache."""
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('🔍 Modo DRY RUN - Nenhuma alteração será feita')
            )
        
        # Limpar cache de usuário específico
        if options['user']:
            user_id = options['user']
            self.stdout.write(f'🧹 Limpando cache do usuário {user_id}...')
            
            if not options['dry_run']:
                success = cache_service.invalidate_user_cache(user_id)
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Cache do usuário {user_id} limpo com sucesso!')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Erro ao limpar cache do usuário {user_id}')
                    )
            else:
                self.stdout.write(f'📋 Seria limpo: cache do usuário {user_id}')
        
        # Limpar cache de objeto específico
        elif options['object']:
            try:
                model_name, object_id = options['object'].split(':')
                object_id = int(object_id)
                
                self.stdout.write(f'🧹 Limpando cache do objeto {model_name}:{object_id}...')
                
                if not options['dry_run']:
                    success = cache_service.invalidate_object_cache(model_name, object_id)
                    if success:
                        self.stdout.write(
                            self.style.SUCCESS(f'✅ Cache do objeto {model_name}:{object_id} limpo com sucesso!')
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'❌ Erro ao limpar cache do objeto {model_name}:{object_id}')
                        )
                else:
                    self.stdout.write(f'📋 Seria limpo: cache do objeto {model_name}:{object_id}')
                    
            except ValueError:
                raise CommandError(
                    'Formato inválido para --object. Use: modelo:id (ex: manga:123)'
                )
        
        # Limpar todo o cache
        elif options['all']:
            self.stdout.write('🧹 Limpando todo o cache de permissões...')
            
            if not options['dry_run']:
                success = cache_service.clear_all_cache()
                if success:
                    self.stdout.write(
                        self.style.SUCCESS('✅ Todo o cache de permissões limpo com sucesso!')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('❌ Erro ao limpar cache de permissões')
                    )
            else:
                self.stdout.write('📋 Seria limpo: todo o cache de permissões')
        
        # Limpeza padrão (cache geral)
        else:
            self.stdout.write('🧹 Limpando cache geral...')
            
            if not options['dry_run']:
                try:
                    cache.clear()
                    self.stdout.write(
                        self.style.SUCCESS('✅ Cache geral limpo com sucesso!')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Erro ao limpar cache geral: {str(e)}')
                    )
            else:
                self.stdout.write('📋 Seria limpo: cache geral')
        
        # Mostrar estatísticas
        if not options['dry_run']:
            self.show_cache_stats()

    def show_cache_stats(self):
        """Mostra estatísticas do cache."""
        try:
            stats = cache_service.get_cache_stats()
            
            self.stdout.write('\n📊 Estatísticas do Cache:')
            self.stdout.write(f'   Backend: {stats.get("backend", "Unknown")}')
            self.stdout.write(f'   TTL Padrão: {stats.get("default_ttl", 300)}s')
            self.stdout.write(f'   Prefixos: {len(stats.get("prefixes", []))}')
            
            if 'error' in stats:
                self.stdout.write(
                    self.style.WARNING(f'   ⚠️ Erro ao obter estatísticas: {stats["error"]}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️ Erro ao obter estatísticas do cache: {str(e)}')
            ) 