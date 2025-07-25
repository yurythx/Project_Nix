from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, HttpResponse, HttpResponseForbidden, Http404
from django.conf import settings
import subprocess
import tempfile
import os
import shutil
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
import datetime
import glob
import logging
import hashlib
from django.contrib import messages
from django.views.generic import View, TemplateView
from django.http import HttpResponseRedirect

logger = logging.getLogger('config.backup')

# Função utilitária para listar backups recentes
def list_backup_files(backup_type='database', limit=5):
    backup_dir = os.path.join(settings.BASE_DIR, 'backups', backup_type)
    if not os.path.exists(backup_dir):
        return []
    files = [
        {
            'name': f,
            'path': os.path.join('backups', backup_type, f),
            'size': os.path.getsize(os.path.join(backup_dir, f)),
            'modified': os.path.getmtime(os.path.join(backup_dir, f)),
        }
        for f in os.listdir(backup_dir)
        if f.endswith('.backup') or f.endswith('.tar.gz') or f.endswith('.zip')
    ]
    files.sort(key=lambda x: x['modified'], reverse=True)
    return files[:limit]

# Função utilitária para gerar hash SHA256 de um arquivo
def generate_sha256(file_path):
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

@method_decorator(staff_member_required, name='dispatch')
class BackupDatabaseView(View):
    def get(self, request):
        print('### BackupDatabaseView GET chamado')
        backups = list_backup_files('database')
        # Adiciona hash SHA256 se existir
        for backup in backups:
            hash_file = os.path.join(settings.BASE_DIR, 'backups', 'database', backup['name'] + '.sha256')
            if os.path.exists(hash_file):
                with open(hash_file) as hf:
                    backup['sha256'] = hf.read().strip()
            else:
                backup['sha256'] = None
        print('### Antes de render backup_database.html')
        return render(request, 'config/backup_database.html', {'backups': backups})
    def post(self, request):
        print('### BackupDatabaseView POST chamado')
        import tempfile, subprocess, os, shutil, datetime
        from django.conf import settings
        from django.http import FileResponse, HttpResponse
        db_engine = settings.DATABASES['default']['ENGINE']
        db_name = settings.DATABASES['default']['NAME']
        db_user = settings.DATABASES['default'].get('USER', '')
        db_host = settings.DATABASES['default'].get('HOST', 'localhost')
        db_port = str(settings.DATABASES['default'].get('PORT', ''))
        db_password = settings.DATABASES['default'].get('PASSWORD', '')
        logger.info(f"[DB BACKUP] Iniciado por {request.user.username} para engine {db_engine}")
        try:
            if 'postgresql' in db_engine:
                suffix = '.backup'
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmpfile:
                    tmpfile.close()
                    cmd = [
                        'pg_dump',
                        '-U', db_user,
                        '-h', db_host,
                        '-p', db_port or '5432',
                        '-F', 'c',
                        '-b',
                        '-v',
                        '-f', tmpfile.name,
                        db_name
                    ]
                    env = os.environ.copy()
                    env['PGPASSWORD'] = db_password
                    subprocess.run(cmd, env=env, check=True)
                    backup_dir = os.path.join(settings.BASE_DIR, 'backups', 'database')
                    os.makedirs(backup_dir, exist_ok=True)
                    backup_filename = f"{db_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
                    backup_path = os.path.join(backup_dir, backup_filename)
                    shutil.copy(tmpfile.name, backup_path)
                    logger.info(f"[DB BACKUP] Sucesso: {backup_filename} salvo em {backup_path} por {request.user.username}")
                    response = FileResponse(open(tmpfile.name, 'rb'), as_attachment=True, filename=backup_filename)
                    # Gerar hash SHA256
                    sha256 = generate_sha256(backup_path)
                    hash_file = backup_path + '.sha256'
                    with open(hash_file, 'w') as hf:
                        hf.write(sha256)
                    logger.info(f"[DB BACKUP] SHA256: {sha256} salvo em {hash_file}")
                    messages.success(request, f"Backup do banco de dados gerado com sucesso!")
                    return response
            elif 'mysql' in db_engine:
                suffix = '.sql'
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode='w+', encoding='utf-8') as tmpfile:
                    tmpfile.close()
                    cmd = [
                        'mysqldump',
                        '-u', db_user,
                        f'-p{db_password}',
                        '-h', db_host,
                    ]
                    if db_port:
                        cmd += ['-P', db_port]
                    cmd += [db_name]
                    with open(tmpfile.name, 'w', encoding='utf-8') as f:
                        subprocess.run(cmd, stdout=f, check=True)
                    backup_dir = os.path.join(settings.BASE_DIR, 'backups', 'database')
                    os.makedirs(backup_dir, exist_ok=True)
                    backup_filename = f"{db_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
                    backup_path = os.path.join(backup_dir, backup_filename)
                    shutil.copy(tmpfile.name, backup_path)
                    logger.info(f"[DB BACKUP] Sucesso: {backup_filename} salvo em {backup_path} por {request.user.username}")
                    response = FileResponse(open(tmpfile.name, 'rb'), as_attachment=True, filename=backup_filename)
                    # Gerar hash SHA256
                    sha256 = generate_sha256(backup_path)
                    hash_file = backup_path + '.sha256'
                    with open(hash_file, 'w') as hf:
                        hf.write(sha256)
                    logger.info(f"[DB BACKUP] SHA256: {sha256} salvo em {hash_file}")
                    messages.success(request, f"Backup do banco de dados MySQL gerado com sucesso!")
                    return response
            elif 'sqlite3' in db_engine:
                suffix = '.sqlite3'
                db_file = db_name
                if not os.path.exists(db_file):
                    logger.error(f"[DB BACKUP] Arquivo SQLite não encontrado: {db_file} por {request.user.username}")
                    print('### Arquivo SQLite não encontrado, retornando 404')
                    return HttpResponse(f'Arquivo SQLite não encontrado: {db_file}'.encode(), status=404)
                backup_dir = os.path.join(settings.BASE_DIR, 'backups', 'database')
                os.makedirs(backup_dir, exist_ok=True)
                backup_filename = f"{os.path.basename(db_file).replace('.sqlite3','')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
                backup_path = os.path.join(backup_dir, backup_filename)
                shutil.copy(db_file, backup_path)
                logger.info(f"[DB BACKUP] Sucesso: {backup_filename} salvo em {backup_path} por {request.user.username}")
                response = FileResponse(open(backup_path, 'rb'), as_attachment=True, filename=backup_filename)
                # Gerar hash SHA256
                sha256 = generate_sha256(backup_path)
                hash_file = backup_path + '.sha256'
                with open(hash_file, 'w') as hf:
                    hf.write(sha256)
                logger.info(f"[DB BACKUP] SHA256: {sha256} salvo em {hash_file}")
                messages.success(request, f"Backup do banco de dados SQLite gerado com sucesso!")
                return response
            else:
                logger.error(f"[DB BACKUP] Engine não suportado: {db_engine} por {request.user.username}")
                print('### Engine de banco não suportada, retornando 400')
                messages.error(request, f"Engine de banco não suportada: {db_engine}")
                return HttpResponse(f'Engine de banco não suportada: {db_engine}'.encode(), status=400)
        except Exception as e:
            logger.error(f"[DB BACKUP] Erro: {str(e)} por {request.user.username}", exc_info=True)
            print(f'### Erro ao gerar backup: {e}, retornando 500')
            messages.error(request, f"Erro ao gerar backup: {e}")
            return HttpResponse(f'Erro ao gerar backup: {e}'.encode(), status=500)

