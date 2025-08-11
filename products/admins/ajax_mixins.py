import json
from django.http import JsonResponse

class AjaxAdminMixin:
    @staticmethod
    def _ok(payload=None, **extra):
        data = {"success": True}
        if payload:
            data.update(payload)
        if extra:
            data.update(extra)
        return JsonResponse(data)

    @staticmethod
    def _err(msg="Invalid request", status=400, **extra):
        data = {"success": False, "error": msg}
        if extra:
            data.update(extra)
        return JsonResponse(data, status=status)

    @staticmethod
    def _is_post(request):
        return request.method == "POST"

    def _json_body(self, request):
        try:
            return json.loads(request.body or "{}")
        except Exception:
            return {}

    def _delete_by(self, model, **filters):
        model.objects.filter(**filters).delete()
        return self._ok()

    def _upload_to_dir(self, request, base_dir, save_func):
        if not self._is_post(request):
            return self._err("Invalid request", status=405)
        upload = request.FILES.get("file")
        if not upload:
            return self._err("No file uploaded", status=400)
        res = save_func(upload, base_dir=base_dir)
        return JsonResponse({"url": res["url"]})
