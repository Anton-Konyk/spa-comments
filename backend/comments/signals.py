from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction  # <-- to send after commit
from .models import Comment

COMMENTS_GROUP = "comments"


@receiver(post_save, sender=Comment)
def comment_created_signal(sender, instance: Comment, created, **kwargs):
    # Broadcast only on creation
    if not created:
        return

    def _send():
        channel_layer = get_channel_layer()
        if not channel_layer:
            return

        payload = {
            # Flat message expected by frontend
            "action": "comment.created",
            "id": instance.id,
            "parent": instance.parent_id,
            "text": instance.text,
            "file": instance.file.url if instance.file else None,
            "created_at": (
                instance.created_at.isoformat() if instance.created_at
                else None
            ),
            "user": {
                "id": instance.user_id,
                "username": getattr(instance.user, "username", None),
                "email": getattr(instance.user, "email", None),
                "avatar": (
                    instance.user.avatar.url
                    if getattr(instance.user, "avatar", None) else None
                ),
            },
            "replies_count": getattr(instance, "replies_count", 0),
        }

        async_to_sync(channel_layer.group_send)(
            COMMENTS_GROUP,
            {
                # will be delivered to consumer.comment_event
                "type": "comment.event",
                # flat, with "action" inside
                "payload": payload,
            },
        )

    # Make sure we publish only after DB commit in transactions
    transaction.on_commit(_send)
