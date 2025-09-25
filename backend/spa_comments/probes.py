import os, time
from django.http import JsonResponse, HttpResponseForbidden
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


def storage_probe(request):

    if os.getenv("ENABLE_STORAGE_PROBE", "") != "True":
        return HttpResponseForbidden("probe disabled")

    token = request.headers.get("X-Probe-Token") or request.GET.get("token")
    if not token or token != os.getenv("STORAGE_PROBE_TOKEN"):
        return HttpResponseForbidden("forbidden")

    info = {
        "storage_class": default_storage.__class__.__name__,
        "storage_module": default_storage.__module__,
        "bucket": getattr(default_storage, "bucket_name", None),
        "endpoint": os.getenv("SUPABASE_S3_ENDPOINT"),
        "project_ref": os.getenv("SUPABASE_PROJECT_REF"),
        "has_key": bool(os.getenv("SUPABASE_S3_KEY")),
        "has_secret": bool(os.getenv("SUPABASE_S3_SECRET")),
        "media_url_setting": settings.MEDIA_URL,
    }

    try:
        key = f"uploads/test/probe_{int(time.time())}.txt"
        path = default_storage.save(key, ContentFile(b"probe-ok"))
        info["saved_path"] = path
        info["public_url"] = default_storage.url(path)
        info["exists_after"] = default_storage.exists(path)
    except Exception as e:
        info["error"] = str(e)

    return JsonResponse(info)
