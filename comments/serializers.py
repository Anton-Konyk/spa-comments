from rest_framework import serializers
from .models import Comment
from users.models import SpaUser


class CommentListSerializer(serializers.ModelSerializer):
    """Serializer for a list of comments with nested replies"""
    user = serializers.StringRelatedField(read_only=True)
    is_reply = serializers.ReadOnlyField()
    replies_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "text",
            "created_at",
            "is_reply",
            "replies_count",
        ]

    def get_replies_count(self, obj):
        return obj.replies.count()
