from django.urls import path
from . import views

urlpatterns = [
    path("", views.api_root, name="api_root"),
    path("games/", views.GameListAPIView.as_view(), name="api_game_list"),
    path("games/<slug:slug>/", views.GameDetailAPIView.as_view(), name="api_game_detail"),
    path("categories/", views.CategoryListAPIView.as_view(), name="api_categories"),
    path("comments/", views.CommentCreateAPIView.as_view(), name="api_comment_create"),
]