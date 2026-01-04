from django.conf import settings
from django.db import models


class Complaint(models.Model):
    STATUS = [
        ("open", "Open"),
        ("in_progress", "In progress"),
        ("closed", "Closed"),
    ]
    PRIORITY = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]
    CATEGORY = [
        ("it", "IT"),
        ("dorm", "Dormitory"),
        ("study", "Study"),
        ("other", "Other"),
    ]

    # who created (optional if not logged in)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaints",
    )

    title = models.CharField(max_length=200)
    description = models.TextField()

    category = models.CharField(max_length=20, choices=CATEGORY, default="other")
    priority = models.CharField(max_length=20, choices=PRIORITY, default="medium")

    status = models.CharField(max_length=20, choices=STATUS, default="open")
    admin_response = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"#{self.id} {self.title}"
