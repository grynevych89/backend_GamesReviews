from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from ckeditor.fields import RichTextField
from django.utils.text import slugify


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
    title = models.CharField("Game Title", max_length=255, help_text="Назва гри")
    slug = models.SlugField("Slug", unique=True, help_text="Автоматично генерується зі заголовка")
    steam_id = models.CharField("Steam ID", max_length=50, blank=True, null=True, help_text="Steam ID (для парсингу)")
    is_active = models.BooleanField("Is Active?", default=True, help_text="Якщо вимкнено — гра не показується на сайті")

    developer = models.CharField("Developer", max_length=255, blank=True, help_text="Розробник")
    publisher = models.CharField("Publisher", max_length=255, blank=True, help_text="Видавець")

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
    review_body = RichTextField("Review Body", help_text="HTML-огляд: H2-H4, списки, картинки 100% ширини")

    pros = models.TextField("Pros", blank=True, help_text="Переваги — по одному в рядок (натискай Enter після кожного)")
    cons = models.TextField("Cons", blank=True, help_text="Недоліки — по одному в рядок (натискай Enter після кожного)")

    categories = models.ManyToManyField(Category, related_name="games", verbose_name="Categories", help_text="Оберіть одну або кілька категорій")

    polls = models.ManyToManyField("Poll", related_name="games", blank=True, help_text="Оберіть опитування, які пов'язані з цією грою")
    faqs = models.ManyToManyField(FAQ, related_name="games", blank=True,
                                  help_text="Оберіть або створіть питання FAQ для гри")

    created_at = models.DateTimeField(auto_now_add=True)

    def get_logo(self):
        return self.logo_file.url if self.logo_file else self.logo_url

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

class Screenshot(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="screenshots")
    image_file = models.ImageField("Local Screenshot", upload_to="screenshots/", blank=True, null=True)
    image_url = models.URLField("Screenshot URL", blank=True, null=True)

    def get_image(self):
        return self.image_file.url if self.image_file else self.image_url

class Comment(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="comments")
    name = models.CharField("Name", max_length=100, help_text="Ім’я користувача")
    email = models.EmailField("Email", help_text="Email користувача (не публікується)")
    text = models.TextField("Comment Text", help_text="Текст коментаря")
    is_approved = models.BooleanField("Approved", help_text="...", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} on {self.game.title}"
