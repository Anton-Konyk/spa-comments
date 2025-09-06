from django.contrib import admin

from comments.models import Comment


from django.contrib import admin
from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("user", "short_text", "created_at", "is_reply")
    list_filter = ("created_at",)
    search_fields = ("text", "user__username")
    ordering = ("-created_at",)
    raw_id_fields = ("user", "parent")

    def short_text(self, obj):
        return obj.text[:25].replace("\n", " ")
    short_text.short_description = "Text"

    def is_reply(self, obj):
        return obj.is_reply
    is_reply.boolean = True
    is_reply.short_description = "Reply?"
