from django.core.management.base import BaseCommand
from faker import Faker
import random
from games.models import Game, Screenshot, FAQ, Poll, PollOption, Comment, Category

fake = Faker()

class Command(BaseCommand):
    help = "Generate fake game(s) with screenshots, FAQ, polls and comments"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=1,
            help="Кількість ігор для генерації (default: 1)"
        )

    def handle(self, *args, **options):
        count = options["count"]

        # Категорії
        categories = list(Category.objects.all())
        if not categories:
            categories = [Category.objects.create(name=n) for n in ["Action", "RPG", "Indie", "Horror", "Strategy"]]

        # Створюємо 5 унікальних опитувань
        poll_questions = [
            "Чи рекомендуєш цю гру?",
            "Наскільки тобі сподобалась графіка?",
            "Чи пройдеш ще раз?",
            "Гра варта своїх грошей?",
            "Твій улюблений режим гри?"
        ]

        polls = []
        for question in poll_questions:
            poll = Poll.objects.create(question=question)
            for opt in ["Так", "Ні", "Можливо", "Ще не грав"]:
                PollOption.objects.create(poll=poll, text=opt)
            polls.append(poll)

        # Створюємо загальні FAQ
        faq_pairs = [
            ("Скільки годин на проходження?", "В середньому 20–30 годин."),
            ("Чи є українська мова?", "Так, підтримується повністю."),
            ("Чи є мультиплеєр?", "Ні, лише синглплеєр."),
            ("Чи є мікротранзакції?", "Так, але тільки косметичні."),
            ("Чи потрібен інтернет для гри?", "Лише для першого запуску.")
        ]

        faqs = []
        for q, a in faq_pairs:
            faqs.append(FAQ.objects.create(question=q, answer=a))

        # Створення ігор
        for i in range(count):
            title = fake.sentence(nb_words=3).rstrip('.')
            game = Game.objects.create(
                title=title,
                steam_id=str(random.randint(100000, 999999)),
                developer=fake.company(),
                publisher=fake.company(),
                logo_url="https://picsum.photos/200",
                rating_manual=round(random.uniform(1, 5), 1),
                rating_external=round(random.uniform(1, 5), 1),
                review_headline=fake.sentence(nb_words=5),
                review_body=fake.paragraph(nb_sentences=8),
                pros="Гарний сюжет\nКрутий звук\nНемає донату",
                cons="Дорогі DLC\nПовільні оновлення\nБаги",
                is_active=True
            )

            game.categories.set(random.sample(categories, k=random.randint(1, 3)))
            game.polls.add(polls[i % len(polls)])
            game.faqs.set(random.sample(faqs, k=random.randint(2, 4)))

            # Screenshots
            for _ in range(3):
                Screenshot.objects.create(
                    game=game,
                    image_url="https://picsum.photos/640/360"
                )

            # Comments
            for _ in range(random.randint(3, 6)):
                Comment.objects.create(
                    game=game,
                    name=fake.first_name(),
                    email=fake.email(),
                    text=fake.paragraph(nb_sentences=2),
                    is_approved=random.choice([True, False])
                )

            self.stdout.write(self.style.SUCCESS(f"[{i+1}/{count}] Created fake game: {title}"))
