import os
from urllib.parse import quote
from storages.backends.s3boto3 import S3Boto3Storage


class SupabaseMediaStorage(S3Boto3Storage):
    """
    Write via Supabase S3-compatible API (boto3),
    read via Supabase CDN:
    https://<project-ref>.supabase.co/storage/v1/object/public/<bucket>/<key>
    """
    bucket_name = os.getenv("SUPABASE_MEDIA_BUCKET", "spa-comments-media")
    default_acl = None
    custom_domain = None  # use our own url()

    def url(self, name, parameters=None, expire=None):
        project_ref = os.getenv("SUPABASE_PROJECT_REF")
        if not project_ref:
            return super().url(name, parameters=parameters, expire=expire)
        base = f"https://{project_ref}.supabase.co/storage/v1/object/public/{self.bucket_name}"
        # preserve slashes in object key
        key = quote(str(name).lstrip("/"), safe="/")
        return f"{base}/{key}"
