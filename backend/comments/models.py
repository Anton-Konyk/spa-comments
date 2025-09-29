import os
import uuid

import bleach
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify
from django.db import models
from django.conf import settings
from lxml import html, etree
from PIL import Image, UnidentifiedImageError, ImageOps, ImageSequence
from io import BytesIO
from django.core.files.base import ContentFile

IMAGE_RESIZE_WIDTH = 320
IMAGE_RESIZE_HEIGHT = 240
MAX_TXT_FILE_SIZE = 100 * 1024
MAX_GIF_FRAMES = 200
MAX_TOTAL_GIF_PIXELS = 50_000_000  # width * height * frames

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
        # --- Sanitize + linkify + XHTML ---
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

        # --- Images (resize/compress in-memory) ---
        if self.file:
            name_lower = (self.file.name or "").lower()
            ext = os.path.splitext(name_lower)[1]
            is_jpg = ext in (".jpg", ".jpeg")
            is_png = ext == ".png"
            is_gif = ext == ".gif"

            try:
                try:
                    # ensure pointer at start (e.g., InMemoryUploadedFile)
                    self.file.seek(0)
                except Exception:
                    pass

                if is_gif:
                    with Image.open(self.file) as im:
                        # detect animation
                        n_frames = getattr(im, "n_frames", 1)
                        is_animated = bool(
                            getattr(im, "is_animated", False)
                        ) or n_frames > 1

                        if is_animated:
                            total_pixels = im.width * im.height * n_frames
                            if total_pixels > MAX_TOTAL_GIF_PIXELS:
                                # Fallback: take first frame =>
                                # static GIF, but backend stays healthy
                                im.seek(0)
                                frame = im.convert("RGBA")
                                try:
                                    frame = ImageOps.exif_transpose(frame)
                                except Exception:
                                    pass
                                if (frame.width > IMAGE_RESIZE_WIDTH
                                        or frame.height > IMAGE_RESIZE_HEIGHT):
                                    frame.thumbnail(
                                        (IMAGE_RESIZE_WIDTH,
                                         IMAGE_RESIZE_HEIGHT)
                                    )
                                buf = BytesIO()
                                frame.convert(
                                    "P",
                                    palette=Image.ADAPTIVE,
                                    colors=256).save(
                                    buf,
                                    format="GIF",
                                    optimize=True,
                                    loop=0,
                                    duration=im.info.get("duration", 100)
                                )
                                buf.seek(0)
                                self.file = ContentFile(
                                    buf.read(),
                                    name=self.file.name
                                )
                            else:
                                # Resize and keep animation
                                # (up to MAX_GIF_FRAMES)
                                frames = []
                                durations = []
                                max_frames = min(n_frames, MAX_GIF_FRAMES)
                                for idx, frame in enumerate(
                                        ImageSequence.Iterator(im)
                                ):
                                    if idx >= max_frames:
                                        break
                                    f = frame.convert("RGBA")
                                    try:
                                        f = ImageOps.exif_transpose(f)
                                    except Exception:
                                        pass
                                    if (f.width > IMAGE_RESIZE_WIDTH
                                            or f.height > IMAGE_RESIZE_HEIGHT):
                                        f.thumbnail(
                                            (IMAGE_RESIZE_WIDTH,
                                             IMAGE_RESIZE_HEIGHT)
                                        )
                                    # Convert to palette for GIF
                                    p = f.convert(
                                        "P",
                                        palette=Image.ADAPTIVE,
                                        colors=256
                                    )
                                    frames.append(p)
                                    durations.append(
                                        frame.info.get(
                                            "duration",
                                            im.info.get("duration", 100)
                                        )
                                    )

                                if not frames:
                                    # extreme edge-case:
                                    # fallback to first frame (static)
                                    im.seek(0)
                                    first = im.convert("RGBA")
                                    if (first.width >
                                            IMAGE_RESIZE_WIDTH
                                            or first.height >
                                            IMAGE_RESIZE_HEIGHT):
                                        first.thumbnail(
                                            (IMAGE_RESIZE_WIDTH,
                                             IMAGE_RESIZE_HEIGHT)
                                        )
                                    buf = BytesIO()
                                    first.convert(
                                        "P",
                                        palette=Image.ADAPTIVE,
                                        colors=256).save(
                                        buf,
                                        format="GIF",
                                        optimize=True,
                                        loop=0,
                                        duration=im.info.get(
                                            "duration",
                                            100
                                        )
                                    )
                                    buf.seek(0)
                                    self.file = ContentFile(
                                        buf.read(),
                                        name=self.file.name
                                    )
                                else:
                                    buf = BytesIO()
                                    frames[0].save(
                                        buf,
                                        format="GIF",
                                        save_all=True,
                                        append_images=frames[1:],
                                        loop=im.info.get("loop", 0),
                                        duration=durations,
                                        optimize=True,
                                    )
                                    buf.seek(0)
                                    self.file = ContentFile(
                                        buf.read(),
                                        name=self.file.name
                                    )
                        else:
                            # Static GIF => resize and keep as GIF
                            frame = im.convert("RGBA")
                            try:
                                frame = ImageOps.exif_transpose(frame)
                            except Exception:
                                pass
                            if (frame.width > IMAGE_RESIZE_WIDTH
                                    or frame.height > IMAGE_RESIZE_HEIGHT):
                                frame.thumbnail(
                                    (IMAGE_RESIZE_WIDTH,
                                     IMAGE_RESIZE_HEIGHT)
                                )
                            buf = BytesIO()
                            frame.convert(
                                "P",
                                palette=Image.ADAPTIVE,
                                colors=256).save(
                                buf,
                                format="GIF",
                                optimize=True
                            )
                            buf.seek(0)
                            self.file = ContentFile(
                                buf.read(),
                                name=self.file.name
                            )

                elif is_jpg or is_png:
                    with Image.open(self.file) as img:
                        try:
                            img = ImageOps.exif_transpose(img)
                        except Exception:
                            pass

                        if (img.width > IMAGE_RESIZE_WIDTH
                                or img.height > IMAGE_RESIZE_HEIGHT):
                            img.thumbnail(
                                (IMAGE_RESIZE_WIDTH,
                                 IMAGE_RESIZE_HEIGHT)
                            )

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
                            # PNG keeps alpha, lossless optimize
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
                    Image.DecompressionBombError,
            ):
                # If anything goes wrong with image processing,
                # keep original file as-is.
                pass

        # final write (text already sanitized; file possibly transformed)
        super().save(*args, **kwargs)

    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        preview = self.text[:30].replace("\n", " ")
        return f"{username}: {preview}"

    class Meta:
        verbose_name_plural = "comments"
        indexes = [
            models.Index(fields=["parent", "created_at"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]
        ordering = ["-created_at"]  # LIFO
