import os
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify


def avatars_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    extension = extension.lower()
    filename = f"{slugify(instance.username)}-{uuid.uuid4()}{extension}"

    return os.path.join("uploads/avatars/", filename)


class SpaUser(AbstractUser):
    avatar = models.ImageField(
        upload_to=avatars_file_path,
        blank=True,
        null=True,
        verbose_name="Avatar"
    )

    def __str__(self):
        return self.username or "Anonymous"
