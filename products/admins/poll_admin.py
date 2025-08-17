from django.contrib import admin
from django.utils.html import format_html
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.urls import path
from django.core.files.storage import default_storage

from products.forms import PollForm
from products.models import Poll, PollOption
from products.utils.images import save_upload_as_webp


class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 4
    verbose_name = "Вариант"
    verbose_name_plural = "Варианты ответа"


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    form = PollForm
    list_display = ("title", "question", "product", "preview")
    readonly_fields = ("preview",)
    inlines = [PollOptionInline]

    def preview(self, obj):
        if obj and getattr(obj, "image", None):
            return format_html(
                '<div style="width:180px;height:100px;border:1px solid #2a2a2a;background:#111;">'
                '<img src="{}" style="width:100%;height:100%;object-fit:contain;display:block;" />'
                '</div>',
                obj.image.url
            )
        return "—"

    preview.short_description = "Preview"

    # ⬇️ добавляем маршрут для AJAX-загрузки картинки
    def get_urls(self):
        urls = super().get_urls()
        my = [
            path(
                "<int:poll_id>/upload-image/",
                self.admin_site.admin_view(self.upload_image),
                name="products_poll_upload_image",
            ),
        ]
        return my + urls

    def upload_image(self, request, poll_id: int, *args, **kwargs):
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])

        poll = get_object_or_404(Poll, pk=poll_id)

        file = request.FILES.get("image")
        if not file:
            return JsonResponse({"success": False, "error": "no file"}, status=400)

        try:
            # сохраняем как webp в папку polls/
            res = save_upload_as_webp(file, base_dir="polls")
            name = res.get("name") or res.get("relative") or res.get("path")
            if not name:
                return JsonResponse({"success": False, "error": "convert failed"}, status=500)

            old = getattr(getattr(poll, "image", None), "name", None)
            poll.image.name = name
            poll.save(update_fields=["image"])

            if old and old != name:
                try:
                    default_storage.delete(old)
                except Exception:
                    pass

            return JsonResponse({"success": True, "url": getattr(poll.image, "url", "")})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
