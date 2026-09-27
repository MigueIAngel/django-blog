from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import CommentForm, PostForm, SignUpForm
from .models import Category, Post, Tag


class PostListView(ListView):
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 6

    def get_queryset(self):
        queryset = (
            Post.published.select_related("author", "category")
            .prefetch_related("tags")
            .annotate(comment_count=Count("comments"))
            .order_by("-published_at", "-id")
        )
        if slug := self.kwargs.get("category_slug"):
            self.category = get_object_or_404(Category, slug=slug)
            queryset = queryset.filter(category=self.category)
        if slug := self.kwargs.get("tag_slug"):
            self.tag = get_object_or_404(Tag, slug=slug)
            queryset = queryset.filter(tags=self.tag)
        if query := self.request.GET.get("q", "").strip():
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(body__icontains=query)
                | Q(tags__name__icontains=query)
            ).distinct()
        return queryset

    def get_template_names(self):
        # HTMX live search only needs the results fragment.
        if self.request.headers.get("HX-Request") and self.request.GET.get("partial"):
            return ["blog/partials/post_results.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = getattr(self, "category", None)
        context["tag"] = getattr(self, "tag", None)
        context["query"] = self.request.GET.get("q", "")
        context["categories"] = Category.objects.annotate(
            total=Count("posts", filter=Q(posts__status=Post.Status.PUBLISHED))
        ).filter(total__gt=0)
        return context


class PostDetailView(DetailView):
    template_name = "blog/post_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        # Authors can preview their own drafts.
        user = self.request.user
        visible = Q(status=Post.Status.PUBLISHED)
        if user.is_authenticated:
            visible |= Q(author=user)
        return Post.objects.filter(visible).select_related("author", "category")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comments"] = self.object.comments.select_related("author")
        context["comment_form"] = CommentForm()
        context["related"] = (
            Post.published.filter(category=self.object.category)
            .exclude(pk=self.object.pk)
            .only("title", "slug", "published_at")[:3]
        )
        return context


@login_required
@require_POST
def add_comment(request: HttpRequest, slug: str) -> HttpResponse:
    post = get_object_or_404(Post.published, slug=slug)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        if request.headers.get("HX-Request"):
            return render(
                request,
                "blog/partials/comment_created.html",
                {"comment": comment, "comment_form": CommentForm(), "post": post},
            )
        return redirect(post)
    if request.headers.get("HX-Request"):
        response = render(
            request, "blog/partials/comment_form.html", {"comment_form": form, "post": post}
        )
        response["HX-Retarget"] = "#comment-form"
        return response
    return redirect(post)


class AuthorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self) -> bool:
        return self.get_object().author == self.request.user


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "blog/post_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, _("Post saved."))
        return super().form_valid(form)


class PostUpdateView(AuthorRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "blog/post_form.html"

    def form_valid(self, form):
        messages.success(self.request, _("Post saved."))
        return super().form_valid(form)


class MyPostsView(LoginRequiredMixin, ListView):
    template_name = "blog/my_posts.html"
    context_object_name = "posts"

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user).select_related("category")


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("blog:post_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, _("Welcome! Your account was created."))
        return response
