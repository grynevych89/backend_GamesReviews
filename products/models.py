from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django_ckeditor_5.fields import CKEditor5Field
from slugify import slugify
from django.contrib.sites.models import Site
from django.utils.html import format_html

# ────────────────────────────────
# 📚 Supporting Models
# ────────────────────────────────
class Category(models.Model):
    name = models.CharField("Category Name", max_length=100, unique=True, help_text="Назва категорії, напр. Action, RPG")
    def __str__(self): return self.name

class Type(models.Model):
    name = models.CharField("Type Name", max_length=100, unique=True, help_text="Тип продукту: Game, Movie або App")
    def __str__(self): return self.name

class Company(models.Model):
    name = models.CharField("Назва компанії", max_length=255, unique=True)
    def __str__(self): return self.name

class FAQ(models.Model):
    question = models.CharField("Question", max_length=255, help_text="Питання")
    answer = models.TextField("Answer", help_text="Відповідь")
    def __str__(self): return self.question

class Poll(models.Model):
    question = models.CharField("Poll Question", max_length=255, help_text="Питання опитування")
    def __str__(self): return self.question

class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="options")
    text = models.CharField("Option Text", max_length=100, help_text="Варіант відповіді")
    def __str__(self): return f"{self.text} (Poll: {self.poll.question})"

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
    site = models.ForeignKey(Site, on_delete=models.CASCADE, verbose_name="Sites", help_text="На якому сайті буде відображатись")
    title = models.CharField("Product Title", max_length=255, help_text="Назва")
    slug = models.SlugField("Slug", unique=True, help_text="Автоматично генерується зі заголовка")
    steam_id = models.CharField("Steam ID", max_length=50, blank=True, null=True, help_text="Steam ID (для парсингу)")
    is_active = models.BooleanField("Is Active?", default=True, help_text="Якщо вимкнено — гра не показується на сайті")
    type = models.ForeignKey(Type, on_delete=models.SET_NULL, null=True, blank=True, related_name="products", verbose_name="Тип", help_text="Оберіть один тип")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products", verbose_name="Категорія", help_text="Оберіть одну категорію")
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Author", help_text="Автор, який додав гру")
    publishers = models.ManyToManyField(Company, related_name="published_products", blank=True)

    # Description & Metadata
    required_age = models.PositiveIntegerField("Required Age", default=0, help_text="Мінімальний вік для гри")
    release_date = models.DateField("Release Date", blank=True, null=True, help_text="Офіційна дата релізу гри")

    # System Requirements
    min_os = models.CharField("Minimum OS", max_length=100, blank=True)
    min_processor = models.CharField("Minimum Processor", max_length=100, blank=True)
    min_ram = models.CharField("Minimum RAM", max_length=50, blank=True)
    min_graphics = models.CharField("Minimum Graphics Card", max_length=150, blank=True)
    min_storage = models.CharField("Minimum Storage", max_length=50, blank=True)
    min_additional = models.CharField("Minimum Additional Info", max_length=200, blank=True)

    # Ratings
    rating = models.IntegerField("Оценка", choices=[(i, str(i)) for i in range(1, 6)], default=5)
    rating_story = models.DecimalField("Story Rating", max_digits=2, decimal_places=1, validators=[MinValueValidator(0), MaxValueValidator(5)])
    rating_directing = models.DecimalField("Directing Rating", max_digits=2, decimal_places=1, validators=[MinValueValidator(0), MaxValueValidator(5)])
    rating_soundTrack = models.DecimalField("Soundtrack Rating", max_digits=2, decimal_places=1, validators=[MinValueValidator(0), MaxValueValidator(5)])
    rating_specialEffects = models.DecimalField("Special Effects Rating", max_digits=2, decimal_places=1, validators=[MinValueValidator(0), MaxValueValidator(5)])

    # Review Content
    review_headline = models.CharField("Review Title(H1)", max_length=255)
    review_body = CKEditor5Field("Review Body")

    pros = models.TextField("Pros", blank=True)
    cons = models.TextField("Cons", blank=True)

    # Relations
    polls = models.ManyToManyField(Poll, related_name="products", blank=True)
    faqs = models.ManyToManyField(FAQ, related_name="products", blank=True)

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
        verbose_name = "Продукт"
        verbose_name_plural = "1. Продукти"

    def __str__(self): return self.title

    def save(self, *args, **kwargs):
        if not self.pk or (self.pk and self.__class__.objects.filter(pk=self.pk).exclude(title=self.title).exists()):
            self.slug = slugify(self.title)
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


