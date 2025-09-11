from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import SpaUserSerializer, RegisterUserSerializer

SpaUser = get_user_model()


class RegisterUserView(generics.CreateAPIView):
    serializer_class = RegisterUserSerializer
    permission_classes = [AllowAny]


class LoginUserView(APIView):
    """Login with username and password (session auth)"""

    permission_classes = ()

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

        login(request, user)
        return Response(SpaUserSerializer(user, context={"request": request}).data)


class LogoutUserView(APIView):
    """Logout current user"""

    def post(self, request):
        logout(request)
        return Response({"detail": "Logged out"}, status=status.HTTP_200_OK)


class CurrentUserView(APIView):
    """Get current logged-in user"""

    def get(self, request):
        if request.user.is_authenticated:
            return Response(SpaUserSerializer(request.user, context={"request": request}).data)
        return Response({"detail": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
