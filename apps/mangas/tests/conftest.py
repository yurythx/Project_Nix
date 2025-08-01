import pytest
import factory
from factory.declarations import Sequence, LazyAttribute, PostGenerationMethodCall, SubFactory
from django.core.files.uploadedfile import SimpleUploadedFile
import os
import tempfile
from PIL import Image
import io


@pytest.fixture
def user_factory():
    from django.contrib.auth import get_user_model
    class UserFactory(factory.django.DjangoModelFactory):
        class Meta:
            model = get_user_model()
        username = Sequence(lambda n: f'user{n}')
        email = LazyAttribute(lambda o: f'{o.username}@example.com')
        password = PostGenerationMethodCall('set_password', '123456')
    return UserFactory


@pytest.fixture
def admin_user_factory(user_factory):
    class AdminUserFactory(user_factory):
        is_staff = True
        is_superuser = True
    return AdminUserFactory


@pytest.fixture
def staff_user_factory(user_factory):
    class StaffUserFactory(user_factory):
        is_staff = True
    return StaffUserFactory


@pytest.fixture
def manga_factory(user_factory):
    from apps.mangas.models import Manga
    class MangaFactory(factory.django.DjangoModelFactory):
        class Meta:
            model = Manga
            skip_postgeneration_save = True  # Evita salvar automaticamente após a geração
            
        title = Sequence(lambda n: f'Manga Teste {n}')
        slug = Sequence(lambda n: f'manga-teste-{n}')
        description = 'Descrição de teste do mangá'
        author = 'Autor Teste'
        is_published = True
        criado_por = SubFactory(user_factory)
        
        @classmethod
        def _create(cls, model_class, *args, **kwargs):
            # Remove campos que não são do modelo antes de criar a instância
            kwargs.pop('status', None)
            return super()._create(model_class, *args, **kwargs)
            
    return MangaFactory


@pytest.fixture
def volume_factory(manga_factory):
    from apps.mangas.models import Volume
    class VolumeFactory(factory.django.DjangoModelFactory):
        class Meta:
            model = Volume
        title = Sequence(lambda n: f'Volume {n}')
        slug = Sequence(lambda n: f'volume-{n}')
        number = Sequence(lambda n: n + 1)
        manga = SubFactory(manga_factory)
    return VolumeFactory


@pytest.fixture
def capitulo_factory(volume_factory):
    from apps.mangas.models import Capitulo
    class CapituloFactory(factory.django.DjangoModelFactory):
        class Meta:
            model = Capitulo
        title = Sequence(lambda n: f'Capítulo {n}')
        slug = Sequence(lambda n: f'capitulo-{n}')
        number = Sequence(lambda n: n + 1)
        volume = SubFactory(volume_factory)
    return CapituloFactory


@pytest.fixture
def pagina_factory(capitulo_factory):
    from apps.mangas.models import Pagina
    class PaginaFactory(factory.django.DjangoModelFactory):
        class Meta:
            model = Pagina
        number = Sequence(lambda n: n + 1)
        capitulo = SubFactory(capitulo_factory)
        
        @factory.post_generation
        def create_image(self, create, extracted, **kwargs):
            if not create:
                return
            
            # Cria uma imagem de teste
            image = Image.new('RGB', (100, 100), color='red')
            image_io = io.BytesIO()
            image.save(image_io, format='JPEG')
            image_io.seek(0)
            
            # Cria um arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(image_io.getvalue())
                tmp_file_path = tmp_file.name
            
            # Cria o SimpleUploadedFile
            with open(tmp_file_path, 'rb') as f:
                uploaded_file = SimpleUploadedFile(
                    name=f'test_page_{self.number}.jpg',
                    content=f.read(),
                    content_type='image/jpeg'
                )
                self.image = uploaded_file
            
            # Remove o arquivo temporário
            os.unlink(tmp_file_path)
    
    return PaginaFactory


@pytest.fixture
def test_image_file():
    """Cria um arquivo de imagem de teste"""
    image = Image.new('RGB', (100, 100), color='blue')
    image_io = io.BytesIO()
    image.save(image_io, format='JPEG')
    image_io.seek(0)
    
    return SimpleUploadedFile(
        name='test_image.jpg',
        content=image_io.getvalue(),
        content_type='image/jpeg'
    )


@pytest.fixture
def test_zip_file():
    """Cria um arquivo ZIP de teste com imagens"""
    import zipfile
    from io import BytesIO
    
    # Cria um arquivo ZIP com algumas imagens de teste
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for i in range(3):
            # Cria uma imagem de teste
            image = Image.new('RGB', (100, 100), color=(i * 50, 100, 150))
            image_io = BytesIO()
            image.save(image_io, format='JPEG')
            image_io.seek(0)
            
            # Adiciona a imagem ao ZIP
            zip_file.writestr(f'page_{i+1:03d}.jpg', image_io.getvalue())
    
    zip_buffer.seek(0)
    return SimpleUploadedFile(
        name='test_chapter.zip',
        content=zip_buffer.getvalue(),
        content_type='application/zip'
    )


@pytest.fixture
def test_pdf_file():
    """Cria um arquivo PDF de teste"""
    from reportlab.pdfgen import canvas
    from io import BytesIO
    
    # Cria um PDF simples com algumas páginas
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer)
    
    for i in range(3):
        c.drawString(100, 750, f'Página de teste {i+1}')
        c.drawString(100, 700, f'Esta é uma página de teste para o capítulo')
        c.showPage()
    
    c.save()
    pdf_buffer.seek(0)
    
    return SimpleUploadedFile(
        name='test_chapter.pdf',
        content=pdf_buffer.getvalue(),
        content_type='application/pdf'
    )


@pytest.fixture(autouse=True)
def enable_mangas_module(db):
    """Habilita o módulo de mangas para os testes"""
    from apps.config.models import AppModuleConfiguration
    AppModuleConfiguration.objects.update_or_create(
        app_name='mangas',
        defaults={
            'display_name': 'Mangás',
            'is_enabled': True,
            'status': 'active',
            'module_type': 'feature',
        }
    )


@pytest.fixture
def client_with_user(client, user_factory):
    """Cliente com usuário logado"""
    user = user_factory()
    client.force_login(user)
    return client


@pytest.fixture
def client_with_admin(client, admin_user_factory):
    """Cliente com usuário admin logado"""
    admin_user = admin_user_factory()
    client.force_login(admin_user)
    return client


@pytest.fixture
def client_with_staff(client, staff_user_factory):
    """Cliente com usuário staff logado"""
    staff_user = staff_user_factory()
    client.force_login(staff_user)
    return client 
