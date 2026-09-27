import pytest

from blog.models import Post


@pytest.mark.django_db
def test_slug_is_unique(author):
    first = Post.objects.create(title="Same title", body="a", author=author)
    second = Post.objects.create(title="Same title", body="b", author=author)
    assert first.slug == "same-title"
    assert second.slug == "same-title-2"


@pytest.mark.django_db
def test_publishing_sets_date_and_manager_filters_drafts(published_post, draft_post):
    assert published_post.published_at is not None
    assert draft_post.published_at is None
    assert list(Post.published.all()) == [published_post]


@pytest.mark.django_db
def test_markdown_is_rendered_and_sanitized(author):
    post = Post.objects.create(
        title="XSS", body="**ok** <script>alert(1)</script> [x](javascript:alert(1))", author=author
    )
    assert "<strong>ok</strong>" in post.body_html
    assert "<script>" not in post.body_html
    assert "javascript:" not in post.body_html


@pytest.mark.django_db
def test_excerpt_is_plain_text(published_post):
    assert published_post.excerpt == "Title Some bold text"
