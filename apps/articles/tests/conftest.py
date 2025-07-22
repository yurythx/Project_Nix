import pytest
import factory
from factory.declarations import Sequence, LazyAttribute, PostGenerationMethodCall, SubFactory
from django.contrib.auth import get_user_model
from apps.articles.models import Article, Comment
from apps.config.models import AppModuleConfiguration

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    username = Sequence(lambda n: f'user{n}')
    email = LazyAttribute(lambda o: f'{o.username}@example.com')
    password = PostGenerationMethodCall('set_password', '123456')

class ArticleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Article
    title = Sequence(lambda n: f'Artigo {n}')
    slug = Sequence(lambda n: f'artigo-{n}')
    content = 'Conteúdo de teste'
    status = 'published'
    author = SubFactory(UserFactory)

class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment
    article = SubFactory(ArticleFactory)
    name = Sequence(lambda n: f'Comentador {n}')
    email = LazyAttribute(lambda o: f'{o.name.lower().replace(" ", "")}@example.com')
    content = 'Comentário de teste'
    is_approved = True

@pytest.fixture
def user_factory():
    return UserFactory

@pytest.fixture
def article_factory():
    return ArticleFactory

@pytest.fixture
def comment_factory():
    return CommentFactory

@pytest.fixture(autouse=True)
def enable_articles_module(db):
    for app_name in ['articles', 'apps.articles']:
        AppModuleConfiguration.objects.update_or_create(
            app_name=app_name,
            defaults={
                'display_name': 'Artigos',
                'is_enabled': True,
                'status': 'active',
                'module_type': 'feature',
            }
        ) 