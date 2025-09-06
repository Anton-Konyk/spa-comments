from django.urls import path
from .views import CommentCreateView, CommentListView, CommentDetailView

urlpatterns = [
    path(
        "comments/",
        CommentListView.as_view(),
        name="comment-list"
    ),
    path(
        "comments/<int:pk>/",
        CommentDetailView.as_view(),
        name="comment-detail"
    ),
    path(
        "comments/create/",
        CommentCreateView.as_view(),
        name="comment-create"),
]
