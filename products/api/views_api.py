from rest_framework import generics, filters
from products.models import Product, Comment
from .serializers import (
    ProductSerializer, ProductDetailSerializer, CommentSerializer
)
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from django_filters.rest_framework import DjangoFilterBackend


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'products': reverse('api_Product_list', request=request, format=format),
        'comments': reverse('api_comment_create', request=request, format=format),
    })


class ProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    search_fields = ["title", "review_headline", "developer", "publisher"]
    ordering_fields = ["created_at", "rating_manual", "rating_external", "title"]
    ordering = ["-created_at"]


class ProductDetailAPIView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductDetailSerializer
    lookup_field = "slug"


class CommentCreateAPIView(generics.CreateAPIView):
    serializer_class = CommentSerializer
