from django.contrib.auth import login, logout
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    GenericAPIView,
    RetrieveAPIView
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import (
    SpaUserSerializer,
    RegisterUserSerializer,
    LoginSerializer,
    EmptySerializer,
)


class RegisterUserView(CreateAPIView):
    """Register a new user"""
    serializer_class = RegisterUserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            SpaUserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )


class LoginUserView(GenericAPIView):
    """Login user view"""
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        return Response(
            SpaUserSerializer(user).data,
            status=status.HTTP_200_OK
        )


class LogoutUserView(GenericAPIView):
    """Logout"""
    permission_classes = [IsAuthenticated]
    serializer_class = EmptySerializer

    @extend_schema(
        summary="Log out current user",
        description="Ends the current session (cookie-based).",
        request=None,
        responses={204: OpenApiResponse(description="Logged out")},
        tags=["auth"],
    )
    def post(self, request):
        logout(request)
        return Response(
            {"detail": "Successfully logged out."},
            status=status.HTTP_200_OK
        )


class CurrentUserView(RetrieveAPIView):
    """Current user (/me)"""
    serializer_class = SpaUserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
