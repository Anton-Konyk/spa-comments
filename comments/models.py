import os
import uuid

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify
from django.db import models
from PIL import Image

from users.models import SpaUser


IMAGE_RESIZE_WIDTH = 320
IMAGE_RESIZE_HEIGHT = 240
MAX_TXT_FILE_SIZE = 100 * 1024


def validate_file_size(value):
    """Checking the file size (maximum 100 KB for txt"""
    if value.size > MAX_TXT_FILE_SIZE and value.name.lower().endswith(".txt"):
        raise ValidationError(
            "The size of the TXT file should not exceed 100 KB."
        )


def comments_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    extension = extension.lower()
    filename = f"{slugify(instance.user.username)}-{uuid.uuid4()}{extension}"

    return os.path.join("uploads/comments/", filename)


class Comment(models.Model):
    user = models.ForeignKey(
        SpaUser, on_delete=models.CASCADE, related_name="comments"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    home_page = models.URLField(blank=True, null=True)
    text = models.TextField()
    file = models.FileField(
        upload_to=comments_file_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg", "jpeg", "png", "gif", "txt"]
            ),
            validate_file_size,
        ],
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )

    @property
    def is_reply(self):
        return self.parent is not None

    def get_replies(self):
        return self.replies.all().order_by("created_at")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.file and self.file.name.lower().endswith(
            (".jpg", ".jpeg", ".png", ".gif")
        ):
            file_path = self.file.path
            with Image.open(file_path) as img:
                if img.width > IMAGE_RESIZE_WIDTH or img.height > IMAGE_RESIZE_HEIGHT:
                    img.thumbnail((IMAGE_RESIZE_WIDTH, IMAGE_RESIZE_HEIGHT))
                    img = img.convert("RGB")
                    img.save(file_path)

    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        return f"{username}: {self.text[:25].replace('\n', ' ')}"

    class Meta:
        verbose_name_plural = "comments"
        ordering = ["-created_at"]  # LIFO
