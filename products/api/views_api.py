from rest_framework import generics, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, NumberFilter, CharFilter
from django.contrib.sites.shortcuts import get_current_site  # ✅

from products.models import Product, Comment
from .serializers import (
    ProductListSerializer, ProductDetailSerializer, CommentSerializer
)
from products.utils.sites import resolve_site_by_host


def get_queryset(self):
    site = resolve_site_by_host(self.request)
    return product_base_qs().filter(site=site).only(*PRODUCT_LIST_ONLY)


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'products': reverse('api_Product_list', request=request, format=format),
        'comments': reverse('api_comment_create', request=request, format=format),
    })


# ────────────────────────────────
# Фильтры для списка продуктов
# ────────────────────────────────
class ProductFilter(FilterSet):
    type = CharFilter(field_name="type", lookup_expr="iexact")
    category = NumberFilter(field_name="category_id", lookup_expr="exact")
    rating_min = NumberFilter(field_name="rating", lookup_expr="gte")
    rating_max = NumberFilter(field_name="rating", lookup_expr="lte")

    class Meta:
        model = Product
        fields = ["type", "category", "is_active"]


# Базовый оптимизированный queryset
def product_base_qs():
    return (
        Product.objects.filter(is_active=True)
        .select_related("category", "author")
        .prefetch_related("faqs", "polls__options", "best_products")
    )

PRODUCT_LIST_ONLY = [
    # собственные поля
    "id", "title", "slug", "type", "created_at", "is_active",
    "rating", "rating_1", "rating_2", "rating_3", "rating_4",
    "logo_file", "logo_url",

    # FK сами по себе тоже нужны при .only + select_related
    "category", "author",

    # поля связанных моделей, которые сериалайзер читает
    "category__id", "category__name", "category__type",
    "author__id", "author__name",
]


class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductListSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["title", "review_headline", "seo_title", "seo_description"]
    ordering_fields = ["created_at", "rating", "title"]
    ordering = ["-created_at"]

    def get_queryset(self):
        current_site = get_current_site(self.request)
        return product_base_qs().filter(site=current_site).only(*PRODUCT_LIST_ONLY)


class ProductDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        current_site = get_current_site(self.request)
        return product_base_qs().filter(site=current_site)


class CommentCreateAPIView(generics.CreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
