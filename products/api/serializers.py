from rest_framework import serializers
from django.contrib.sites.models import Site

from products.models import (
    Product, Category, Author, FAQ, Poll, PollOption, Comment
)

# ────────────────────────────────
# Small serializers
# ────────────────────────────────

class CategorySerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "type", "type_display"]


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name"]


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ["id", "question", "answer"]


class PollOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollOption
        fields = ["id", "text"]


class PollSerializer(serializers.ModelSerializer):
    options = PollOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Poll
        fields = ["id", "question", "options"]


class BestProductMiniSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "title", "slug", "type", "logo"]

    def get_logo(self, obj):
        return obj.get_logo()


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ["id", "domain", "name"]


class CommentSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = Comment
        fields = ['id', 'product', 'name', 'email', 'text', 'status', 'created_at']
        read_only_fields = ['status', 'created_at']

# ────────────────────────────────
# Product list & detail
# ────────────────────────────────

class ProductListSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "title", "slug", "type",
            "logo",
            "category", "author",
            "rating", "rating_1", "rating_2", "rating_3", "rating_4",
            "created_at", "is_active",
        ]

    def get_logo(self, obj):
        return obj.get_logo()


class ProductDetailSerializer(serializers.ModelSerializer):
    # relations
    category = CategorySerializer(read_only=True)
    author = AuthorSerializer(read_only=True)
    faqs = FAQSerializer(many=True, read_only=True)
    polls = PollSerializer(many=True, read_only=True)
    best_products = BestProductMiniSerializer(many=True, read_only=True)

    # computed / удобные представления
    logo = serializers.SerializerMethodField()
    pros_list = serializers.SerializerMethodField()
    cons_list = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            # identity / meta
            "id", "created_at",
            "title", "slug", "type", "steam_id",

            # taxonomy / people
            "category", "author", "publishers", "developers",

            # button / release meta
            "button_text", "required_age", "release_date",

            # type-specific (movie/app)
            "length", "director", "actors", "country",  # movie-only
            "version",                                   # app-only

            # system requirements (games/apps)
            "min_os", "min_processor", "min_ram", "min_graphics", "min_storage", "min_additional",

            # ratings
            "rating", "rating_1", "rating_2", "rating_3", "rating_4",

            # review content
            "review_headline", "review_body",
            "pros", "cons", "pros_list", "cons_list",

            # media
            "logo", "screenshots",

            # platforms
            "official_website", "steam_url", "app_store_url", "android_url", "playstation_url",

            # SEO
            "seo_title", "seo_description",

            # related blocks
            "faqs", "polls", "best_products",
        ]

    def get_logo(self, obj):
        request = self.context.get("request")
        if obj.logo_file:
            url = obj.logo_file.url
            return request.build_absolute_uri(url) if request else url
        if obj.logo_url:
            return obj.logo_url
        return None

    def get_pros_list(self, obj):
        return [line for line in (obj.pros or "").splitlines() if line.strip()]

    def get_cons_list(self, obj):
        return [line for line in (obj.cons or "").splitlines() if line.strip()]
