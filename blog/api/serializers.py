from django.contrib.auth import get_user_model
from rest_framework import serializers

from blog.models import Category, Comment, Post, Tag


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "author", "body", "created_at"]


class PostListSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    url = serializers.HyperlinkedIdentityField(view_name="api:post-detail", lookup_field="slug")

    class Meta:
        model = Post
        fields = [
            "id",
            "url",
            "title",
            "slug",
            "excerpt",
            "author",
            "category",
            "tags",
            "status",
            "published_at",
            "reading_time",
        ]


class PostDetailSerializer(PostListSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only=True,
        required=False,
        allow_null=True,
    )
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50), write_only=True, required=False
    )
    body_html = serializers.CharField(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + [
            "body",
            "body_html",
            "category_id",
            "tag_names",
            "comments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["slug", "published_at"]

    def _set_tags(self, post: Post, names: list[str] | None) -> None:
        if names is not None:
            post.tags.set([Tag.objects.get_or_create(name=name.strip())[0] for name in names])

    def create(self, validated_data):
        names = validated_data.pop("tag_names", None)
        post = super().create(validated_data)
        self._set_tags(post, names)
        return post

    def update(self, instance, validated_data):
        names = validated_data.pop("tag_names", None)
        post = super().update(instance, validated_data)
        self._set_tags(post, names)
        return post
