from django.urls import path
from . import views_api

urlpatterns = [
    path("", views_api.api_root, name="api_root"),
    path("products/", views_api.ProductListAPIView.as_view(), name="api_Product_list"),
    path("products/<slug:slug>/", views_api.ProductDetailAPIView.as_view(), name="api_Product_detail"),
    path("comments/", views_api.CommentCreateAPIView.as_view(), name="api_comment_create"),
]