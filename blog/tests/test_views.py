import pytest
from django.urls import reverse

from blog.models import Comment


@pytest.mark.django_db
def test_home_lists_only_published_posts(client, published_post, draft_post):
    response = client.get(reverse("blog:post_list"))
    assert response.status_code == 200
    assert published_post.title in response.content.decode()
    assert draft_post.title not in response.content.decode()


@pytest.mark.django_db
def test_live_search_returns_partial(client, published_post):
    response = client.get(
        reverse("blog:post_list"), {"q": "django", "partial": "1"}, HTTP_HX_REQUEST="true"
    )
    content = response.content.decode()
    assert "<html" not in content
    assert published_post.title in content


@pytest.mark.django_db
def test_spanish_home_is_translated(client, published_post):
    response = client.get("/es/")
    assert "Buscar artículos" in response.content.decode()


@pytest.mark.django_db
def test_drafts_are_hidden_from_other_users(client, other_user, draft_post):
    client.force_login(other_user)
    assert client.get(draft_post.get_absolute_url()).status_code == 404


@pytest.mark.django_db
def test_author_can_preview_draft(client, author, draft_post):
    client.force_login(author)
    assert client.get(draft_post.get_absolute_url()).status_code == 200


@pytest.mark.django_db
def test_htmx_comment_returns_fragment(client, other_user, published_post):
    client.force_login(other_user)
    url = reverse("blog:add_comment", args=[published_post.slug])
    response = client.post(url, {"body": "Nice post!"}, HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    assert "Nice post!" in response.content.decode()
    assert Comment.objects.filter(post=published_post, author=other_user).count() == 1


@pytest.mark.django_db
def test_comment_requires_login(client, published_post):
    url = reverse("blog:add_comment", args=[published_post.slug])
    response = client.post(url, {"body": "Hi"})
    assert response.status_code == 302
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_only_author_can_edit(client, other_user, published_post):
    client.force_login(other_user)
    assert client.get(reverse("blog:post_update", args=[published_post.slug])).status_code == 403


@pytest.mark.django_db
def test_create_post_with_tags(client, author, category):
    client.force_login(author)
    response = client.post(
        reverse("blog:post_create"),
        {
            "title": "New one",
            "body": "Body",
            "category": category.pk,
            "status": "published",
            "tags_text": "python, django",
        },
    )
    assert response.status_code == 302
    post = author.posts.get(title="New one")
    assert sorted(t.name for t in post.tags.all()) == ["django", "python"]
