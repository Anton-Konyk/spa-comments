import os
import uuid

import bleach
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify
from django.db import models
from django.conf import settings
from lxml import html, etree
from PIL import Image, UnidentifiedImageError, ImageOps
from io import BytesIO
from django.core.files.base import ContentFile


IMAGE_RESIZE_WIDTH = 320
IMAGE_RESIZE_HEIGHT = 240
MAX_TXT_FILE_SIZE = 100 * 1024

ALLOWED_TAGS = ["a", "code", "i", "strong"]
ALLOWED_ATTRS = {"a": ["href", "title"]}


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


def to_valid_xhtml_fragment(cleaned: str) -> str:
    """
    Converts a cleaned HTML fragment into valid XHTML with closed tags.
    """
    wrapped = f"<div>{cleaned}</div>"

    try:
        node = html.fromstring(wrapped)
    except etree.ParserError as e:
        raise ValidationError(f"Invalid HTML markup: {e}")

    xhtml = html.tostring(node, method="xml", encoding="unicode")

    if xhtml.startswith("<div>") and xhtml.endswith("</div>"):
        xhtml = xhtml[len("<div>"):-len("</div>")]

    return xhtml.strip()


class Comment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments"
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

    def clean(self):
        if self.file and self.file.name.lower().endswith(".txt"):
            # Try to read the beginning of the file as UTF-8 text
            try:
                self.file.seek(0)
                sample = self.file.read(1024)  # read first 1KB
                if isinstance(sample, bytes):
                    sample.decode("utf-8")
            except UnicodeDecodeError:
                raise ValidationError("TXT files must be valid UTF-8 text.")
            finally:
                self.file.seek(0)  # reset pointer

    def save(self, *args, **kwargs):
        self.text = bleach.clean(
            self.text,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRS,
            protocols=["http", "https"],
            strip=True,
            strip_comments=True,
        )
        self.text = bleach.linkify(
            self.text,
            callbacks=[
                bleach.callbacks.nofollow,
                bleach.callbacks.target_blank
            ],
        )
        self.text = to_valid_xhtml_fragment(self.text)

        if self.file:
            name_lower = (self.file.name or "").lower()
            ext = os.path.splitext(name_lower)[1]
            is_jpg = ext in (".jpg", ".jpeg")
            is_png = ext == ".png"

            if is_jpg or is_png:
                try:
                    try:
                        self.file.seek(0)
                    except Exception:
                        pass

                    with Image.open(self.file) as img:
                        try:
                            img = ImageOps.exif_transpose(img)
                        except Exception:
                            pass

                        if (img.width > IMAGE_RESIZE_WIDTH
                                or img.height > IMAGE_RESIZE_HEIGHT):
                            img.thumbnail((
                                IMAGE_RESIZE_WIDTH,
                                IMAGE_RESIZE_HEIGHT
                            ))

                        buf = BytesIO()
                        if is_jpg:

                            if img.mode in ("RGBA", "P"):
                                img = img.convert("RGB")
                            img.save(
                                buf,
                                format="JPEG",
                                quality=85,
                                optimize=True
                            )
                        else:
                            # PNG
                            img.save(buf, format="PNG", optimize=True)

                        buf.seek(0)

                        self.file = ContentFile(
                            buf.read(),
                            name=self.file.name
                        )

                except (
                        UnidentifiedImageError,
                        OSError,
                        ValueError,
                        Image.DecompressionBombError
                ):
                    pass

        super().save(*args, **kwargs)

    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        preview = self.text[:30].replace("\n", " ")
        return f"{username}: {preview}"

    class Meta:
        verbose_name_plural = "comments"
        ordering = ["-created_at"]  # LIFO
