from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Comment
from .serializers import (
    CommentListSerializer,
)


class CommentListView(generics.ListAPIView):
    """
    GET /api/comments/
    Returns a list of root comments with the number of replies.
    """
    queryset = Comment.objects.filter(parent=None) \
        .select_related("user") \
        .prefetch_related("replies")
    serializer_class = CommentListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
