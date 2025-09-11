import requests
import bleach
from rest_framework import serializers

from spa_comments import settings
from users.serializers import SpaUserSerializer
from .models import Comment
from drf_spectacular.utils import extend_schema_field


ALLOWED_TAGS = ["a", "code", "i", "strong"]
ALLOWED_ATTRS = {"a": ["href", "title"]}
ALLOWED_PROTOCOLS = ["http", "https"]


class CommentListSerializer(serializers.ModelSerializer):
    """Serializer for a list of comments with nested replies"""
    user = SpaUserSerializer(read_only=True)
    is_reply = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField(method_name="get_replies_count")

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

    @extend_schema_field(bool)
    def get_is_reply(self, obj) -> bool:
        return obj.is_reply

    @extend_schema_field(int)
    def get_replies_count(self, obj) -> int:
        return obj.replies.count()


class CommentCreateSerializer(serializers.ModelSerializer):
    recaptcha_token = serializers.CharField(write_only=True)

    class Meta:
        model = Comment
        fields = [
            "text",
            "file",
            "home_page",
            "parent",
            "recaptcha_token",
        ]

    def validate(self, data):
        token = data.get("recaptcha_token")
        secret = settings.RECAPTCHA_SECRET_KEY

        response = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={"secret": secret, "response": token},
        )
        result = response.json()

        if not result.get("success"):
            raise serializers.ValidationError({"recaptcha": "reCAPTCHA verification failed"})

        return data

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

    def validate_text(self, value: str) -> str:
        """
        User text cleaning:
        - leave only safe tags (<a>, <code>, <i>, <strong>);
        - allow only href and title for <a>;
        - filter link protocols (http/https);
        - remove prohibited tags, comments and potential XSS.
        """
        cleaned = bleach.clean(
            text=value,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRS,
            protocols=ALLOWED_PROTOCOLS,
            strip=True,  # cut forbidden tags
            strip_comments=True,  # remove html comments
        )

        return cleaned

    def create(self, validated_data):
        validated_data.pop("recaptcha_token", None)

        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["user"] = request.user

        return super().create(validated_data)


class CommentDetailSerializer(serializers.ModelSerializer):
    user = SpaUserSerializer(read_only=True)
    is_reply = serializers.SerializerMethodField()
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

    @extend_schema_field(bool)
    def get_is_reply(self, obj) -> bool:
        return obj.is_reply

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_replies(self, obj):
        qs = obj.get_replies()
        return CommentDetailSerializer(qs, many=True, context=self.context).data
