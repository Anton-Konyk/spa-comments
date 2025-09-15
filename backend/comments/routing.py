from django.urls import re_path
from .consumers import CommentsConsumer

# Single public stream: ws://<host>/ws/comments/
websocket_urlpatterns = [
    re_path(r"^ws/comments/$", CommentsConsumer.as_asgi()),
]
