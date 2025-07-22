from ..base import WizardStepHandler
from django.contrib import messages
from django.shortcuts import redirect, render
from pathlib import Path

class DatabaseStepHandler(WizardStepHandler):
    def process(self, request, orchestrator):
        database_type = request.POST.get('database_type')
        config = {'type': database_type}

        if database_type == 'sqlite':
            sqlite_existing = request.POST.get('sqlite_existing')
            sqlite_name = request.POST.get('sqlite_name') or 'db.sqlite3'
            if sqlite_existing:
                config['ENGINE'] = 'django.db.backends.sqlite3'
                config['NAME'] = sqlite_existing
            else:
                config['ENGINE'] = 'django.db.backends.sqlite3'
                config['NAME'] = sqlite_name
        elif database_type == 'postgresql':
            config['ENGINE'] = 'django.db.backends.postgresql'
            config['HOST'] = request.POST.get('pg_host', 'localhost')
            config['PORT'] = request.POST.get('pg_port', '5432')
            config['USER'] = request.POST.get('pg_user', 'postgres')
            config['PASSWORD'] = request.POST.get('pg_password', '')
            pg_existing = request.POST.get('pg_existing')
            pg_name = request.POST.get('pg_name')
            config['NAME'] = pg_existing or pg_name
        elif database_type == 'mysql':
            config['ENGINE'] = 'django.db.backends.mysql'
            config['HOST'] = request.POST.get('mysql_host', 'localhost')
            config['PORT'] = request.POST.get('mysql_port', '3306')
            config['USER'] = request.POST.get('mysql_user', 'root')
            config['PASSWORD'] = request.POST.get('mysql_password', '')
            mysql_existing = request.POST.get('mysql_existing')
            mysql_name = request.POST.get('mysql_name')
            config['NAME'] = mysql_existing or mysql_name
        else:
            messages.error(request, "❌ O tipo de banco de dados selecionado é inválido.")
            return render(request, self.template_name, {'form': self.form})

        # Corrigir bug: converter Path para str se existir
        if config.get('ENGINE') == 'django.db.backends.sqlite3' or config.get('type') == 'sqlite':
            if 'NAME' in config and isinstance(config['NAME'], Path):
                config['NAME'] = str(config['NAME'])
            if 'path' in config and isinstance(config['path'], Path):
                config['path'] = str(config['path'])

        # Testar conexão usando orchestrator
        if not orchestrator.test_database_connection(config):
            messages.error(request, "Falha na conexão com o banco de dados")
            return redirect('setup_wizard')
        orchestrator.save_progress('database', config)
        messages.success(request, "Configuração do banco de dados salva com sucesso!")
        return redirect('setup_wizard?step=2') 