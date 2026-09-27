from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import Comment, Post, Tag


class PostForm(forms.ModelForm):
    tags_text = forms.CharField(
        label=_("Tags"),
        required=False,
        help_text=_("Comma-separated, e.g. django, python"),
    )

    class Meta:
        model = Post
        fields = ["title", "category", "excerpt", "body", "status"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 14}),
            "excerpt": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["tags_text"].initial = ", ".join(t.name for t in self.instance.tags.all())

    def save(self, commit: bool = True) -> Post:
        post = super().save(commit=commit)
        if commit:
            names = {n.strip() for n in self.cleaned_data["tags_text"].split(",") if n.strip()}
            post.tags.set([Tag.objects.get_or_create(name=name)[0] for name in names])
        return post


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        labels = {"body": ""}
        widgets = {"body": forms.Textarea(attrs={"rows": 3, "placeholder": _("Write a comment…")})}


class SignUpForm(UserCreationForm):
    email = forms.EmailField(label=_("Email"))

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ["username", "email"]
