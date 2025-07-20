from rest_framework import serializers
from .models import Game, Category, Screenshot, Poll, PollOption, Comment, FAQ


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class ScreenshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Screenshot
        fields = ["id", "image_file", "image_url"]


class PollOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollOption
        fields = ["id", "text"]


class PollSerializer(serializers.ModelSerializer):
    options = PollOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Poll
        fields = ["id", "question", "options"]


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ["id", "question", "answer"]


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "name", "text", "created_at"]
        read_only_fields = ["created_at"]


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["game", "name", "email", "text"]


class GameListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ["id", "title", "slug", "review_headline", "get_logo", "rating_manual"]


class GameDetailSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    screenshots = ScreenshotSerializer(many=True, read_only=True)
    poll = PollSerializer(read_only=True)
    faqs = FAQSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Game
        fields = [
            "id", "title", "slug", "steam_id", "is_active",
            "developer", "publisher", "get_logo",
            "rating_manual", "rating_external",
            "review_headline", "review_body",
            "pros", "cons", "created_at",
            "categories", "screenshots", "poll", "faqs", "comments"
        ]
