from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django_ckeditor_5.fields import CKEditor5Field
from slugify import slugify
from django.contrib.sites.models import Site


class Category(models.Model):
    name = models.CharField("Category Name", max_length=100, unique=True, help_text="Назва категорії, напр. Action, RPG")

    def __str__(self):
        return self.name

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

class Game(models.Model):
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        verbose_name="Sites",
        help_text="На якому сайті буде відображатись ця гра"
    )
    title = models.CharField("Game Title", max_length=255, help_text="Назва гри")
    slug = models.SlugField("Slug", unique=True, help_text="Автоматично генерується зі заголовка")
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="games",
        verbose_name="Категорія",
        help_text="Оберіть одну категорію для гри"
    )
    steam_id = models.CharField("Steam ID", max_length=50, blank=True, null=True, help_text="Steam ID (для парсингу)")
    is_active = models.BooleanField("Is Active?", default=True, help_text="Якщо вимкнено — гра не показується на сайті")

    developer = models.CharField("Developer", max_length=255, blank=True, help_text="Розробник")
    publisher = models.CharField("Publisher", max_length=255, blank=True, help_text="Видавець")
    author = models.ForeignKey(
        "Author",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Автор",
        help_text="Автор, який додав гру"
    )

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

    logo_file = models.ImageField("Local Logo", upload_to="logos/", blank=True, null=True, help_text="Завантаження логотипу вручну")
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

    review_headline = models.CharField("Review Headline (H1)", max_length=255, help_text="Заголовок огляду")
    review_body = CKEditor5Field("Review Body", help_text="HTML-огляд: H2-H4, списки, картинки 100% ширини")

    pros = models.TextField("Pros", blank=True, help_text="Переваги — по одному в рядок (натискай Enter після кожного)")
    cons = models.TextField("Cons", blank=True, help_text="Недоліки — по одному в рядок (натискай Enter після кожного)")


    polls = models.ManyToManyField("Poll", related_name="games", blank=True, help_text="Оберіть опитування, які пов'язані з цією грою")
    faqs = models.ManyToManyField(FAQ, related_name="games", blank=True,
                                  help_text="Оберіть або створіть питання FAQ для гри")

    created_at = models.DateTimeField(auto_now_add=True)



    def get_logo(self):
        return self.logo_file.url if self.logo_file else self.logo_url

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.pk or Game.objects.get(pk=self.pk).title != self.title:
            self.slug = slugify(self.title)  # 👈 будет "vpravva"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"https://{self.site.domain.rstrip('/')}/game/{self.slug}"

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"

class Screenshot(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="screenshots")
    image_file = models.ImageField("Local Screenshot", upload_to="screenshots/", blank=True, null=True)
    image_url = models.URLField("Screenshot URL", blank=True, null=True)

    def get_image(self):
        return self.image_file.url if self.image_file else self.image_url

class Comment(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'New'
        APPROVED = 'approved', 'Опубліковано'
        REJECTED = 'rejected', 'Відхилено'

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="comments")
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

    def __str__(self):
        return f"{self.name} on {self.game.title}"

class Author(models.Model):
    name = models.CharField("Ім’я автора", max_length=100, unique=True)

    def __str__(self):
        return self.name
