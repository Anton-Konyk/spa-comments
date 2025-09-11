from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
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
