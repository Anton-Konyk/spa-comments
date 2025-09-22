import requests
from django.contrib.auth.password_validation import validate_password
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework.validators import UniqueValidator

from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class SpaUserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
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
                user_obj = User.objects.get(email=username_or_email.lower())
                user = authenticate(
                    username=user_obj.username,
                    password=password
                )
            except User.DoesNotExist:
                pass

        if not user:
            raise serializers.ValidationError(
                {"detail": "Invalid username/email or password."}
            )

        data["user"] = user
        return data


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )
    recaptcha_token = serializers.CharField(write_only=True)
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "avatar",
            "recaptcha_token"
        ]
        extra_kwargs = {
            "password": {"write_only": True},
            "username": {"required": True},
            "email": {"required": True},
        }

    def validate_recaptcha_token(self, value):
        secret = settings.RECAPTCHA_SECRET_KEY
        try:
            response = requests.post(
                settings.RECAPTCHA_VERIFY_URL,
                data={"secret": secret, "response": value},
                timeout=5,
            )
            result = response.json()
        except Exception:
            raise serializers.ValidationError(
                "Unable to verify reCAPTCHA. Try again later."
            )

        if not result.get("success"):
            raise serializers.ValidationError("reCAPTCHA verification failed")
        return value

    def create(self, validated_data):
        validated_data.pop("recaptcha_token", None)
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"].lower(),
            password=validated_data["password"],
            avatar=validated_data.get("avatar"),
        )
        return user

    def to_representation(self, instance):
        return SpaUserSerializer(instance, context=self.context).data


class EmptySerializer(serializers.Serializer):
    pass
