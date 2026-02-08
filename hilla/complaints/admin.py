from django.contrib import admin
from .models import Category, Ticket, TicketComment, TicketRating


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 0


class TicketRatingInline(admin.TabularInline):
    model = TicketRating
    extra = 0


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "type",
        "subject",
        "status",
        "priority",
        "category",
        "created_at",
        "is_answered",
        "is_anonymous",
    )
    list_filter = ("type", "status", "priority", "category", "is_answered", "is_anonymous")
    search_fields = ("subject", "message", "name", "email")
    ordering = ("-created_at",)
    inlines = [TicketCommentInline, TicketRatingInline]


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "ticket", "author_name", "created_at")
    search_fields = ("author_name", "text")
    list_filter = ("created_at",)


@admin.register(TicketRating)
class TicketRatingAdmin(admin.ModelAdmin):
    list_display = ("id", "ticket", "score", "rater_name", "created_at")
    list_filter = ("score", "created_at")
    search_fields = ("rater_name", "comment")
