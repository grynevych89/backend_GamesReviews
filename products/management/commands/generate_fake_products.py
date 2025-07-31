from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from products.models import (
    Product, Category, Poll, FAQ, Comment,
    Author
)
from faker import Faker
from slugify import slugify
import random

MOVIE_CATEGORIES = [
    "Action", "Adventure", "Animation", "Anime", "Comedy", "Crime",
    "Documentary", "Drama", "Family", "Fantasy", "Sci-Fi", "Game Show",
    "Horror", "Lifestyle", "Music", "Reality TV", "Sport", "Western", "Thriller"
]

GAME_CATEGORIES = [
    "Action", "Adventure", "RPG", "Strategy", "Simulation",
    "Sports", "Racing", "Puzzle", "Shooter", "Survival",
    "Open World", "Indie", "MMO", "Horror", "Platformer",
    "Fighting", "Casual", "VR", "Co-op", "Rogue-like"
]

APP_CATEGORIES = [
    "Productivity", "Education", "Finance", "Health & Fitness", "Entertainment",
    "Photo & Video", "Music", "Lifestyle", "News", "Social Networking",
    "Travel", "Navigation", "Shopping", "Sports", "Food & Drink",
    "Business", "Utilities", "Books", "Reference", "Weather"
]

class Command(BaseCommand):
    help = "Generate fake products with related data"

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=1, help='Number of products to create')

    def handle(self, *args, **options):
        fake = Faker()
        count = options['count']

        # ────────────────
        # Ensure Categories
        # ────────────────
        def ensure_categories(cat_list, type_name):
            for name in cat_list:
                Category.objects.get_or_create(name=name, type=type_name)

        ensure_categories(MOVIE_CATEGORIES, "movie")
        ensure_categories(GAME_CATEGORIES, "game")
        ensure_categories(APP_CATEGORIES, "app")

        # ────────────────
        # Ensure other models
        # ────────────────
        if not FAQ.objects.exists():
            for _ in range(5):
                FAQ.objects.create(question=fake.sentence(), answer=fake.paragraph())

        if not Poll.objects.exists():
            for _ in range(3):
                Poll.objects.create(question=fake.sentence())

        if not Author.objects.exists():
            for _ in range(3):
                Author.objects.create(name=fake.name())

        # ────────────────
        # Подготавливаем данные
        # ────────────────
        sites = list(Site.objects.all())
        categories_by_type = {
            "movie": list(Category.objects.filter(type="movie")),
            "game": list(Category.objects.filter(type="game")),
            "app": list(Category.objects.filter(type="app")),
        }
        authors = list(Author.objects.all())
        faqs = list(FAQ.objects.all())
        polls = list(Poll.objects.all())

        type_choices = [choice[0] for choice in Product.TYPE_CHOICES]

        def generate_unique_slug(title):
            base = slugify(title)
            slug = base
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base}-{counter}"
                counter += 1
            return slug

        # ────────────────
        # Генерация продуктов
        # ────────────────
        for _ in range(count):
            product_type = random.choice(type_choices)
            title = fake.catch_phrase()
            slug = generate_unique_slug(title)
            category = random.choice(categories_by_type[product_type])

            # --- Movie / App specific fields ---
            if product_type == "movie":
                length = random.randint(80, 180)
                director = fake.name()
                actors = [fake.name() for _ in range(random.randint(2, 5))]
                country = fake.country()
                version = None
            elif product_type == "app":
                length = None
                director = None
                actors = []
                country = ""
                version = fake.numerify(text="%#.%#.%#")
            else:  # game
                length = None
                director = None
                actors = []
                country = ""
                version = None

            # --- Ratings ---
            rating = random.randint(1, 5)

            product = Product.objects.create(
                site=random.choice(sites),
                title=title,
                slug=slug,
                steam_id=str(random.randint(100000, 999999)),
                is_active=True,
                type=product_type,
                author=random.choice(authors),
                category=category,
                required_age=random.choice([0, 12, 16, 18]),
                release_date=fake.date_between(start_date='-5y', end_date='today'),

                # Movie / App specific
                length=length,
                director=director,
                actors=actors,
                country=country,
                version=version,

                # System Requirements
                min_os="Windows 10",
                min_processor="Intel i5",
                min_ram="8 GB",
                min_graphics="GTX 1050",
                min_storage="20 GB",
                min_additional="64-bit OS required",

                # Ratings
                rating=rating,
                rating_1=round(random.uniform(4, 10), 1),
                rating_2=round(random.uniform(4, 10), 1),
                rating_3=round(random.uniform(4, 10), 1),
                rating_4=round(random.uniform(4, 10), 1),

                # Review
                review_headline=fake.sentence(),
                review_body=fake.paragraph(nb_sentences=10),
                pros="\n".join(fake.words(3)),
                cons="\n".join(fake.words(3)),
                seo_title=fake.sentence(nb_words=6),
                seo_description=fake.text(160),

                # Media
                logo_url=f"https://picsum.photos/200?random={random.randint(1, 1000)}",
                screenshots=[
                    f"https://picsum.photos/800/450?random={random.randint(1, 10000)}"
                    for _ in range(random.randint(5, 10))
                ],

                # Publishers JSON
                publishers=[fake.company() for _ in range(random.randint(1, 3))],

                # Platforms
                steam_url=f"https://store.steampowered.com/app/{random.randint(100000, 999999)}/",
                app_store_url=f"https://apps.apple.com/app/id{random.randint(1000000000, 9999999999)}",
                android_url=f"https://play.google.com/store/apps/details?id=com.example{random.randint(1000, 9999)}",
                playstation_url=f"https://www.playstation.com/en-us/games/{slug}/",
                official_website=f"https://example.com/{slug}",
            )

            # M2M
            product.polls.set(random.sample(polls, min(len(polls), 2)))
            product.faqs.set(random.sample(faqs, min(len(faqs), 2)))

            # Comments
            for _ in range(random.randint(2, 5)):
                Comment.objects.create(
                    product=product,
                    name=fake.first_name(),
                    email=fake.email(),
                    text=fake.sentence(),
                    status=random.choice([
                        Comment.Status.NEW,
                        Comment.Status.APPROVED,
                        Comment.Status.REJECTED
                    ])
                )

        self.stdout.write(self.style.SUCCESS(f"✔ Створено {count} фейкових продуктів"))
