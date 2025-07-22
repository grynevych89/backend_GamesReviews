from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from games.models import (
    Game, Category, Screenshot, Poll, PollOption, FAQ, Comment, Author
)
from faker import Faker
from slugify import slugify
import random

class Command(BaseCommand):
    help = "Generate fake games with related data"

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=1, help='Number of games to create')

    def handle(self, *args, **options):
        fake = Faker()
        count = options['count']

        # Create initial data if needed
        if not Category.objects.exists():
            for _ in range(5):
                Category.objects.create(name=fake.word())

        if not FAQ.objects.exists():
            for _ in range(5):
                FAQ.objects.create(
                    question=fake.sentence(nb_words=5),
                    answer=fake.paragraph(nb_sentences=3)
                )

        if not Poll.objects.exists():
            for _ in range(3):
                poll = Poll.objects.create(question=fake.sentence(nb_words=6))
                for _ in range(4):
                    PollOption.objects.create(poll=poll, text=fake.word())

        if not Author.objects.exists():
            for _ in range(3):
                Author.objects.create(name=fake.name())

        categories = list(Category.objects.all())
        faqs = list(FAQ.objects.all())
        polls = list(Poll.objects.all())
        authors = list(Author.objects.all())
        sites = list(Site.objects.all())

        def generate_unique_slug(title):
            base_slug = slugify(title)
            slug = base_slug
            counter = 1
            while Game.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            return slug

        for _ in range(count):
            title = fake.sentence(nb_words=3).rstrip('.')
            slug = generate_unique_slug(title)
            site = random.choice(sites)

            game = Game.objects.create(
                site=site,
                title=title,
                slug=slug,
                steam_id=str(random.randint(100000, 999999)),
                is_active=True,
                developer=fake.company(),
                publisher=fake.company(),
                author=random.choice(authors),
                category=random.choice(categories),
                logo_url=f"https://picsum.photos/200?random={random.randint(1, 1000)}",
                rating_manual=round(random.uniform(1, 5), 1),
                rating_external=round(random.uniform(1, 5), 1),
                review_headline=fake.sentence(),
                review_body=fake.paragraph(nb_sentences=10),
                pros="\n".join([fake.word() for _ in range(3)]),
                cons="\n".join([fake.word() for _ in range(3)]),

                # Minimum requirements
                min_os="Windows 7",
                min_processor="Intel Core 2 Duo 2.5GHz",
                min_ram="4 GB",
                min_graphics="NVIDIA GTX 470 / AMD HD 6870",
                min_storage="9 GB",
                min_additional="64-bit OS recommended",

                # Recommended requirements
                rec_os="Windows 10",
                rec_processor="Intel Core i5-4570 3.20GHz",
                rec_ram="8 GB",
                rec_graphics="NVIDIA GTX 970 / AMD R9 390",
                rec_storage="9 GB",
                rec_additional="64-bit OS recommended",
            )

            game.faqs.set(random.sample(faqs, k=min(len(faqs), 2)))
            game.polls.set(random.sample(polls, k=min(len(polls), 1)))

            for _ in range(random.randint(2, 4)):
                Screenshot.objects.create(
                    game=game,
                    image_url=f"https://picsum.photos/600/400?random={random.randint(1, 1000)}"
                )

            for _ in range(random.randint(2, 5)):
                Comment.objects.create(
                    game=game,
                    name=fake.first_name(),
                    email=fake.email(),
                    text=fake.sentence(),
                    status=random.choice([
                        Comment.Status.NEW,
                        Comment.Status.APPROVED,
                        Comment.Status.REJECTED
                    ])
                )

        self.stdout.write(self.style.SUCCESS(f"✔ Створено {count} фейкових ігор"))