@method_decorator(staff_member_required, name='dispatch')
class BackupMediaView(View):
    def get(self, request):
        import os
        backups = list_backup_files('media')
        return render(request, 'config/backup_media.html', {'backups': backups})
    def post(self, request):
        import tempfile, shutil, os, datetime
        from django.conf import settings
        from django.http import FileResponse, HttpResponse
        media_root = settings.MEDIA_ROOT
        backup_dir = os.path.join(settings.BASE_DIR, 'backups', 'media')
        os.makedirs(backup_dir, exist_ok=True)
        if not os.path.exists(media_root):
            return HttpResponse('Pasta de mídia não encontrada.'.encode('utf-8'), status=404)
        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmpfile:
            tmpfile.close()
            logger.info(f"[MEDIA BACKUP] Iniciado por {request.user.username}")
            try:
                shutil.make_archive(tmpfile.name[:-7], 'gztar', media_root)
                tar_path = tmpfile.name[:-7] + '.tar.gz'
                backup_filename = f"media_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
                backup_path = os.path.join(backup_dir, backup_filename)
                shutil.copy(tar_path, backup_path)
                logger.info(f"[MEDIA BACKUP] Sucesso: {backup_filename} salvo em {backup_path} por {request.user.username}")
            except Exception as e:
                logger.error(f"[MEDIA BACKUP] Erro: {str(e)} por {request.user.username}", exc_info=True)
                return HttpResponse(f'Erro ao compactar mídia: {e}'.encode(), status=500)
            response = FileResponse(open(tar_path, 'rb'), as_attachment=True, filename='media_backup.tar.gz')
            return response

