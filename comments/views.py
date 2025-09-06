from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Comment
from .serializers import (
    CommentListSerializer,
    CommentDetailSerializer,
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


class CommentDetailView(generics.RetrieveAPIView):
    """
    GET /api/comments/<id>/
    Returns one comment with embedded replies (replies).
    """
    queryset = Comment.objects.all() \
        .select_related("user") \
        .prefetch_related("replies__user", "replies__replies")
    serializer_class = CommentDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
