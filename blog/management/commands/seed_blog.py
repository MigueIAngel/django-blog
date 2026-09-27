from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from blog.models import Category, Comment, Post, Tag

POSTS = [
    {
        "title": "Designing REST APIs that age well",
        "category": "Backend",
        "tags": ["api", "rest", "architecture"],
        "body": """Good APIs are boring in the best possible way.

## Principles

- **Nouns, not verbs**: `/orders/42`, not `/getOrder?id=42`.
- **Consistent errors**: always return a machine-readable code and a human message.
- **Pagination from day one**: adding it later breaks clients.

> An API is a contract. Version it like one.

```http
GET /api/v1/orders?status=paid&page=2
```
""",
    },
    {
        "title": "Why I reach for PostgreSQL first",
        "category": "Databases",
        "tags": ["postgresql", "sql"],
        "body": """PostgreSQL covers most needs before you need anything else.

## What you get for free

1. Transactions you can trust
2. `JSONB` columns when the schema is still moving
3. Full-text search good enough for many products
4. Row-level locking (`SELECT ... FOR UPDATE`) for inventory-like problems
""",
    },
    {
        "title": "HTMX: server-rendered apps that feel dynamic",
        "category": "Frontend",
        "tags": ["htmx", "django"],
        "body": """HTMX lets any element issue HTTP requests and swap the response into the page.

This blog uses it for **live search** and **comments**: the server returns small HTML
fragments and no client-side framework is needed.

```html
<input hx-get="/search/" hx-trigger="keyup changed delay:300ms" hx-target="#results">
```
""",
    },
    {
        "title": "Integrando APIs de facturación electrónica",
        "category": "Backend",
        "tags": ["api", "integrations"],
        "body": """Integrar un proveedor de facturación electrónica (PAC)
implica mucho más que un `POST`.

## Lecciones aprendidas

- **Trazabilidad**: registra cada request y response con un identificador de correlación.
- **Idempotencia**: los reintentos no deben duplicar comprobantes.
- **Validación temprana**: valida el XML antes de enviarlo.
""",
    },
    {
        "title": "Testing Django views with pytest",
        "category": "Testing",
        "tags": ["django", "pytest", "testing"],
        "body": """`pytest-django` makes Django tests shorter and easier to read.

```python
def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
```

Fixtures such as `client`, `admin_client` and `django_user_model` remove most of the boilerplate.
""",
    },
    {
        "title": "Docker Compose para desarrollo local",
        "category": "DevOps",
        "tags": ["docker", "devops"],
        "body": """Un `docker-compose.yml` bien hecho reduce el *onboarding* de días a minutos.

- Usa `healthcheck` para que la API espere a la base de datos.
- Monta volúmenes para persistir datos.
- Nunca subas secretos: usa variables de entorno.
""",
    },
]

COMMENTS = [
    "Great write-up, thanks for sharing!",
    "¡Muy útil, gracias!",
    "I would add rate limiting to the list.",
]


class Command(BaseCommand):
    help = "Create demo users, categories, tags, posts and comments."

    def handle(self, *args, **options):
        User = get_user_model()
        if Post.objects.exists():
            self.stdout.write("Blog already has posts, skipping seed.")
            return

        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "is_staff": True,
                "is_superuser": True,
                "first_name": "Admin",
            },
        )
        if created:
            admin.set_password("admin12345")
            admin.save()
        reader, created = User.objects.get_or_create(
            username="reader", defaults={"email": "reader@example.com", "first_name": "Reader"}
        )
        if created:
            reader.set_password("reader12345")
            reader.save()

        now = timezone.now()
        for index, data in enumerate(POSTS):
            category, _ = Category.objects.get_or_create(name=data["category"])
            post = Post.objects.create(
                title=data["title"],
                body=data["body"],
                author=admin,
                category=category,
                status=Post.Status.PUBLISHED,
                published_at=now - timedelta(days=index * 3),
            )
            post.tags.set([Tag.objects.get_or_create(name=name)[0] for name in data["tags"]])
            Comment.objects.create(post=post, author=reader, body=COMMENTS[index % len(COMMENTS)])

        Post.objects.create(
            title="Draft: GraphQL vs REST",
            body="Work in progress.",
            author=admin,
            status=Post.Status.DRAFT,
        )
        self.stdout.write(self.style.SUCCESS("Demo data created (admin / admin12345)."))
