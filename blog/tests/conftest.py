import pytest
from django.core.cache import cache

from blog.models import Category, Post


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    cache.clear()


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create_user("author", password="pass12345!")


@pytest.fixture
def other_user(django_user_model):
    return django_user_model.objects.create_user("other", password="pass12345!")


@pytest.fixture
def category(db):
    return Category.objects.create(name="Backend")


@pytest.fixture
def published_post(author, category):
    return Post.objects.create(
        title="Hello Django",
        body="# Title\n\nSome **bold** text",
        author=author,
        category=category,
        status=Post.Status.PUBLISHED,
    )


@pytest.fixture
def draft_post(author):
    return Post.objects.create(title="Secret draft", body="WIP", author=author)
