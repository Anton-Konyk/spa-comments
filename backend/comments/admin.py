from django.contrib import admin
from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "short_text",
        "created_at",
        "is_reply",
        "parent_preview",
        "file"
    )
    list_filter = ("created_at",)
    search_fields = (
        "text",
        "user__username",
        "parent__text",
        "parent__user__username"
    )
    ordering = ("-created_at",)
    raw_id_fields = ("user", "parent")

    def short_text(self, obj):
        return obj.text[:25].replace("\n", " ")
    short_text.short_description = "Text"

    def is_reply(self, obj):
        return obj.is_reply
    is_reply.boolean = True
    is_reply.short_description = "Reply?"

    def parent_preview(self, obj):
        if obj.parent:
            parent_text = obj.parent.text[:25].replace("\n", " ")
            return f"{obj.parent.user.username}: {parent_text}"
        return "-"
    parent_preview.short_description = "In reply to"
