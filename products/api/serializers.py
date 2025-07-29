from rest_framework import serializers
from products.models import Product, Comment, FAQ, Poll, PollOption


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer']


class PollOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollOption
        fields = ['id', 'text']


class PollSerializer(serializers.ModelSerializer):
    options = PollOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Poll
        fields = ['id', 'question', 'options']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'review_headline', 'get_logo', 'is_active', 'review']


class ProductDetailSerializer(serializers.ModelSerializer):
    faqs = FAQSerializer(many=True, read_only=True)
    polls = PollSerializer(many=True, read_only=True)
    pros = serializers.SerializerMethodField()
    cons = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'description', 'review_headline', 'review_body',
            'rating_manual', 'rating_external',
            'developer', 'publisher',
            'platform_windows', 'platform_mac', 'platform_linux',
            'min_os', 'min_processor', 'min_ram', 'min_graphics', 'min_storage', 'min_additional',
            'rec_os', 'rec_processor', 'rec_ram', 'rec_graphics', 'rec_storage', 'rec_additional',
            'download_button_text',
            'screenshots', 'faqs', 'polls',
            'pros', 'cons', 'logo'
        ]

    def get_logo(self, obj):
        return obj.get_logo()

    def get_pros(self, obj):
        return obj.pros.strip().splitlines()

    def get_cons(self, obj):
        return obj.cons.strip().splitlines()


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'name', 'email', 'text', 'status', 'created_at']
        read_only_fields = ['status', 'created_at']
