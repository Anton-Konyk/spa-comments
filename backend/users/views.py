from django.contrib.auth import login, logout
from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import SpaUserSerializer, RegisterUserSerializer, LoginSerializer


class RegisterUserView(CreateAPIView):
    """Register a new user"""
    serializer_class = RegisterUserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(SpaUserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginUserView(GenericAPIView):
    """Login user view"""
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        return Response(SpaUserSerializer(user).data, status=status.HTTP_200_OK)


class LogoutUserView(GenericAPIView):
    """Logout"""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        logout(request)
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)


class CurrentUserView(RetrieveAPIView):
    """Current user (/me)"""
    serializer_class = SpaUserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
