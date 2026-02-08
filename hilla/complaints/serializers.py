from rest_framework import serializers
from .models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()

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
            "is_anonymous",
            "subject",
            "message",
            "answer",
            "is_answered",
            "average_rating",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_average_rating(self, obj):
        ratings = obj.ratings.all()
        if not ratings:
            return None
        return round(sum(r.score for r in ratings) / ratings.count(), 2)
