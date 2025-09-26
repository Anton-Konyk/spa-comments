import os
from urllib.parse import quote, urlparse
from storages.backends.s3boto3 import S3Boto3Storage


class SupabaseMediaStorage(S3Boto3Storage):
    """
    Writes via Supabase S3-compatible endpoint;
    reads via Supabase public CDN URL.
    """
    bucket_name = os.getenv("SUPABASE_MEDIA_BUCKET", "spa-comments-media")
    default_acl = None
    custom_domain = None  # we build URL ourselves

    def _get_project_ref(self) -> str | None:
        # 1) explicit env
        ref = os.getenv("SUPABASE_PROJECT_REF")
        if ref:
            return ref

        # 2) derive from S3 endpoint, e.g.
        # https://kigtjheeeawcilwzqfkw.supabase.co/storage/v1/s3
        endpoint = os.getenv("SUPABASE_S3_ENDPOINT", "")
        host = urlparse(endpoint).hostname or ""
        if host.endswith(".supabase.co"):
            return host.split(".")[0]

        return None

    def url(self, name, parameters=None, expire=None):
        project_ref = self._get_project_ref()
        if not project_ref:
            # Fallback to S3Boto3Storage logic if ref is still unknown
            return super().url(name, parameters=parameters, expire=expire)

        base = (f"https://{project_ref}."
                f"supabase.co/storage/v1/object/public/{self.bucket_name}")

        key = quote(str(name).lstrip("/"), safe="/")
        return f"{base}/{key}"