@method_decorator(staff_member_required, name='dispatch')
class DeleteBackupView(View):
    def post(self, request, backup_type, filename):
        allowed_types = ['database', 'media']
        if backup_type not in allowed_types:
            raise Http404('Tipo de backup inválido.')
        backup_dir = os.path.join(settings.BASE_DIR, 'backups', backup_type)
        file_path = os.path.join(backup_dir, filename)
        if not os.path.isfile(file_path) or not file_path.startswith(backup_dir):
            raise Http404('Arquivo não encontrado.')
        os.remove(file_path)
        # Remove hash se existir
        hash_file = file_path + '.sha256'
        if os.path.exists(hash_file):
            os.remove(hash_file)
        messages.success(request, f'Backup {filename} excluído com sucesso!')
        if backup_type == 'database':
            return redirect('config:backup_database')
        else:
            return redirect('config:backup_media')

@method_decorator(staff_member_required, name='dispatch')
class RestoreDatabaseView(View):
    def get(self, request):
        return render(request, 'config/restore_database_form.html')
    def post(self, request):
        import tempfile, os, shutil, datetime, subprocess
        from django.conf import settings
        from django.http import HttpResponse
        db_engine = settings.DATABASES['default']['ENGINE']
        db_name = settings.DATABASES['default']['NAME']
        db_user = settings.DATABASES['default'].get('USER', '')
        db_host = settings.DATABASES['default'].get('HOST', 'localhost')
        db_port = str(settings.DATABASES['default'].get('PORT', ''))
        db_password = settings.DATABASES['default'].get('PASSWORD', '')
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        if request.method == 'POST' and request.FILES.get('backup_file'):
            backup_file = request.FILES['backup_file']
            logger.info(f"[DB RESTORE] Iniciado por {request.user.username} para engine {db_engine}")
            try:
                # Salvar backup recebido temporariamente para validação de hash
                with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
                    for chunk in backup_file.chunks():
                        tmpfile.write(chunk)
                    tmpfile.close()
                    temp_backup_path = tmpfile.name
                # Procurar arquivo de hash correspondente (se existir)
                backup_dir = os.path.join(settings.BASE_DIR, 'backups', 'database')
                hash_file = None
                for f in os.listdir(backup_dir):
                    if f.startswith(os.path.splitext(backup_file.name)[0]) and f.endswith('.sha256'):
                        hash_file = os.path.join(backup_dir, f)
                        break
                if hash_file and os.path.exists(hash_file):
                    with open(hash_file) as hf:
                        expected_hash = hf.read().strip()
                    actual_hash = generate_sha256(temp_backup_path)
                    if expected_hash != actual_hash:
                        logger.error(f"[DB RESTORE] Hash inválido para {backup_file.name} por {request.user.username}")
                        os.remove(temp_backup_path)
                        messages.error(request, "Falha na validação de integridade do backup (SHA256).")
                        return HttpResponse(f'Falha na validação de integridade do backup (SHA256).'.encode('utf-8'), status=400)
                    logger.info(f"[DB RESTORE] Hash validado com sucesso para {backup_file.name} por {request.user.username}")
                    messages.success(request, "Backup validado com sucesso (SHA256).")
                # Segue fluxo normal de restauração, usando temp_backup_path como arquivo de backup
                if 'postgresql' in db_engine:
                    # Backup automático do banco atual
                    with tempfile.NamedTemporaryFile(suffix=f'_pre_restore_{timestamp}.backup', delete=False) as pre_bkp:
                        pre_bkp.close()
                        cmd_bkp = [
                            'pg_dump',
                            '-U', db_user,
                            '-h', db_host,
                            '-p', db_port or '5432',
                            '-F', 'c',
                            '-b',
                            '-v',
                            '-f', pre_bkp.name,
                            db_name
                        ]
                        env = os.environ.copy()
                        env['PGPASSWORD'] = db_password
                        subprocess.run(cmd_bkp, env=env, check=True)
                        logger.info(f"[DB RESTORE] Backup automático pré-restauração salvo em {pre_bkp.name} por {request.user.username}")
                    # Restaurar o novo backup enviado
                    cmd = [
                        'pg_restore',
                        '-U', db_user,
                        '-h', db_host,
                        '-p', db_port or '5432',
                        '-d', db_name,
                        '-c',
                        temp_backup_path
                    ]
                    env = os.environ.copy()
                    env['PGPASSWORD'] = db_password
                    subprocess.run(cmd, env=env, check=True)
                    logger.info(f"[DB RESTORE] Sucesso: restauração concluída por {request.user.username}")
                    os.remove(temp_backup_path)
                    messages.success(request, "Restauração do banco de dados concluída com sucesso!")
                    return HttpResponse(f'Restaurado com sucesso! Backup anterior salvo em {pre_bkp.name}'.encode('utf-8'))
                elif 'mysql' in db_engine:
                    with tempfile.NamedTemporaryFile(suffix=f'_pre_restore_{timestamp}.sql', delete=False, mode='w+', encoding='utf-8') as pre_bkp:
                        pre_bkp.close()
                        cmd_bkp = [
                            'mysqldump',
                            '-u', db_user,
                            f'-p{db_password}',
                            '-h', db_host,
                        ]
                        if db_port:
                            cmd_bkp += ['-P', db_port]
                        cmd_bkp += [db_name]
                        with open(pre_bkp.name, 'w', encoding='utf-8') as f:
                            subprocess.run(cmd_bkp, stdout=f, check=True)
                        logger.info(f"[DB RESTORE] Backup automático pré-restauração salvo em {pre_bkp.name} por {request.user.username}")
                    cmd = [
                        'mysql',
                        '-u', db_user,
                        f'-p{db_password}',
                        '-h', db_host,
                    ]
                    if db_port:
                        cmd += ['-P', db_port]
                    cmd += [db_name]
                    with open(temp_backup_path, 'rb') as f:
                        subprocess.run(cmd, stdin=f, check=True)
                    logger.info(f"[DB RESTORE] Sucesso: restauração concluída por {request.user.username}")
                    os.remove(temp_backup_path)
                    messages.success(request, "Restauração do banco de dados MySQL concluída com sucesso!")
                    return HttpResponse(f'Restaurado com sucesso! Backup anterior salvo em {pre_bkp.name}'.encode('utf-8'))
                elif 'sqlite3' in db_engine:
                    db_file = db_name
                    if not os.path.exists(db_file):
                        logger.error(f"[DB RESTORE] Arquivo SQLite não encontrado: {db_file} por {request.user.username}")
                        os.remove(temp_backup_path)
                        messages.error(request, f"Arquivo SQLite não encontrado: {db_file}")
                        return HttpResponse(f'Arquivo SQLite não encontrado: {db_file}'.encode(), status=404)
                    backup_dir = os.path.join(settings.BASE_DIR, 'backups', 'database')
                    os.makedirs(backup_dir, exist_ok=True)
                    backup_filename = f"{os.path.basename(db_file).replace('.sqlite3','')}_pre_restore_{timestamp}.sqlite3"
                    backup_path = os.path.join(backup_dir, backup_filename)
                    shutil.copy(db_file, backup_path)
                    logger.info(f"[DB RESTORE] Backup automático pré-restauração salvo em {backup_path} por {request.user.username}")
                    shutil.copy(temp_backup_path, db_file)
                    logger.info(f"[DB RESTORE] Sucesso: restauração concluída por {request.user.username}")
                    os.remove(temp_backup_path)
                    messages.success(request, "Restauração do banco de dados SQLite concluída com sucesso!")
                    return HttpResponse(f'Restaurado com sucesso! Backup anterior salvo em {backup_path}'.encode('utf-8'))
                else:
                    logger.error(f"[DB RESTORE] Engine não suportada: {db_engine} por {request.user.username}")
                    os.remove(temp_backup_path)
                    messages.error(request, f"Engine de banco não suportada: {db_engine}")
                    return HttpResponse(f'Engine de banco não suportada: {db_engine}'.encode(), status=400)
            except Exception as e:
                logger.error(f"[DB RESTORE] Erro: {str(e)} por {request.user.username}", exc_info=True)
                messages.error(request, f"Erro ao restaurar backup: {e}")
                return HttpResponse(f'Erro ao restaurar backup: {e}'.encode('utf-8'), status=500)
        return render(request, 'config/restore_database_form.html')

