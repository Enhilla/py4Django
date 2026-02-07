from django.contrib import admin
from django.db.models import Avg
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
        "avg_rating_display",
        "created_at",
        "is_answered",
        "is_anonymous",
    )
    list_filter = ("type", "status", "priority", "category", "is_answered", "is_anonymous")
    search_fields = ("subject", "message", "name", "email")
    ordering = ("-created_at",)
    list_display_links = ("id", "subject")
    list_editable = ("status", "priority", "is_answered")
    actions = ("mark_open", "mark_in_progress", "mark_closed", "mark_answered", "mark_unanswered")
    inlines = [TicketCommentInline, TicketRatingInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(avg_rating=Avg("ratings__score"))

    @admin.display(description="Avg rating", ordering="avg_rating")
    def avg_rating_display(self, obj):
        if obj.avg_rating is None:
            return "-"
        return f"{obj.avg_rating:.1f}"

    @admin.action(description="Set status: Open")
    def mark_open(self, request, queryset):
        queryset.update(status=Ticket.OPEN)

    @admin.action(description="Set status: In progress")
    def mark_in_progress(self, request, queryset):
        queryset.update(status=Ticket.IN_PROGRESS)

    @admin.action(description="Set status: Closed")
    def mark_closed(self, request, queryset):
        queryset.update(status=Ticket.CLOSED)

    @admin.action(description="Mark as answered")
    def mark_answered(self, request, queryset):
        queryset.update(is_answered=True)

    @admin.action(description="Mark as unanswered")
    def mark_unanswered(self, request, queryset):
        queryset.update(is_answered=False)


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
