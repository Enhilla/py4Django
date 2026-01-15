from rest_framework import serializers
from .models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = [
            "id",
            "user",
            "category",
            "type",
            "priority",
            "status",
            "name",
            "email",
            "subject",
            "message",
            "answer",
            "is_answered",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