@method_decorator(staff_member_required, name='dispatch')
class RestoreMediaView(View):
    def get(self, request):
        return render(request, 'config/restore_media_form.html')
    def post(self, request):
        import tempfile, shutil, os, datetime
        from django.conf import settings
        from django.http import HttpResponse
        media_root = settings.MEDIA_ROOT
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        if request.method == 'POST' and request.FILES.get('media_file'):
            media_file = request.FILES['media_file']
            backup_name = f'media_pre_restore_{timestamp}'
            backup_path = os.path.join(tempfile.gettempdir(), backup_name)
            logger.info(f"[MEDIA RESTORE] Iniciado por {request.user.username}")
            try:
                shutil.make_archive(backup_path, 'zip', media_root)
                logger.info(f"[MEDIA RESTORE] Backup automático pré-restauração salvo em {backup_path}.zip por {request.user.username}")
            except Exception as e:
                logger.error(f"[MEDIA RESTORE] Erro no backup automático: {str(e)} por {request.user.username}", exc_info=True)
                return HttpResponse(f'Erro ao criar backup automático da mídia: {e}'.encode('utf-8'), status=500)
            with tempfile.NamedTemporaryFile(suffix='.upload', delete=False) as tmpfile:
                for chunk in media_file.chunks():
                    tmpfile.write(chunk)
                tmpfile.close()
                ext = os.path.splitext(media_file.name)[-1].lower()
                try:
                    if ext == '.zip':
                        shutil.unpack_archive(tmpfile.name, media_root, 'zip')
                    elif ext in ['.tar.gz', '.tgz']:
                        shutil.unpack_archive(tmpfile.name, media_root, 'gztar')
                    else:
                        logger.error(f"[MEDIA RESTORE] Formato de arquivo não suportado: {media_file.name} por {request.user.username}")
                        return HttpResponse('Formato de arquivo não suportado. Envie .zip ou .tar.gz'.encode('utf-8'), status=400)
                    logger.info(f"[MEDIA RESTORE] Sucesso: restauração concluída por {request.user.username}")
                except Exception as e:
                    logger.error(f"[MEDIA RESTORE] Erro: {str(e)} por {request.user.username}", exc_info=True)
                    return HttpResponse(f'Erro ao restaurar mídia: {e}'.encode('utf-8'), status=500)
            return HttpResponse(f'Restaurado com sucesso! Backup anterior salvo em {backup_path}.zip'.encode('utf-8'))
        return render(request, 'config/restore_media_form.html')

@staff_member_required
def download_backup(request, backup_type, filename):
    logger.info(f"[DOWNLOAD BACKUP] {backup_type}/{filename} solicitado por {request.user.username}")
    # Defina os diretórios permitidos
    allowed_types = ['database', 'media']
    if backup_type not in allowed_types:
        raise Http404('Tipo de backup inválido.')

    backup_dir = os.path.join(settings.BASE_DIR, 'backups', backup_type)
    file_path = os.path.join(backup_dir, filename)

    # Segurança: só permite arquivos dentro do diretório correto
    if not os.path.isfile(file_path) or not file_path.startswith(backup_dir):
        raise Http404('Arquivo não encontrado.')

    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename) 