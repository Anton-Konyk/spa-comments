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


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = [
            "text",
            "file",
            "home_page",
            "parent",
        ]

    def validate_file(self, value):
        """
        Additional file check.
        Prohibit uploading empty .txt files
        """
        if value and value.name.lower().endswith(".txt") and value.size == 0:
            raise serializers.ValidationError(
                "You cannot upload an empty TXT file."
            )
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["user"] = request.user
        return super().create(validated_data)


class CommentDetailSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    is_reply = serializers.ReadOnlyField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "text",
            "file",
            "home_page",
            "created_at",
            "parent",
            "is_reply",
            "replies",
        ]

    def get_replies(self, obj):
        qs = obj.get_replies()
        return CommentListSerializer(qs, many=True).data
