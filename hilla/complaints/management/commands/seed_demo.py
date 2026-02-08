import random
from django.core.management.base import BaseCommand

from complaints.models import Category, Ticket, TicketRating


class Command(BaseCommand):
    help = "Seed demo tickets and ratings."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=8)

    def handle(self, *args, **options):
        count = options["count"]
        categories = ["Dormitory", "IT", "Study", "Safety", "Cafeteria"]
        subjects = [
            "Broken light in corridor",
            "Water leak in bathroom",
            "Wi‑Fi unstable in classroom",
            "Noise complaint after midnight",
            "Heating not working",
            "Dirty water in dorm",
        ]
        names = ["Temirlan", "Hilla", "Amina", "Sasha", "Omar", "Lina"]

        for name in categories:
            Category.objects.get_or_create(name=name)

        all_categories = list(Category.objects.all())

        for _ in range(count):
            ticket = Ticket.objects.create(
                category=random.choice(all_categories),
                type=random.choice([Ticket.QUESTION, Ticket.COMPLAINT]),
                priority=random.choice([Ticket.LOW, Ticket.MEDIUM, Ticket.HIGH]),
                status=random.choice([Ticket.OPEN, Ticket.IN_PROGRESS, Ticket.CLOSED]),
                name=random.choice(names),
                email="demo@example.com",
                subject=random.choice(subjects),
                message="Demo ticket created for UI preview.",
            )
            for _ in range(random.randint(0, 3)):
                TicketRating.objects.create(
                    ticket=ticket,
                    score=random.randint(3, 5),
                    rater_name=random.choice(names),
                    comment="Thanks, fixed quickly.",
                )

        self.stdout.write(self.style.SUCCESS(f"Seeded {count} tickets."))
