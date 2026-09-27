from django.contrib import admin

from .models import Category, Comment, Post, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ["name"]}


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ["author", "created_at"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "category", "status", "published_at"]
    list_filter = ["status", "category", "tags", "published_at"]
    search_fields = ["title", "body"]
    prepopulated_fields = {"slug": ["title"]}
    autocomplete_fields = ["tags"]
    raw_id_fields = ["author"]
    date_hierarchy = "published_at"
    inlines = [CommentInline]
    actions = ["publish"]

    @admin.action(description="Publish selected posts")
    def publish(self, request, queryset):
        for post in queryset:
            post.status = Post.Status.PUBLISHED
            post.save()


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["post", "author", "created_at"]
    search_fields = ["body"]
