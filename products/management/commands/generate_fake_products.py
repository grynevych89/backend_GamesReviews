from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from products.models import (
    Product, Category, Screenshot, Poll, PollOption,
    FAQ, Comment, Author, StorePlatform,
    Genre, Language, Company, Type
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

        # Ensure related data exists
        def ensure(model, count, creator):
            if not model.objects.exists():
                for _ in range(count):
                    creator()

        ensure(Category, 5, lambda: Category.objects.create(name=fake.word()))
        ensure(FAQ, 5, lambda: FAQ.objects.create(question=fake.sentence(), answer=fake.paragraph()))
        ensure(Poll, 3, lambda: Poll.objects.create(question=fake.sentence()))
        ensure(Author, 3, lambda: Author.objects.create(name=fake.name()))
        ensure(StorePlatform, 4, lambda: StorePlatform.objects.create(
            name=fake.company(),
            icon_url=fake.image_url(),
            store_url=fake.url()
        ))
        ensure(Genre, 5, lambda: Genre.objects.create(name=fake.word()))
        ensure(Language, 5, lambda: Language.objects.create(name=fake.language_name()))
        ensure(Company, 5, lambda: Company.objects.create(name=fake.company()))
        ensure(Type, 3, lambda: Type.objects.create(name=fake.word()))

        sites = list(Site.objects.all())
        categories = list(Category.objects.all())
        authors = list(Author.objects.all())
        faqs = list(FAQ.objects.all())
        polls = list(Poll.objects.all())
        platforms = list(StorePlatform.objects.all())
        genres = list(Genre.objects.all())
        languages = list(Language.objects.all())
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
                short_description=fake.text(200),
                description=fake.paragraph(5),
                review_headline=fake.sentence(),
                review_body=fake.paragraph(10),
                pros="\n".join(fake.words(3)),
                cons="\n".join(fake.words(3)),
                required_age=random.choice([0, 12, 16, 18]),
                release_date=fake.date_between(start_date='-5y', end_date='today'),
                platform_windows=True,
                platform_mac=random.choice([True, False]),
                platform_linux=random.choice([True, False]),
                min_os="Windows 7",
                min_processor="Intel Core 2 Duo",
                min_ram="4 GB",
                min_graphics="NVIDIA GTX 470",
                min_storage="9 GB",
                min_additional="64-bit OS required",
                rec_os="Windows 10",
                rec_processor="Intel i5",
                rec_ram="8 GB",
                rec_graphics="NVIDIA GTX 970",
                rec_storage="20 GB",
                rec_additional="SSD recommended",
                rating_manual=round(random.uniform(1, 5), 1),
                rating_external=round(random.uniform(1, 5), 1),
                is_free=random.choice([True, False]),
                price_initial=random.randint(1000, 5000),
                price_final=random.randint(500, 4000),
                discount_percent=random.choice([0, 10, 25, 50]),
                currency="USD",
                website=fake.url(),
                seo_title=fake.sentence(nb_words=6),
                seo_description=fake.text(160),
                seo_keywords=", ".join(fake.words(5)),
                og_image=fake.image_url(),
                download_button_text="Get Game",
                download_button_url=fake.url(),
                logo_url=f"https://picsum.photos/200?random={random.randint(1, 1000)}"
            )

            product.polls.set(random.sample(polls, min(len(polls), 2)))
            product.faqs.set(random.sample(faqs, min(len(faqs), 2)))
            product.store_platforms.set(random.sample(platforms, min(len(platforms), 3)))
            product.genres.set(random.sample(genres, min(len(genres), 3)))
            product.languages.set(random.sample(languages, min(len(languages), 3)))
            product.developers.set(random.sample(companies, min(len(companies), 2)))
            product.publishers.set(random.sample(companies, min(len(companies), 2)))

            for _ in range(random.randint(2, 4)):
                Screenshot.objects.create(
                    product=product,
                    image_url=f"https://picsum.photos/600/400?random={random.randint(1, 1000)}"
                )

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
