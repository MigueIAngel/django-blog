from django.db.models import Q
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from blog.models import Category, Post

from .permissions import IsAuthorOrReadOnly
from .serializers import (
    CategorySerializer,
    CommentSerializer,
    PostDetailSerializer,
    PostListSerializer,
)


class PostFilter(filters.FilterSet):
    category = filters.CharFilter(field_name="category__slug")
    tag = filters.CharFilter(field_name="tags__slug")
    author = filters.CharFilter(field_name="author__username")

    class Meta:
        model = Post
        fields = ["category", "tag", "author", "status"]


class PostViewSet(viewsets.ModelViewSet):
    """Blog posts. Published posts are public; authors also see their own drafts."""

    lookup_field = "slug"
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filterset_class = PostFilter
    search_fields = ["title", "body", "tags__name"]
    ordering_fields = ["published_at", "title", "created_at"]

    def get_queryset(self):
        user = self.request.user
        visible = Q(status=Post.Status.PUBLISHED)
        if user.is_authenticated:
            visible |= Q(author=user)
        return (
            Post.objects.filter(visible)
            .select_related("author", "category")
            .prefetch_related("tags", "comments__author")
            .distinct()
        )

    def get_serializer_class(self):
        return PostListSerializer if self.action == "list" else PostDetailSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @extend_schema(request=CommentSerializer, responses=CommentSerializer)
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
        serializer_class=CommentSerializer,
    )
    def comments(self, request, slug=None):
        post = self.get_object()
        if not post.is_published:
            return Response(
                {"detail": "Comments are only allowed on published posts."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(post=post, author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"
    pagination_class = None
