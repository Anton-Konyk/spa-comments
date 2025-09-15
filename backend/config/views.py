from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .serializers import AppConfigSerializer


class AppConfigView(APIView):
    """Returns frontend settings like BACKEND_URL and PAGE_SIZE"""

    @extend_schema(
        summary="Retrieve frontend configuration",
        description="Returns frontend settings "
                    "like BACKEND_URL and PAGE_SIZE",
        parameters=[
            OpenApiParameter(
                name='format',
                description='Response format (default: json)',
                required=False,
                type=str,
                default='json'
            ),
            OpenApiParameter(
                name='lang',
                description='Interface language (default: en)',
                required=False,
                type=str,
                default='en'
            ),
        ],
        responses=AppConfigSerializer
    )
    def get(self, request):
        data = {
            "BACKEND_URL": getattr(
                settings,
                "FRONTEND_BACKEND_URL",
                "http://localhost:8000"),
            "PAGE_SIZE": getattr(
                settings,
                "PAGE_SIZE",
                10),
        }
        serializer = AppConfigSerializer(data)
        return Response(serializer.data)
