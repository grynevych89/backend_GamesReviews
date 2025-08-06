from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django_ckeditor_5.fields import CKEditor5Field
from slugify import slugify
from django.contrib.sites.models import Site
from django.utils.html import format_html
from django.core.exceptions import ValidationError


# ────────────────────────────────
# 📚 Supporting Models
# ────────────────────────────────
PRODUCT_TYPE_CHOICES = [
    ('game', 'Game'),
    ('movie', 'Movie'),
    ('app', 'App'),
]

class Category(models.Model):
    name = models.CharField("Category Name", max_length=100)
    type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default='game', null=True, blank=True)

    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

class FAQ(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=255, verbose_name='Question', blank=True)
    answer = models.CharField(max_length=512, verbose_name='Answer', blank=True)

    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question

class Author(models.Model):
    name = models.CharField("Ім’я автора", max_length=100, unique=True)
    def __str__(self): return self.name

class StorePlatform(models.Model):
    name = models.CharField("Platform Name", max_length=100, unique=True)
    icon_url = models.URLField("Icon URL", blank=True, help_text="Посилання на іконку платформи")
    store_url = models.URLField("Store URL", blank=True, help_text="Посилання на магазин або гру")

    def __str__(self):
        return self.name

# ────────────────────────────────
# 🎮 Product Model
# ────────────────────────────────
class Product(models.Model):
    TYPE_CHOICES = PRODUCT_TYPE_CHOICES
    RATING_MIN = 4
    RATING_MAX = 10

    site = models.ForeignKey(Site, on_delete=models.CASCADE, verbose_name="Sites")
    title = models.CharField("Product Title", max_length=255, help_text="Назва")
    slug = models.SlugField("Slug", help_text="Автоматично генерується зі заголовка")
    steam_id = models.CharField("Steam ID", max_length=50, blank=True, null=True)
    is_active = models.BooleanField("Is Active?", default=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='game', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products", verbose_name="Категорія")
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Author")
    publishers = models.JSONField("Publishers", default=list,blank=True)
    button_text = models.CharField("Button text", max_length=50, blank=True)

    # Description & Metadata
    required_age = models.PositiveIntegerField("Required Age", default=0)
    release_date = models.DateField("Release Date", blank=True, null=True)

    # Только для фильмов
    length = models.PositiveIntegerField(
        "Length (minutes)", blank=True, null=True)
    director = models.CharField("Director", max_length=255, blank=True, null=True)
    actors = models.JSONField("Actors", default=list, blank=True, null=True)
    country = models.CharField("Country", max_length=255, blank=True, null=True)

    # Только для приложений
    version = models.CharField(
        "Version", max_length=50, blank=True, null=True)

    # System Requirements / Только для приложений и игр
    min_os = models.CharField("Minimum OS", max_length=300, blank=True)
    min_processor = models.CharField("Minimum Processor", max_length=300, blank=True)
    min_ram = models.CharField("Minimum RAM", max_length=300, blank=True)
    min_graphics = models.CharField("Minimum Graphics Card", max_length=300, blank=True)
    min_storage = models.CharField("Minimum Storage", max_length=300, blank=True)
    min_additional = models.CharField("Minimum Additional Info", max_length=300, blank=True)

    # Ratings
    rating = models.IntegerField("Оценка", choices=[(i, str(i)) for i in range(1, 6)], default=5)
    rating_1 = models.DecimalField(
        "Rating 1",
        max_digits=3,
        decimal_places=1,
        default=4.0,
        validators=[MinValueValidator(RATING_MIN), MaxValueValidator(RATING_MAX)]
    )
    rating_2 = models.DecimalField(
        "Rating 2",
        max_digits=3,
        decimal_places=1,
        default=4.0,
        validators=[MinValueValidator(RATING_MIN), MaxValueValidator(RATING_MAX)]
    )
    rating_3 = models.DecimalField(
        "Rating 3",
        max_digits=3,
        decimal_places=1,
        default=4.0,
        validators=[MinValueValidator(RATING_MIN), MaxValueValidator(RATING_MAX)]
    )
    rating_4 = models.DecimalField(
        "Rating 4",
        max_digits=3,
        decimal_places=1,
        default=4.0,
        validators=[MinValueValidator(RATING_MIN), MaxValueValidator(RATING_MAX)]
    )

    best_products = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='recommended_for',
        verbose_name="Лучшие продукты (до 4)",
        help_text="Выберите до 4 продуктов для блока рекомендаций"
    )

    # Review Content
    review_headline = models.CharField("Review Title(H1)", max_length=255)
    review_body = CKEditor5Field("Review Body")

    pros = models.TextField("Pros", blank=True)
    cons = models.TextField("Cons", blank=True)

    # Media
    logo_file = models.ImageField("Local Logo", upload_to="logos/", blank=True, null=True)
    logo_url = models.URLField("Logo URL", blank=True, null=True)
    screenshots = models.JSONField(
        blank=True,
        default=list,
        verbose_name="Screenshots URLs",
    )

    # Platforms
    steam_url = models.URLField("Steam", blank=True, default="")
    app_store_url = models.URLField("AppStore", blank=True, default="")
    android_url = models.URLField("Android", blank=True, default="")
    playstation_url = models.URLField("PlayStation", blank=True, default="")
    official_website = models.URLField("Website", blank=True, default="")

    # SEO
    seo_title = models.CharField("SEO Title", max_length=255, blank=True)
    seo_description = models.TextField("SEO Description", max_length=300, blank=True)

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('slug', 'site')
        verbose_name = "Продукт"
        verbose_name_plural = "1. Продукти"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug_candidate = base_slug
            counter = 1

            # Проверяем уникальность в пределах одного сайта
            while Product.objects.filter(site=self.site, slug=slug_candidate).exclude(pk=self.pk).exists():
                counter += 1
                slug_candidate = f"{base_slug}-{counter}"

            self.slug = slug_candidate

        self.button_text = {
            'game': "Get Game",
            'movie': "Watch Now",
            'app': "Get App"
        }.get(self.type, "View Product")

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"https://{self.site.domain.rstrip('/')}/product/{self.slug}"

    def get_logo(self):
        return self.logo_file.url if self.logo_file else self.logo_url

    def logo_preview(self):
        logo_url = self.get_logo()
        if logo_url:
            return format_html('<img src="{}" style="max-height: 50px;" />', logo_url)
        return "—"
    logo_preview.short_description = "Logo"

    def clean(self):
        if self.pk and self.best_products.count() > 4:
            raise ValidationError("Можно выбрать максимум 4 продукта.")

    def get_best_products(self):
        return self.best_products.all()[:4]

    @property
    def publishers_str(self):
        return ", ".join(self.publishers or [])
    publishers_str.fget.short_description = "Publishers"

    def __str__(self):
        return self.title

class Poll(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='polls')
    question = models.CharField("Вопрос", max_length=255)

    def __str__(self):
        return self.question

class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="options")
    text = models.CharField("Вариант ответа", max_length=255)

    def __str__(self):
        return self.text

# ────────────────────────────────
# 💬 Comments
# ────────────────────────────────
class Comment(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'New'
        APPROVED = 'approved', 'Опубліковано'
        REJECTED = 'rejected', 'Відхилено'

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="comments")
    name = models.CharField("Name", max_length=100, help_text="Ім’я користувача")
    email = models.EmailField("Email", help_text="Email користувача (не публікується)")
    text = models.TextField("Comment Text", help_text="Текст коментаря")
    status = models.CharField("Статус", max_length=10, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = [models.Case(
            models.When(status='new', then=0),
            models.When(status='approved', then=1),
            models.When(status='rejected', then=2),
            output_field=models.IntegerField()
        )]
        verbose_name = "Коментар"
        verbose_name_plural = "2. Коментарі"

    def __str__(self):
        return f"{self.name} on {self.product.title}"
