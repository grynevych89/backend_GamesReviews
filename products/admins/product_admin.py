from typing import cast
from urllib.parse import parse_qs

from django.contrib import admin
from django.contrib.sites.models import Site
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from products.forms import ProductForm
from products.models import Product, Category, FAQ, Poll, PollOption
from products.utils.images import save_upload_as_webp
from products.utils.slug import unique_slug
from products.constants import PRODUCT_DUPLICATE_EXCLUDE_FIELDS
from .product_fieldsets import PRODUCT_FIELDSETS
from .product_inlines import FAQInline, PollInline
from .product_admin_urls import build_product_admin_urls
from .ajax_mixins import AjaxAdminMixin


@admin.register(Product)
class ProductAdmin(AjaxAdminMixin, admin.ModelAdmin):
    form = ProductForm

    list_display = (
        "title",
        "is_active",
        "type",
        "category",
        "created_at",
        "platform_links",
        "action_links",
    )
    list_editable = ("is_active",)
    list_display_links = ("title",)
    search_fields = ("title", "author", "publishers_str", "developers_str")
    readonly_fields = ("created_at", "steam_id", "logo_preview")
    save_on_top = True
    view_on_site = True
    change_list_template = "admin/products/change_list_with_generate.html"
    prepopulated_fields = {"slug": ("title",)}
    exclude = ("site", "publishers", "developers")
    inlines = [FAQInline, PollInline]
    fieldsets = PRODUCT_FIELDSETS

    # ───────── helpers ─────────
    @staticmethod
    def _current_site_id(request):
        # 1) Явно передан параметр site → он главнее всего
        if "site" in request.GET:
            sid = request.GET.get("site")
            if sid and str(sid).isdigit():
                request.session["current_site_id"] = int(sid)
                return int(sid)
            # пустое или мусор => "Все сайты"
            request.session.pop("current_site_id", None)
            return None

        # 2) Возврат со страницы объекта: Django кладёт фильтры в _changelist_filters
        if "_changelist_filters" in request.GET:
            parsed = parse_qs(request.GET["_changelist_filters"])
            sid = (parsed.get("site") or [None])[0]
            if sid and str(sid).isdigit():
                request.session["current_site_id"] = int(sid)
                return int(sid)
            # фильтры есть, но site нет/пуст → "Все сайты"
            request.session.pop("current_site_id", None)
            return None

        # 3) Параметр site отсутствует вовсе → трактуем как "Все сайты"
        request.session.pop("current_site_id", None)
        return None

    # ───────── display columns ─────────
    def platform_links(self, obj):
        platforms = [
            (obj.steam_url, "https://upload.wikimedia.org/wikipedia/commons/8/83/Steam_icon_logo.svg", "Steam"),
            (obj.app_store_url, "https://cdn-icons-png.flaticon.com/24/888/888857.png", "App Store"),
            (obj.android_url, "https://cdn-icons-png.flaticon.com/24/888/888841.png", "Android"),
            (obj.playstation_url, "https://upload.wikimedia.org/wikipedia/commons/4/4e/Playstation_logo_colour.svg",
             "PlayStation"),
            (obj.official_website, "https://images.emojiterra.com/google/noto-emoji/unicode-16.0/color/svg/1f310.svg",
             "Official Website"),
        ]
        icons = "".join(
            [
                format_html(
                    '<a href="{0}" target="_blank" class="button" title="{2}" style="padding:2px 5px;"><img src="{1}" style="height:18px;" alt="{2}"/></a>',
                    url, icon, label,
                )
                for url, icon, label in platforms
                if url and url.strip()
            ]
        )
        return format_html('<div style="display:flex;gap:4px;">{}</div>', format_html(icons))

    platform_links.short_description = "Platform Links"

    def action_links(self, obj):
        return format_html(
            '<div style="display:flex;gap:4px;">'
            '<a class="button" target="_blank" href="{}">👁️</a>'
            '<a class="button" href="{}">✏️</a>'
            '<a class="button" href="{}">📄</a>'
            '<a href="#" class="button delete-button" data-url="{}" style="background-color:red;">🗑️</a>'
            "</div>",
            obj.get_absolute_url(),
            reverse(f"{self.admin_site.name}:products_product_change", args=[obj.pk]),
            reverse(f"{self.admin_site.name}:product-duplicate", args=[obj.pk]),
            reverse(f"{self.admin_site.name}:product-delete-confirm", args=[obj.pk]),
        )

    action_links.short_description = "Action Links"

    # ───────── queryset / preview ─────────
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        site_id = self._current_site_id(request)
        return qs.filter(site_id=site_id) if site_id else qs

    @admin.display(description="Logo")
    def logo_preview(self, obj):
        # приоритет: URL > локальный файл
        url = None
        if getattr(obj, "logo_url", None):
            url = obj.logo_url
        elif getattr(obj, "logo_file", None):
            try:
                url = obj.logo_file.url
            except ValueError:
                url = None
        return format_html('<img src="{}" style="max-height: 80px;" />', url) if url else "—"

    # ───────── save hooks ─────────
    def save_model(self, request, obj, form, change):
        obj = cast(Product, obj)
        if not change:
            sid = self._current_site_id(request)
            obj.site = Site.objects.get(id=sid) if sid else Site.objects.first()

        if "is_active_toggle" in request.POST:
            obj.is_active = "is_active" in request.POST

        obj.polls_title = request.POST.get("polls_title", "").strip()

        super().save_model(request, obj, form, change)

        if hasattr(form, "finalize_logo_cleanup"):
            form.finalize_logo_cleanup()

        # ограничение «Лучшие продукты»
        extra = obj.best_products.count() - 4
        if extra > 0:
            to_remove = obj.best_products.order_by("-id")[:extra]
            obj.best_products.remove(*to_remove)

    def add_view(self, request, form_url="", extra_context=None):
        site_id = request.GET.get("site") or request.session.get("current_site_id")
        if not site_id:
            context = dict(
                self.admin_site.each_context(request),
                title="Добавление продукта",
                message="⚠ Сначала выберите сайт",
                opts=self.model._meta,
                app_label=self.model._meta.app_label,
                has_permission=False,
            )
            return TemplateResponse(request, "admin/products/product/add_denied.html", context)
        return super().add_view(request, form_url, extra_context)

    # ───────── AJAX views ─────────
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if request.path.endswith("/autocomplete/") and request.GET.get("field_name") == "best_products":
            product_type = request.GET.get("type")
            object_id = request.GET.get("object_id")
            if object_id:
                try:
                    current_product = Product.objects.get(pk=object_id)
                    product_type = product_type or current_product.type
                    queryset = queryset.exclude(id=current_product.id)
                    queryset = queryset.exclude(id__in=current_product.best_products.values_list("id", flat=True))
                except Product.DoesNotExist:
                    queryset = queryset.none()
            if product_type:
                queryset = queryset.filter(type=product_type)
        return queryset, use_distinct

    def get_products(self, request, product_type):
        current_site_id = self._current_site_id(request) or Site.objects.get_current().id
        data = [{"id": p.id, "title": p.title} for p in
                Product.objects.filter(type=product_type, site_id=current_site_id)]
        return JsonResponse(data, safe=False)

    def best_products_autocomplete(self, request):
        term = request.GET.get("term", "")
        product_type = request.GET.get("type")
        selected_ids = request.GET.getlist("selected[]")
        current_site_id = self._current_site_id(request) or Site.objects.get_current().id

        qs = Product.objects.filter(site_id=current_site_id)
        if product_type:
            qs = qs.filter(type=product_type)
        if selected_ids:
            qs = qs.exclude(id__in=selected_ids)
        if term:
            qs = qs.filter(title__icontains=term)
        return JsonResponse({"results": [{"id": p.id, "text": p.title} for p in qs[:20]]})

    @csrf_exempt
    def upload_screenshot(self, request):
        return self._upload_to_dir(request, base_dir="screenshots", save_func=save_upload_as_webp)

    @method_decorator(csrf_exempt)
    def autosave_screenshots(self, request, pk):
        if not self._is_post(request):
            return self._err("Invalid request", status=400)
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return self._err("Product not found", status=404)
        data = self._json_body(request)
        product.screenshots = data.get("screenshots", [])
        product.save(update_fields=["screenshots"])
        return self._ok(screenshots=product.screenshots)

    @csrf_exempt
    def ajax_delete(self, request, pk):
        if not self._is_post(request):
            return self._err("Invalid request", status=400)
        obj = self.get_object(request, pk)
        obj.delete()
        return self._ok(message="🗑️ Продукт удалён")

    def ajax_delete_faq(self, request, pk):
        if not self._is_post(request):
            return self._err("Invalid request", status=400)
        return self._delete_by(FAQ, pk=pk)

    @csrf_exempt
    def ajax_save_faq(self, request, pk=None):
        if not self._is_post(request):
            return self._err("Invalid request", status=400)
        data = self._json_body(request)
        q, a = data.get("question"), data.get("answer")
        if not q or not a:
            return self._err("Both fields required", status=400)

        if pk:
            FAQ.objects.filter(pk=pk).update(question=q, answer=a)
            return self._ok(id=pk)

        product_id = request.GET.get("product_id")
        if not product_id:
            return self._err("Product ID required", status=400)
        faq = FAQ.objects.create(product_id=product_id, question=q, answer=a)
        return self._ok(id=faq.id)

    @csrf_exempt
    def ajax_save_poll(self, request, pk):
        if not self._is_post(request):
            return self._err("Invalid request")
        data = self._json_body(request)
        question, answers = data.get("question"), data.get("answers", [])
        poll_id = request.GET.get("poll_id")
        if not question or not answers:
            return self._err("Incomplete data")

        product = Product.objects.get(pk=pk)
        if poll_id:
            poll = Poll.objects.filter(pk=poll_id, product=product).first()
            if not poll:
                return self._err("Poll not found")
            poll.question = question
            poll.save()
            PollOption.objects.filter(poll=poll).delete()
        else:
            poll = Poll.objects.create(product=product, question=question)

        for ans in answers:
            PollOption.objects.create(poll=poll, text=ans)

        return self._ok(poll_id=poll.id)

    @csrf_exempt
    def ajax_delete_poll(self, request, pk, poll_id):
        if not self._is_post(request):
            return self._err("Invalid request")
        return self._delete_by(Poll, pk=poll_id, product_id=pk)

    @csrf_exempt
    def upload_image(self, request):  # TinyMCE
        if not self._is_post(request):
            return self._err("Invalid request method", status=405)
        upload = request.FILES.get("file")
        if not upload:
            return self._err("No file uploaded", status=400)
        res = save_upload_as_webp(upload, base_dir="uploads")
        return JsonResponse({"location": request.build_absolute_uri(res["url"])})

    def get_categories(self, request, product_type):
        cats = Category.objects.filter(type=product_type)
        data = [{"id": c.id, "name": c.name, "type": c.type, "type_label": c.get_type_display()} for c in cats]
        return JsonResponse(data, safe=False)

    @csrf_exempt
    def toggle_is_active(self, request, pk):
        if not self._is_post(request):
            return self._err("Invalid request", status=400)
        obj = self.get_object(request, pk)
        data = self._json_body(request)
        obj.is_active = data.get("is_active", False)
        obj.save(update_fields=["is_active"])
        return self._ok()

    def duplicate_product(self, request, product_id):
        original = Product.objects.get(pk=product_id)
        base_title = original.title

        n = 1
        new_title = f"{base_title} (Copy)"
        while Product.objects.filter(title=new_title).exists():
            n += 1
            new_title = f"{base_title} (Copy {n})"

        new_slug = unique_slug(model=Product, title=new_title, site=original.site)

        data = model_to_dict(original, exclude=PRODUCT_DUPLICATE_EXCLUDE_FIELDS)
        new_product = Product(**data)
        new_product.title = new_title
        new_product.slug = new_slug
        new_product.site = original.site
        new_product.category = original.category
        new_product.author = original.author
        new_product.type = original.type

        with transaction.atomic():
            new_product.save()
            new_product.polls.set(original.polls.all())
            new_product.best_products.set(original.best_products.all())
            new_product.publishers = list(original.publishers or [])
            new_product.developers = list(original.developers or [])
            new_product.screenshots = list(original.screenshots or [])
            new_product.save(update_fields=["publishers", "developers", "screenshots"])

        self.message_user(request, f'Продукт скопійовано як “{new_product.title}”.')
        return redirect(reverse(f"{self.admin_site.name}:products_product_change", args=[new_product.id]))

    # ───────── URLs ─────────
    def render_change_form(self, request, context, *args, **kwargs):
        context["toggle_active_url_name"] = f"{self.admin_site.name}:products_product_toggle_active"
        context["show_rating"] = True
        return super().render_change_form(request, context, *args, **kwargs)

    def get_urls(self):
        urls = super().get_urls()
        views = {
            "duplicate_product": self.duplicate_product,
            "toggle_is_active": self.toggle_is_active,
            "ajax_delete": self.ajax_delete,
            "upload_screenshot": self.upload_screenshot,
            "autosave_screenshots": self.autosave_screenshots,
            "get_categories": self.get_categories,
            "ajax_save_faq": self.ajax_save_faq,
            "ajax_delete_faq": self.ajax_delete_faq,
            "ajax_save_poll": self.ajax_save_poll,
            "ajax_delete_poll": self.ajax_delete_poll,
            "get_products": self.get_products,
            "best_products_autocomplete": self.best_products_autocomplete,
            "upload_image": self.upload_image,
        }
        custom = build_product_admin_urls(self.admin_site.admin_view, views)
        return custom + urls

    # ───────── Media ─────────
    class Media:
        css = {
            "all": (
                "https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css",
                "admin/products/css/custom_admin.css",
                "admin/products/css/autocomplete_wide.css",
            )
        }
        js = (
            "https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js",
            "admin/products/js/toggle_is_active.js",
            "admin/products/js/delete_modal.js",
            "admin/products/js/product_type_toggle.js",
            "admin/products/js/category_filter.js",
            "admin/products/js/best_products_limit.js",
        )
