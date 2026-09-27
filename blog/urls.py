from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    path("", views.PostListView.as_view(), name="post_list"),
    path("category/<slug:category_slug>/", views.PostListView.as_view(), name="category"),
    path("tag/<slug:tag_slug>/", views.PostListView.as_view(), name="tag"),
    path("posts/new/", views.PostCreateView.as_view(), name="post_create"),
    path("posts/mine/", views.MyPostsView.as_view(), name="my_posts"),
    path("posts/<slug:slug>/", views.PostDetailView.as_view(), name="post_detail"),
    path("posts/<slug:slug>/edit/", views.PostUpdateView.as_view(), name="post_update"),
    path("posts/<slug:slug>/comments/", views.add_comment, name="add_comment"),
    path("signup/", views.SignUpView.as_view(), name="signup"),
]
