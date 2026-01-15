from django.contrib import admin
from .models import Category, Ticket, TicketComment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 0


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "subject", "status", "priority", "category", "created_at", "is_answered")
    list_filter = ("type", "status", "priority", "category", "is_answered")
    search_fields = ("subject", "message", "name", "email")
    ordering = ("-created_at",)
    inlines = [TicketCommentInline]


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "ticket", "author_name", "created_at")
    search_fields = ("author_name", "text")
    list_filter = ("created_at",)
