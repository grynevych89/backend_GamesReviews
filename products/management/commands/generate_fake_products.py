from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from products.models import (
    Product, Category, Poll, FAQ, Comment,
    Author, Company, Type
)
from faker import Faker
from slugify import slugify
import random


class Command(BaseCommand):
    help = "Generate fake products with related data"

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=1, help='Number of products to create')

    def handle(self, *args, **options):
        fake = Faker()
        count = options['count']

        def ensure(model, n, creator):
            if not model.objects.exists():
                for _ in range(n):
                    creator()

        ensure(Category, 5, lambda: Category.objects.create(name=fake.word()))
        ensure(FAQ, 5, lambda: FAQ.objects.create(question=fake.sentence(), answer=fake.paragraph()))
        ensure(Poll, 3, lambda: Poll.objects.create(question=fake.sentence()))
        ensure(Author, 3, lambda: Author.objects.create(name=fake.name()))
        ensure(Company, 5, lambda: Company.objects.create(name=fake.company()))
        ensure(Type, 3, lambda: Type.objects.create(name=fake.word()))

        sites = list(Site.objects.all())
        categories = list(Category.objects.all())
        authors = list(Author.objects.all())
        faqs = list(FAQ.objects.all())
        polls = list(Poll.objects.all())
        companies = list(Company.objects.all())
        types = list(Type.objects.all())

        def generate_unique_slug(title):
            base = slugify(title)
            slug = base
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base}-{counter}"
                counter += 1
            return slug

        for _ in range(count):
            title = fake.catch_phrase()
            slug = generate_unique_slug(title)

            product = Product.objects.create(
                site=random.choice(sites),
                title=title,
                slug=slug,
                steam_id=str(random.randint(100000, 999999)),
                is_active=True,
                type=random.choice(types),
                author=random.choice(authors),
                category=random.choice(categories),
                required_age=random.choice([0, 12, 16, 18]),
                release_date=fake.date_between(start_date='-5y', end_date='today'),
                min_os="Windows 10",
                min_processor="Intel i5",
                min_ram="8 GB",
                min_graphics="GTX 1050",
                min_storage="20 GB",
                min_additional="64-bit OS required",
                rating=random.randint(1, 5),
                rating_story=round(random.uniform(1, 5), 1),
                rating_directing=round(random.uniform(1, 5), 1),
                rating_soundTrack=round(random.uniform(1, 5), 1),
                rating_specialEffects=round(random.uniform(1, 5), 1),
                review_headline=fake.sentence(),
                review_body=fake.paragraph(nb_sentences=10),
                pros="\n".join(fake.words(3)),
                cons="\n".join(fake.words(3)),
                seo_title=fake.sentence(nb_words=6),
                seo_description=fake.text(160),
                logo_url=f"https://picsum.photos/200?random={random.randint(1, 1000)}",

                # platform links
                steam_url=f"https://store.steampowered.com/app/{random.randint(100000, 999999)}/",
                app_store_url=f"https://apps.apple.com/app/id{random.randint(1000000000, 9999999999)}",
                android_url=f"https://play.google.com/store/apps/details?id=com.example{random.randint(1000, 9999)}",
                playstation_url=f"https://www.playstation.com/en-us/games/{slug}/",
                official_website=f"https://example.com/{slug}",

                # ✅ Генерируем список скриншотов от 5 до 10
                screenshots=[
                    f"https://picsum.photos/800/450?random={random.randint(1, 10000)}"
                    for _ in range(random.randint(5, 10))
                ]
            )

            product.polls.set(random.sample(polls, min(len(polls), 2)))
            product.faqs.set(random.sample(faqs, min(len(faqs), 2)))
            product.publishers.set(random.sample(companies, min(len(companies), 2)))

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
