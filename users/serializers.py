from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from django.core.exceptions import ValidationError

from .models import SpaUser


class SpaUserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = SpaUser
        fields = ["id", "username", "email", "avatar"]

    @extend_schema_field(str)
    def get_avatar(self, obj) -> str | None:
        request = self.context.get("request")
        if obj.avatar and hasattr(obj.avatar, "url"):
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username_or_email = data.get("username")
        password = data.get("password")

        user = authenticate(username=username_or_email, password=password)
        if not user:
            try:
                user_obj = SpaUser.objects.get(email=username_or_email.lower())
                user = authenticate(username=user_obj.username, password=password)
            except SpaUser.DoesNotExist:
                pass

        if not user:
            raise serializers.ValidationError(
                {"detail": "Invalid username/email or password."}
            )

        data["user"] = user
        return data
