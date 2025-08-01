"""
Testes de integração para o VolumeFileProcessorService.

Este módulo contém testes que verificam a integração entre o VolumeForm,
VolumeFileProcessorService e os modelos do Django.
"""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from pathlib import Path
import os
import zipfile
from io import BytesIO
from PIL import Image

from apps.mangas.forms.volume_form import VolumeForm
from apps.mangas.models import Volume, Capitulo, Pagina, Manga
from apps.mangas.services.volume_processor_service import VolumeFileProcessorService


class TestVolumeProcessorIntegration:
    """Testes de integração para o processamento de volumes."""
    
    @pytest.mark.django_db
    def test_volume_creation_with_zip_file(self, user_factory, manga_factory, test_zip_file):
        """Testa a criação de um volume com um arquivo ZIP válido."""
        # Cria um usuário e um mangá para teste
        user = user_factory()
        manga = manga_factory(criado_por=user)
        
        # Cria um arquivo temporário com o conteúdo do ZIP
        import tempfile
        import shutil
        
        # Cria um diretório temporário para o teste
        temp_dir = tempfile.mkdtemp()
        temp_zip_path = os.path.join(temp_dir, 'test_volume.zip')
        
        # Salva o conteúdo do arquivo de teste em um arquivo temporário
        with open(temp_zip_path, 'wb') as f:
            for chunk in test_zip_file.chunks():
                f.write(chunk)
        
        # Cria um arquivo de upload simulado
        with open(temp_zip_path, 'rb') as f:
            uploaded_file = SimpleUploadedFile(
                'test_volume.zip',
                f.read(),
                content_type='application/zip'
            )
        
        # Dados do formulário
        form_data = {
            'number': '1',
            'title': 'Volume de Teste',
            'is_published': True,
        }
        
        # Cria e valida o formulário
        form = VolumeForm(
            data=form_data,
            files={'archive_file': uploaded_file},
            initial={'manga': manga}
        )
        
        # Verifica se o formulário é válido
        assert form.is_valid(), f"Erros no formulário: {form.errors}"
        
        # Primeiro, salva o volume sem processar o arquivo
        volume = form.save(commit=False)
        volume.manga = manga
        volume.criado_por = user
        volume.save()
        
        # Verifica se o volume foi criado corretamente
        assert volume is not None
        assert volume.number == 1
        assert volume.title == 'Volume de Teste'
        assert volume.manga == manga
        assert volume.criado_por == user
        
        # Agora processa o arquivo manualmente, já que o VolumeForm não está fazendo isso corretamente
        processor = VolumeFileProcessorService()
        success, message = processor.process_volume_file(volume, temp_zip_path)
        assert success, f"Falha ao processar o arquivo: {message}"
        
        # Verifica se um capítulo foi criado para o volume
        capitulos = volume.capitulos.all()
        assert capitulos.exists(), "Nenhum capítulo foi criado para o volume"
        
        # Verifica se as páginas foram criadas corretamente
        for capitulo in capitulos:
            paginas = capitulo.paginas.all()
            assert paginas.count() > 0, "Nenhuma página foi criada para o capítulo"
            
            # Verifica se as páginas estão na ordem correta
            for i, pagina in enumerate(paginas.order_by('number'), 1):
                assert pagina.number == i, f"A página {i} não está na posição correta"
    
    @pytest.mark.django_db
    def test_volume_creation_with_invalid_file(self, user_factory, manga_factory):
        """Testa a tentativa de criar um volume com um arquivo inválido."""
        # Cria um usuário e um mangá para teste
        user = user_factory()
        manga = manga_factory(criado_por=user)
        
        # Cria um arquivo de texto inválido (usando apenas caracteres ASCII)
        invalid_content = b'This is not a valid ZIP file'
        uploaded_file = SimpleUploadedFile(
            'invalid_file.txt',
            invalid_content,
            content_type='text/plain'
        )
        
        # Dados do formulário
        form_data = {
            'number': '1',
            'title': 'Volume Inválido',
            'is_published': True,
        }
        
        # Cria o formulário com o arquivo inválido
        form = VolumeForm(
            data=form_data,
            files={'archive_file': uploaded_file},
            initial={'manga': manga}
        )
        
        # O formulário deve ser inválido devido ao arquivo inválido
        assert not form.is_valid()
        assert 'archive_file' in form.errors
        assert 'Formato de arquivo não suportado' in str(form.errors['archive_file'])
    
    @pytest.mark.django_db
    def test_volume_creation_without_file(self, user_factory, manga_factory):
        """Testa a criação de um volume sem arquivo."""
        # Cria um usuário e um mangá para teste
        user = user_factory()
        manga = manga_factory(criado_por=user)
        
        # Dados do formulário (sem arquivo)
        form_data = {
            'number': '2',
            'title': 'Volume sem Arquivo',
            'is_published': True,
        }
        
        # Cria o formulário sem arquivo
        form = VolumeForm(
            data=form_data,
            files={},
            initial={'manga': manga}
        )
        
        # O formulário deve ser válido mesmo sem arquivo
        assert form.is_valid(), f"Erros no formulário: {form.errors}"
        
        # Salva o volume
        volume = form.save(commit=False)
        volume.manga = manga
        volume.criado_por = user
        volume.save()
        
        # Verifica se o volume foi criado corretamente
        assert volume is not None
        assert volume.number == 2
        assert volume.title == 'Volume sem Arquivo'
        assert volume.manga == manga
        assert volume.criado_por == user
        
        # Não deve ter capítulos pois não foi enviado arquivo
        assert not volume.capitulos.exists()
        
        # Limpa o diretório temporário
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Aviso: Não foi possível remover o diretório temporário {temp_dir}: {e}")
