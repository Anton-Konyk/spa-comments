from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import never_cache

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .serializers import AppConfigSerializer


@method_decorator(ensure_csrf_cookie, name="get")
@method_decorator(never_cache, name="get")
class AppConfigView(APIView):
    """Returns frontend settings like BACKEND_URL, PAGE_SIZE, ok, csrfToken"""

    permission_classes = [AllowAny]

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
            "ok": True,
            "csrfToken": get_token(request),
        }
        serializer = AppConfigSerializer(data)
        resp = Response(serializer.data)
        resp["Vary"] = "Origin, Cookie"
        return resp
