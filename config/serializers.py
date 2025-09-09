from rest_framework import serializers


class AppConfigSerializer(serializers.Serializer):
    BACKEND_URL = serializers.CharField()
    PAGE_SIZE = serializers.IntegerField()
