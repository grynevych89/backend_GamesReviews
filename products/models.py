from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django_ckeditor_5.fields import CKEditor5Field
from slugify import slugify
from django.contrib.sites.models import Site
from django.utils.html import format_html
from django.utils.safestring import mark_safe


class Category(models.Model):
    name = models.CharField("Category Name", max_length=100, unique=True,
                            help_text="Назва категорії, напр. Action, RPG")

    def __str__(self):
        return self.name

class Language(models.Model):
    name = models.CharField("Language", max_length=100, unique=True)

    def __str__(self):
        return self.name

class Type(models.Model):
    name = models.CharField("Type Name", max_length=100, unique=True, help_text="Тип продукту: Game, Movie або App")

    def __str__(self):
        return self.name

class Genre(models.Model):
    name = models.CharField("Genre Name", max_length=100, unique=True)

    def __str__(self):
        return self.name

class StorePlatform(models.Model):
    name = models.CharField("Platform Name", max_length=100, unique=True)
    icon_url = models.URLField("Icon URL", help_text="Посилання на іконку (SVG/PNG)")
    store_url = models.URLField("Store URL", blank=True, null=True,
                                help_text="Посилання на сторінку в магазині (Steam, Epic і т.д.)")

    def __str__(self):
        return self.name

class Company(models.Model):
    name = models.CharField("Назва компанії", max_length=255, unique=True)

class FAQ(models.Model):
    question = models.CharField("Question", max_length=255, help_text="Питання")
    answer = models.TextField("Answer", help_text="Відповідь")

    def __str__(self):
        return self.question

class Poll(models.Model):
    question = models.CharField("Poll Question", max_length=255, help_text="Питання опитування")

    def __str__(self):
        return self.question

class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="options")
    text = models.CharField("Option Text", max_length=100, help_text="Варіант відповіді")

    def __str__(self):
        return f"{self.text} (Poll: {self.poll.question})"

