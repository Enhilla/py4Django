from django.core.management.base import BaseCommand

from complaints.models import Ticket, TicketComment, TicketRating


class Command(BaseCommand):
    help = "Delete all tickets, comments, and ratings."

    def handle(self, *args, **options):
        TicketComment.objects.all().delete()
        TicketRating.objects.all().delete()
        Ticket.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("All tickets, comments, and ratings deleted."))
