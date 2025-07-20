from rest_framework import generics, filters
from .models import Game, Category, Comment
from .serializers import (
    GameListSerializer, GameDetailSerializer,
    CategorySerializer, CommentCreateSerializer
)
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from django_filters.rest_framework import DjangoFilterBackend

@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'categories': reverse('api_categories', request=request, format=format),
        'games': reverse('api_game_list', request=request, format=format),
        'comments': reverse('api_comment_create', request=request, format=format),
    })

class GameListAPIView(generics.ListAPIView):
    queryset = Game.objects.filter(is_active=True)
    serializer_class = GameListSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    filterset_fields = ["categories"]
    search_fields = ["title", "review_headline", "developer", "publisher"]
    ordering_fields = ["created_at", "rating_manual", "rating_external", "title"]
    ordering = ["-created_at"]


class GameDetailAPIView(generics.RetrieveAPIView):
    queryset = Game.objects.filter(is_active=True)
    serializer_class = GameDetailSerializer
    lookup_field = "slug"


class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CommentCreateAPIView(generics.CreateAPIView):
    serializer_class = CommentCreateSerializer
