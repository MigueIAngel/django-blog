import pytest
from rest_framework.test import APIClient

from blog.models import Post


@pytest.fixture
def api():
    return APIClient()


@pytest.mark.django_db
def test_list_is_public_and_hides_drafts(api, published_post, draft_post):
    response = api.get("/api/posts/")
    assert response.status_code == 200
    slugs = [item["slug"] for item in response.data["results"]]
    assert slugs == [published_post.slug]


@pytest.mark.django_db
def test_filter_by_category_and_search(api, published_post):
    assert api.get("/api/posts/?category=backend").data["count"] == 1
    assert api.get("/api/posts/?category=frontend").data["count"] == 0
    assert api.get("/api/posts/?search=hello").data["count"] == 1


@pytest.mark.django_db
def test_token_auth_and_create(api, author):
    token = api.post("/api/auth/token/", {"username": "author", "password": "pass12345!"}).data
    api.credentials(HTTP_AUTHORIZATION=f"Token {token['token']}")
    response = api.post(
        "/api/posts/",
        {"title": "From API", "body": "Hi", "status": "published", "tag_names": ["api"]},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["author"]["username"] == "author"
    assert response.data["tags"] == ["api"]


@pytest.mark.django_db
def test_anonymous_cannot_create(api):
    response = api.post("/api/posts/", {"title": "x", "body": "y"}, format="json")
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_only_author_can_update(api, other_user, published_post):
    api.force_authenticate(other_user)
    response = api.patch(f"/api/posts/{published_post.slug}/", {"title": "Hacked"}, format="json")
    assert response.status_code == 403
    published_post.refresh_from_db()
    assert published_post.title == "Hello Django"


@pytest.mark.django_db
def test_comment_action(api, other_user, published_post, draft_post, author):
    api.force_authenticate(other_user)
    ok = api.post(f"/api/posts/{published_post.slug}/comments/", {"body": "Great"}, format="json")
    assert ok.status_code == 201
    assert ok.data["author"]["username"] == "other"

    api.force_authenticate(author)
    draft = api.post(f"/api/posts/{draft_post.slug}/comments/", {"body": "x"}, format="json")
    assert draft.status_code == 400


@pytest.mark.django_db
def test_openapi_schema_is_available(api):
    response = api.get("/api/schema/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_author_sees_own_drafts(api, author, draft_post):
    api.force_authenticate(author)
    slugs = [p["slug"] for p in api.get("/api/posts/").data["results"]]
    assert draft_post.slug in slugs
    assert Post.objects.count() == 1
