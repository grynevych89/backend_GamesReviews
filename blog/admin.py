from django.contrib import admin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import path
from django.utils import timezone
from django.utils.html import format_html
from django.core.exceptions import PermissionDenied


from blog.models import BlogPost

class BlogCategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

    def _strip_site_param(self, request):
        if "site" in request.GET:
            q = request.GET.copy()
            q.pop("site", None)
            request.GET = q
            request.META["QUERY_STRING"] = q.urlencode()

    def changelist_view(self, request, extra_context=None):
        self._strip_site_param(request)
        extra_context = extra_context or {}
        extra_context["disable_site_switcher"] = True
        return super().changelist_view(request, extra_context=extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        self._strip_site_param(request)
        extra_context = (extra_context or {}) | {"disable_site_switcher": True}
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def add_view(self, request, form_url="", extra_context=None):
        self._strip_site_param(request)
        extra_context = (extra_context or {}) | {"disable_site_switcher": True}
        return super().add_view(request, form_url, extra_context=extra_context)

class BlogPostAdmin(admin.ModelAdmin):
    exclude = ("site",)
    list_display = ("title", "is_active", "published_at", "updated_at", "image_preview")
    list_filter = ("is_active", "published_at", "updated_at", "category", "author")
    search_fields = ("title", "slug", "seo_title", "seo_description")
    save_on_top = True
    change_form_template = "admin/products/product/change_form.html"
    list_editable = ("is_active",)
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        ("Основне", {
            "classes": ("fieldset-horizontal",),
            "fields": (("title", "slug", "category", ),),
        }),
        ("Контент", {
            "classes": ("fieldset-horizontal",),
            "fields": ("author", "content",)}),
        ("Зображення", {
            "classes": ("fieldset-horizontal",),
            "fields": (("main_image", "image_preview"),),
        }),
        ("SEO", {
            "classes": ("fieldset-horizontal",),
            "fields": (("seo_title", "seo_description"),),
        }),
        # ("Система", {
        #     "classes": ("fieldset-horizontal",),
        #     "fields": (("created_at", "updated_at", "published_at", ),),
        # }),
    )
    readonly_fields = ("image_preview", "created_at", "updated_at")

    def image_preview(self, obj):
        if not getattr(obj, "main_image", None):
            return "—"
        return format_html('<img src="{}" style="max-height:80px;border-radius:6px" />', obj.main_image.url)
    image_preview.short_description = "Preview"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<int:pk>/toggle-active/",
                self.admin_site.admin_view(self.toggle_active),
                name="blog_blogpost_toggle_active",
            ),
        ]
        return custom + urls

    def toggle_active(self, request, pk):
        obj = get_object_or_404(BlogPost, pk=pk)
        obj.is_active = not obj.is_active
        obj.save(update_fields=["is_active"])
        return JsonResponse({"success": True, "is_active": obj.is_active})

    def save_model(self, request, obj, form, change):
        site_id = request.GET.get("site") or request.session.get("current_site_id")
        if site_id:
            obj.site_id = int(site_id)
        if not change and obj.is_active and not obj.published_at:
            obj.published_at = timezone.now()
        super().save_model(request, obj, form, change)

    def add_view(self, request, form_url="", extra_context=None):
        site_id = request.GET.get("site") or request.session.get("current_site_id")
        if not site_id:
            # показываем ошибку в админке
            from django.template.response import TemplateResponse
            context = dict(
                self.admin_site.each_context(request),
                title="Добавление блога",
                message="⚠ Сначала выберите сайт",
                opts=self.model._meta,
                app_label=self.model._meta.app_label,
                has_permission=False,
            )
            return TemplateResponse(request, "admin/blogs/add_denied.html", context)
        return super().add_view(request, form_url, extra_context)

    def render_change_form(self, request, context, *args, **kwargs):
        context["toggle_active_url_name"] = f"{self.admin_site.name}:blog_blogpost_toggle_active"
        context["show_rating"] = False
        return super().render_change_form(request, context, *args, **kwargs)

    class Media:
        css = {"all": ("admin/products/css/blog_admin.css",)}
