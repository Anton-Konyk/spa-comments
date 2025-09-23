import os
from urllib.parse import quote
from storages.backends.s3boto3 import S3Boto3Storage


class SupabaseMediaStorage(S3Boto3Storage):
    """
    We write to Supabase via the S3-compatible API (boto3),
    and read via the Supabase CDN path:
    https://<project-ref>.supabase.co/storage/v1/object/public/<bucket>/<key>
    """
    bucket_name = os.getenv("SUPABASE_MEDIA_BUCKET", "spa-comments-media")
    default_acl = None
    custom_domain = None  # use our own url()

    def url(self, name, parameters=None, expire=None):
        project_ref = os.getenv("SUPABASE_PROJECT_REF")
        if not project_ref:
            # Fallback: standard URL from S3Boto3Storage (not cached as such)
            return super().url(name, parameters=parameters, expire=expire)
        base = f"https://{project_ref}.supabase.co/storage/v1/object/public/{self.bucket_name}"
        # name may contain spaces/unicode - carefully escape it for URL
        return f"{base}/{quote(name)}"
