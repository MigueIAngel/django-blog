from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, PostViewSet

app_name = "api"

router = DefaultRouter()
router.register("posts", PostViewSet, basename="post")
router.register("categories", CategoryViewSet, basename="category")

urlpatterns = [
    path("auth/token/", obtain_auth_token, name="token"),
    path("", include(router.urls)),
]
