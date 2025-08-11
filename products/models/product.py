from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from tinymce.models import HTMLField
from slugify import slugify
from django.contrib.sites.models import Site
from django.utils.html import format_html
from django.core.exceptions import ValidationError

from products.constants import PRODUCT_TYPE_CHOICES, RATING_MIN, RATING_MAX, BUTTON_TEXT_BY_TYPE
from .category import Category, Author
from ..utils.slug import unique_slug_for_site


class Product(models.Model):
    TYPE_CHOICES = PRODUCT_TYPE_CHOICES

    site = models.ForeignKey(Site, on_delete=models.CASCADE, verbose_name="Sites")

    # Основные
    title = models.CharField("Product Title", max_length=255, help_text="Назва")
    slug = models.SlugField("Slug", help_text="Автоматично генерується зі заголовка")
    steam_id = models.CharField("Steam ID", max_length=50, blank=True, null=True)
    is_active = models.BooleanField("Is Active?", default=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='game', null=True, blank=True)

    # Связи
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="products", verbose_name="Категорія"
    )
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Author")

    # Компании
    publishers = models.JSONField("Publishers", default=list, blank=True)
    developers = models.JSONField("Developers", default=list, blank=True)

    button_text = models.CharField("Button text", max_length=50, blank=True)

    # Метаданные/релиз
    required_age = models.PositiveIntegerField("Required Age", default=0)
    release_date = models.DateField("Release Date", blank=True, null=True)

    # Только для фильмов
    length = models.PositiveIntegerField("Length (minutes)", blank=True, null=True)
    director = models.CharField("Director", max_length=255, blank=True, null=True)
    actors = models.JSONField("Actors", default=list, blank=True, null=True)
    country = models.CharField("Country", max_length=255, blank=True, null=True)

    # Только для приложений
    version = models.CharField("Version", max_length=50, blank=True, null=True)

    # System Requirements (игры/приложения)
    min_os = models.CharField("Minimum OS", max_length=300, blank=True)
    min_processor = models.CharField("Minimum Processor", max_length=300, blank=True)
    min_ram = models.CharField("Minimum RAM", max_length=300, blank=True)
    min_graphics = models.CharField("Minimum Graphics Card", max_length=300, blank=True)
    min_storage = models.CharField("Minimum Storage", max_length=300, blank=True)
    min_additional = models.CharField("Minimum Additional Info", max_length=300, blank=True)

    # Ratings
    rating = models.IntegerField("Оценка", choices=[(i, str(i)) for i in range(1, 6)], default=5)
    rating_1 = models.DecimalField(
        "Rating 1", max_digits=3, decimal_places=1, default=4.0,
        validators=[MinValueValidator(RATING_MIN), MaxValueValidator(RATING_MAX)]
    )
    rating_2 = models.DecimalField(
        "Rating 2", max_digits=3, decimal_places=1, default=4.0,
        validators=[MinValueValidator(RATING_MIN), MaxValueValidator(RATING_MAX)]
    )
    rating_3 = models.DecimalField(
        "Rating 3", max_digits=3, decimal_places=1, default=4.0,
        validators=[MinValueValidator(RATING_MIN), MaxValueValidator(RATING_MAX)]
    )
    rating_4 = models.DecimalField(
        "Rating 4", max_digits=3, decimal_places=1, default=4.0,
        validators=[MinValueValidator(RATING_MIN), MaxValueValidator(RATING_MAX)]
    )

    # Рекомендации
    best_products = models.ManyToManyField(
        'self', blank=True, symmetrical=False, related_name='recommended_for',
        verbose_name="Лучшие продукты (до 4)",
        help_text="Выберите до 4 продуктов для блока рекомендаций"
    )

    # Обзор
    review_headline = models.CharField("Review Title(H1)", max_length=255)
    review_body = HTMLField("Review Body")
    pros = models.TextField("Pros", blank=True)
    cons = models.TextField("Cons", blank=True)

    # Медиа
    logo_file = models.ImageField("Local Logo", upload_to="logos/", blank=True, null=True)
    logo_url = models.URLField("Logo URL", blank=True, null=True)
    screenshots = models.JSONField(blank=True, default=list, verbose_name="Screenshots URLs")

    # Платформы/ссылки
    steam_url = models.URLField("Steam", blank=True, default="")
    app_store_url = models.URLField("AppStore", blank=True, default="")
    android_url = models.URLField("Android", blank=True, default="")
    playstation_url = models.URLField("PlayStation", blank=True, default="")
    official_website = models.URLField("Website", blank=True, default="")

    # SEO
    seo_title = models.CharField("SEO Title", max_length=255, blank=True)
    seo_description = models.TextField("SEO Description", max_length=300, blank=True)

    # Служебные
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('slug', 'site')
        verbose_name = "Продукт"
        verbose_name_plural = "1. Продукти"

    # ——— Служебные методы ———
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_for_site(Product, self.site, self.title, self.pk)

        self.button_text = BUTTON_TEXT_BY_TYPE.get(self.type, "View Product")

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"https://{self.site.domain.rstrip('/')}/product/{self.slug}"

    def get_logo(self):
        return self.logo_file.url if self.logo_file else self.logo_url

    def logo_preview(self):
        url = self.get_logo()
        return f'<img src="{url}" style="max-height:50px;" />' if url else "—"

    def clean(self):
        if self.pk and self.best_products.count() > 4:
            raise ValidationError("Можно выбрать максимум 4 продукта.")

    def get_best_products(self):
        return self.best_products.all()[:4]

    def developers_str(self):
        return ", ".join(self.developers or [])

    def publishers_str(self):
        return ", ".join(self.publishers or [])

    def __str__(self):
        return self.title