class Product(models.Model):
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        verbose_name="Sites",
        help_text="На якому сайті буде відображатись"
    )

    title = models.CharField("Product Title", max_length=255, help_text="Назва")
    slug = models.SlugField("Slug", unique=True, help_text="Автоматично генерується зі заголовка")
    short_description = models.TextField(
        "Short Description",
        blank=True,
        help_text="Короткий опис (до 300 символів)"
    )
    description = CKEditor5Field("Full Description", blank=True,
                                 help_text="Повний опис гри з HTML-розміткою (парсинг зі Steam)")
    required_age = models.PositiveIntegerField("Required Age", default=0, help_text="Мінімальний вік для гри")
    release_date = models.DateField("Release Date", blank=True, null=True, help_text="Офіційна дата релізу гри")

    genres = models.ManyToManyField(Genre, blank=True, help_text="Жанри з Steam: Indie, Multiplayer, Sports тощо.")
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="Категорія",
        help_text="Оберіть одну категорію"
    )
    type = models.ForeignKey(
        Type,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="Тип",
        help_text="Оберіть один тип"
    )
    store_platforms = models.ManyToManyField(
        StorePlatform,
        related_name="products",
        blank=True,
        help_text="Платформи, де доступний продукт (Steam, Epic, GOG)"
    )

    steam_id = models.CharField("Steam ID", max_length=50, blank=True, null=True, help_text="Steam ID (для парсингу)")
    is_active = models.BooleanField("Is Active?", default=True, help_text="Якщо вимкнено — гра не показується на сайті")

    is_free = models.BooleanField("Free to Play?", default=False, help_text="Чи безкоштовна гра")
    price_initial = models.PositiveIntegerField(
        "Initial Price (in cents)", blank=True, null=True,
        help_text="Початкова ціна (в копійках, напр. 2999 = 29.99)"
    )
    price_final = models.PositiveIntegerField(
        "Final Price (in cents)", blank=True, null=True,
        help_text="Фінальна ціна після знижки (напр. 1499 = 14.99)"
    )
    discount_percent = models.PositiveIntegerField(
        "Знижка (%)", blank=True, null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Знижка в %"
    )
    currency = models.CharField(
        "Валюта", max_length=10, blank=True,
        help_text="Код валюти (USD, EUR тощо)"
    )

    review = models.BooleanField("Review", default=False, help_text="Review")
    website = models.URLField("Офіційний сайт", blank=True, null=True, help_text="Посилання на офіційний сайт гри")

    developers = models.ManyToManyField(Company, related_name="developed_products", blank=True)
    publishers = models.ManyToManyField(Company, related_name="published_products", blank=True)

    languages = models.ManyToManyField(Language, blank=True, help_text="Підтримувані мови")

    author = models.ForeignKey(
        "Author",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Author",
        help_text="Автор, який додав гру"
    )

    # Platforms
    platform_windows = models.BooleanField("Windows", default=False)
    platform_mac = models.BooleanField("macOS", default=False)
    platform_linux = models.BooleanField("Linux", default=False)

    # Minimum requirements
    min_os = models.CharField("Minimum OS", max_length=100, blank=True,
                              help_text="Мінімально підтримувана операційна система")
    min_processor = models.CharField("Minimum Processor", max_length=100, blank=True, help_text="Мінімальний процесор")
    min_ram = models.CharField("Minimum RAM", max_length=50, blank=True,
                               help_text="Мінімальний обсяг оперативної пам’яті")
    min_graphics = models.CharField("Minimum Graphics Card", max_length=150, blank=True,
                                    help_text="Мінімальна відеокарта")
    min_storage = models.CharField("Minimum Storage", max_length=50, blank=True,
                                   help_text="Мінімальний обсяг місця на диску")
    min_additional = models.CharField("Minimum Additional Info", max_length=200, blank=True,
                                      help_text="Інші мінімальні вимоги")

    # Recommended requirements
    rec_os = models.CharField("Recommended OS", max_length=100, blank=True,
                              help_text="Рекомендована операційна система")
    rec_processor = models.CharField("Recommended Processor", max_length=100, blank=True,
                                     help_text="Рекомендований процесор")
    rec_ram = models.CharField("Recommended RAM", max_length=50, blank=True,
                               help_text="Рекомендований обсяг оперативної пам’яті")
    rec_graphics = models.CharField("Recommended Graphics Card", max_length=150, blank=True,
                                    help_text="Рекомендована відеокарта")
    rec_storage = models.CharField("Recommended Storage", max_length=50, blank=True,
                                   help_text="Рекомендований обсяг місця на диску")
    rec_additional = models.CharField("Recommended Additional Info", max_length=200, blank=True,
                                      help_text="Інші рекомендовані вимоги")

    download_button_text = models.CharField(
        "Текст кнопки завантаження",
        max_length=50,
        default="Get App",
        help_text="Наприклад: Get Game, Watch Movie, Get App"
    )
    download_button_url = models.URLField(
        "Посилання кнопки завантаження",
        blank=True,
        help_text="URL, куди веде кнопка (наприклад, Steam, YouTube, сайт гри)"
    )

    logo_file = models.ImageField("Local Logo", upload_to="logos/", blank=True, null=True,
                                  help_text="Завантаження логотипу вручну")
    logo_url = models.URLField("Logo URL", blank=True, null=True, help_text="Посилання на логотип із парсингу")

    rating_manual = models.DecimalField(
        "Manual Rating",
        max_digits=2,
        decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="Оцінка вручну (0–5)"
    )
    rating_external = models.DecimalField(
        "External Rating",
        max_digits=2,
        decimal_places=1,
        blank=True,
        null=True,
        help_text="Оцінка з інших сервісів"
    )

    review_headline = models.CharField("Review Title(H1)", max_length=255, help_text="Заголовок огляду")
    review_body = CKEditor5Field("Review Body", help_text="HTML-огляд: H2-H4, списки, картинки 100% ширини")

    pros = models.TextField("Pros", blank=True, help_text="Переваги — по одному в рядок (натискай Enter після кожного)")
    cons = models.TextField("Cons", blank=True, help_text="Недоліки — по одному в рядок (натискай Enter після кожного)")

    polls = models.ManyToManyField("Poll", related_name="products", blank=True,
                                   help_text="Оберіть опитування, які пов'язані з цією грою")
    faqs = models.ManyToManyField(FAQ, related_name="products", blank=True,
                                  help_text="Оберіть або створіть питання FAQ")

    created_at = models.DateTimeField(auto_now_add=True)

    #SEO
    seo_title = models.CharField(
        "SEO Title",
        max_length=255,
        blank=True,
        help_text="HTML SEO title"
    )

    seo_description = models.TextField(
        "SEO Description",
        max_length=300,
        blank=True,
        help_text="Meta description"
    )

    seo_keywords = models.CharField(
        "SEO Keywords",
        max_length=255,
        blank=True,
        help_text="Ключові слова через кому"
    )

    og_image = models.URLField(
        "OG Image (URL)",
        blank=True,
        null=True,
        help_text="OpenGraph-зображення для Facebook, Telegram, Twitter (URL до .jpg/.png)"
    )

    def get_logo(self):
        return self.logo_file.url if self.logo_file else self.logo_url

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.pk or (
                self.pk and self.__class__.objects.filter(pk=self.pk).exclude(title=self.title).exists()
        ):
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"https://{self.site.domain.rstrip('/')}/product/{self.slug}"

    def logo_preview(self):
        logo_url = self.get_logo()
        if logo_url:
            return format_html('<img src="{}" style="max-height: 50px;" />', logo_url)
        return "—"

    logo_preview.short_description = "Logo"

    def platform_icons(self):
        icons = []
        for platform in self.store_platforms.all():
            url = platform.store_url or "#"
            icon = platform.icon_url
            icons.append(
                f'<a href="{url}" target="_blank" title="{platform.name}">'
                f'<img src="{icon}" height="24" style="margin-right:6px;" />'
                f'</a>'
            )
        return mark_safe("".join(icons))

    platform_icons.short_description = "Store Platform"

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "1. Продукти"


class Screenshot(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="screenshots")
    image_file = models.ImageField("Local Screenshot", upload_to="screenshots/", blank=True, null=True)
    image_url = models.URLField("Screenshot URL", blank=True, null=True)

    def get_image(self):
        return self.image_file.url if self.image_file else (self.image_url or None)


class Comment(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'New'
        APPROVED = 'approved', 'Опубліковано'
        REJECTED = 'rejected', 'Відхилено'

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="comments")
    name = models.CharField("Name", max_length=100, help_text="Ім’я користувача")
    email = models.EmailField("Email", help_text="Email користувача (не публікується)")
    text = models.TextField("Comment Text", help_text="Текст коментаря")
    status = models.CharField(
        "Статус",
        max_length=10,
        choices=Status.choices,
        default=Status.NEW,
        help_text="Статус модерації коментаря"
    )
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


class Author(models.Model):
    name = models.CharField("Ім’я автора", max_length=100, unique=True)

    def __str__(self):
        return self.name

