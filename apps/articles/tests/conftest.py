import pytest
import factory
from factory.declarations import Sequence, LazyAttribute, PostGenerationMethodCall, SubFactory

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
def article_factory(user_factory):
    from apps.articles.models import Article
    class ArticleFactory(factory.django.DjangoModelFactory):
        class Meta:
            model = Article
        title = Sequence(lambda n: f'Artigo {n}')
        slug = Sequence(lambda n: f'artigo-{n}')
        content = 'Conteúdo de teste'
        status = 'published'
        author = SubFactory(user_factory)
    return ArticleFactory

@pytest.fixture
def comment_factory(article_factory):
    from apps.articles.models import Comment
    class CommentFactory(factory.django.DjangoModelFactory):
        class Meta:
            model = Comment
        article = SubFactory(article_factory)
        name = Sequence(lambda n: f'Comentador {n}')
        email = LazyAttribute(lambda o: f'{o.name.lower().replace(" ", "")}@example.com')
        content = 'Comentário de teste'
        is_approved = True
    return CommentFactory

@pytest.fixture(autouse=True)
def enable_articles_module(db):
    from apps.config.models import AppModuleConfiguration
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