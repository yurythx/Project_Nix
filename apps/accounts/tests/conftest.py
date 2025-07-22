import pytest
import factory
from django.contrib.auth import get_user_model

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@example.com')
    first_name = 'Test'
    last_name = 'User'
    is_active = True
    is_verified = True
    password = factory.PostGenerationMethodCall('set_password', 'senha123')

@pytest.fixture
def user_factory():
    return UserFactory 