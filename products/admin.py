# products/admin.py
import json
from urllib.parse import urlparse, parse_qs

from django import forms
from django.contrib import admin, messages
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.db import models, transaction
from django.forms.models import BaseInlineFormSet, model_to_dict
from django.http import JsonResponse, QueryDict
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.text import slugify
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .forms import ProductForm
from .models import (
    Product, Comment, Category, Author,
    FAQ, Poll, PollOption
)
from .custom_admin import SiteAwareAdminSite
from .services import steam_parser
from .utils.images import save_upload_as_webp


# ────────────────────────────────
# 🧭 Site / Admin Site
# ────────────────────────────────

class CustomSiteAdmin(admin.ModelAdmin):
    list_display = ('domain', 'name')
    search_fields = ('domain', 'name')


custom_admin_site = SiteAwareAdminSite(name="custom_admin")
custom_admin_site.register(Site, CustomSiteAdmin)

custom_admin_site.site_header = "Reviews Admin"
custom_admin_site.site_title = "Reviews Admin"
custom_admin_site.index_title = "Панель Управління"


# ────────────────────────────────
# 🔧 Utilities
# ────────────────────────────────

@csrf_exempt
def upload_image(request):
    """
    TinyMCE: загрузка изображений с конвертацией в WEBP и именем без хэшей.
    Возвращает абсолютный URL в поле 'location' (ожидает TinyMCE).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    upload = request.FILES.get('file')
    if not upload:
        return JsonResponse({'error': 'No file uploaded'}, status=400)

    try:
        res = save_upload_as_webp(upload, base_dir='uploads')
        return JsonResponse({'location': request.build_absolute_uri(res["url"])})
    except Exception as e:
        return JsonResponse({'error': f'WEBP convert/save failed: {e}'}, status=400)


def generate_unique_slug_for_model(model, title: str) -> str:
    base_slug = slugify(title)
    slug = base_slug or "item"
    counter = 1
    while model.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


def extract_site_from_referer(request, param="site"):
    referer = request.META.get("HTTP_REFERER", "")
    parsed = urlparse(referer)
    return parse_qs(parsed.query).get(param, [None])[0]


def redirect_back_to_filtered_list(request, view_name, param="site"):
    site = request.GET.get(param) or extract_site_from_referer(request, param)
    if site and str(site).isdigit():
        return redirect(f"{reverse(view_name)}?{param}={site}")
    return None


# ────────────────────────────────
# 📄 Inlines
# ────────────────────────────────

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ("name", "email", "text", "status", "created_at")
    readonly_fields = ("created_at",)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "type")
    list_filter = ("type",)
    search_fields = ("name",)
    ordering = ("name",)

    def changelist_view(self, request, extra_context=None):
        # убираем паразитные фильтры site из списка категорий
        request.GET = request.GET.copy()
        request.GET.pop('site', None)
        request.GET.pop('_changelist_filters', None)
        return super().changelist_view(request, extra_context=extra_context)


class FAQInline(admin.TabularInline):
    model = FAQ
    extra = 1
    min_num = 0
    can_delete = False
    show_change_link = False
    fields = ('question', 'answer', 'actions')
    readonly_fields = ('actions',)

    def actions(self, obj):
        save_btn = (
            '<button type="button" class="button faq-save-button" '
            'style="background-color:green;color:white;margin-right:5px;">💾</button>'
        )
        delete_btn = ''
        if obj.pk:
            url = reverse(f'{self.admin_site.name}:faq-inline-delete', args=[obj.pk])
            delete_btn = (
                f'<button type="button" class="button faq-delete-button" '
                f'data-url="{url}" style="background-color:red;color:white;">🗑️</button>'
            )
        return format_html(save_btn + delete_btn)

    class Media:
        js = ('admin/products/js/delete_modal.js',)


class PollInlineFormSet(BaseInlineFormSet):
    def clean(self):
        # пассивная валидация — всё делаем через AJAX
        super().clean()


class PollInline(admin.TabularInline):
    model = Poll
    formset = PollInlineFormSet
    extra = 0
    min_num = 0
    can_delete = False
    show_change_link = False
    fields = ('question',)
    verbose_name = "📊 Опрос"
    verbose_name_plural = "📊 Опросы продукта"
    template = "admin/products/product/tabular.html"

    # нужно, чтобы input отображался и в empty_form
    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'class': 'vTextField'})},
    }

    class Media:
        js = ('admin/products/js/poll_inline.js',)


class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 4
    verbose_name = "Вариант"
    verbose_name_plural = "Варианты ответа"


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('question', 'product')
    inlines = [PollOptionInline]


# ───────────────────────────────
# 🕹️ Product Admin
# ───────────────────────────────

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductForm
    list_display = (
        "title", "is_active", "type", "category", "created_at",
        "platform_links", "action_links",
    )
    list_editable = ("is_active",)
    list_display_links = ("title",)
    search_fields = ("title", "author", "publishers_str", "developers_str")
    readonly_fields = ("created_at", "steam_id", "logo_preview")
    save_on_top = True
    view_on_site = True
    change_list_template = "admin/products/change_list_with_generate.html"
    prepopulated_fields = {"slug": ("title",)}
    exclude = ('site', 'publishers', 'developers')
    inlines = [FAQInline, PollInline]

    # ────────── Разметка формы (секции) ──────────
    fieldsets = [
        (None, {
            "fields": (
                ("title", "slug", "type", "category", "required_age",
                 "publishers_str", "developers_str", "release_date"),
                ("best_products", "length", "version", "director", "country", "actors_str"),
            ),
            "classes": ("fieldset-horizontal", "movie-info-fieldset", "block-separator"),
        }),
        (None, {
            "fields": (
                ("min_os", "min_processor", "min_ram"),
                ("min_graphics", "min_storage", "min_additional"),
            ),
            "classes": ("fieldset-horizontal", "requirements-fieldset", "block-separator"),
        }),
        (None, {
            "fields": (
                ("official_website", "android_url", "app_store_url", "steam_url", "playstation_url"),
            ),
            "classes": ("fieldset-horizontal", "block-separator"),
        }),
        (None, {"fields": (("review_headline", "author"), "review_body"), "classes": ("block-separator",)}),
        (None, {"fields": (("pros", "cons"),), "classes": ("fieldset-horizontal", "block-separator")}),
        (None, {"fields": (("rating_1", "rating_2", "rating_3", "rating_4"),),
                "classes": ("fieldset-horizontal", "block-separator")}),
        (None, {"fields": (("seo_title", "seo_description"),), "classes": ("block-separator",)}),
        (None, {"fields": (("logo_preview", "logo_file", "logo_url"),),
                "classes": ("fieldset-horizontal", "block-separator")}),
        (None, {"fields": (("screenshots",),)}),
        (None, {"fields": ("rating",), "classes": ("hidden-fieldset", "block-separator")}),
    ]

    # ────────── Быстрые ссылки ──────────

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
        icons_html = "".join([
            format_html(
                '<a href="{0}" target="_blank" class="button" title="{2}" style="padding:2px 5px;">'
                '<img src="{1}" style="height:18px;" alt="{2}"/></a>',
                url, icon, label
            )
            for url, icon, label in platforms if url and url.strip()
        ])
        return format_html('<div style="display:flex;gap:4px;">{}</div>', format_html(icons_html))

    platform_links.short_description = "Platform Links"

    def action_links(self, obj):
        view_url = obj.get_absolute_url()
        change_url = reverse("admin:products_product_change", args=[obj.pk])
        duplicate_url = reverse("admin:product-duplicate", args=[obj.pk])
        delete_url = reverse("admin:product-delete-confirm", args=[obj.pk])

        return format_html(
            '<div style="display:flex;gap:4px;">'
            '<a class="button" target="_blank" href="{}">👁️</a>'
            '<a class="button" href="{}">✏️</a>'
            '<a class="button" href="{}">📄</a>'
            '<a href="#" class="button delete-button" data-url="{}" style="background-color:red;">🗑️</a>'
            '</div>',
            view_url, change_url, duplicate_url, delete_url
        )

    action_links.short_description = "Action Links"

    # ────────── Queryset / фильтры ──────────

    def get_queryset(self, request):
        site_id = request.GET.get("site")
        qs = super().get_queryset(request)
        if site_id and site_id.isdigit():
            return qs.filter(site_id=int(site_id))
        return qs

    @admin.display(description="Logo")
    def logo_preview(self, obj):
        url = obj.get_logo()
        if url:
            return format_html('<img src="{}" style="max-height: 80px;" />', url)
        return "—"

    @admin.display(description="Developers")
    def developers_admin(self, obj: Product):
        return obj.developers_str()

    @admin.display(description="Publishers")
    def publishers_admin(self, obj: Product):
        return obj.publishers_str()

    # ────────── Save hooks ──────────

    def save_model(self, request, obj, form, change):
        # 1) Автоустановка site при создании
        if not change:
            site_id = request.session.get("current_site_id") or request.GET.get("site")
            if not site_id and "_changelist_filters" in request.GET:
                filters = request.GET["_changelist_filters"]
                parsed = parse_qs(filters)
                site_id = parsed.get("site", [None])[0]
            obj.site = Site.objects.get(id=site_id) if site_id else Site.objects.first()

        # 2) Тоггл активности через AJAX переключатель
        if 'is_active_toggle' in request.POST:
            obj.is_active = 'is_active' in request.POST

        super().save_model(request, obj, form, change)

        # 3) Проверка лимита Best Products
        if obj.best_products.count() > 4:
            self.message_user(request, "⚠️ Можно выбрать максимум 4 продукта для блока Best!", level='warning')
            while obj.best_products.count() > 4:
                first_to_remove = obj.best_products.last()
                obj.best_products.remove(first_to_remove)

    # ────────── Fields / формы ──────────

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        if 'rating' not in fields:
            fields.insert(0, 'rating')
        return fields

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # при GET берём тип из объекта, при POST — из формы
        product_type = request.POST.get("type") if request.method == "POST" else (obj.type if obj else None)
        if product_type:
            form.base_fields['category'].queryset = Category.objects.filter(type=product_type)
        return form

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        site = request.GET.get("site") or request.session.get("current_site_id")
        if site:
            initial["site"] = site
        return initial

    def render_change_form(self, request, context, *args, **kwargs):
        context['form'] = context['adminform'].form
        return super().render_change_form(request, context, *args, **kwargs)

    # ────────── AJAX / API ──────────

    def best_products_autocomplete(self, request):
        term = request.GET.get('term', '')
        product_type = request.GET.get('type')
        selected_ids = request.GET.getlist('selected[]')

        current_site_id = request.session.get('current_site_id') or Site.objects.get_current().id
        qs = Product.objects.filter(site_id=current_site_id)

        if product_type:
            qs = qs.filter(type=product_type)

        if selected_ids:
            qs = qs.exclude(id__in=selected_ids)

        if term:
            qs = qs.filter(title__icontains=term)

        results = [{'id': p.id, 'text': p.title} for p in qs[:20]]
        return JsonResponse({'results': results})

    def get_products(self, request, product_type):
        products = Product.objects.filter(type=product_type)
        data = [{"id": p.id, "title": p.title} for p in products]
        return JsonResponse(data, safe=False)

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        # Чистим автокомплит best_products
        if request.path.endswith('/autocomplete/') and request.GET.get('field_name') == 'best_products':
            product_type = request.GET.get('type')
            object_id = request.GET.get('object_id')

            if object_id:
                try:
                    current_product = Product.objects.get(pk=object_id)
                    product_type = product_type or current_product.type
                    queryset = queryset.exclude(id=current_product.id)
                    queryset = queryset.exclude(id__in=current_product.best_products.values_list('id', flat=True))
                except Product.DoesNotExist:
                    queryset = queryset.none()

            if product_type:
                queryset = queryset.filter(type=product_type)

        return queryset, use_distinct

    @csrf_exempt
    def upload_screenshot(self, request):
        """
        Загрузка скриншотов (кнопка под JSON/галереей) → WEBP, дата‑папки, имя без хэша.
        Возвращает {"url": "<media url>"}.
        """
        if request.method != "POST":
            return JsonResponse({"error": "Invalid request"}, status=400)

        file = request.FILES.get('file')
        if not file:
            return JsonResponse({"error": "No file"}, status=400)

        try:
            res = save_upload_as_webp(file, base_dir='screenshots')
            return JsonResponse({"url": res["url"]})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    @method_decorator(csrf_exempt)
    def autosave_screenshots(self, request, pk):
        """AJAX: перезаписывает список URL скриншотов (JSON) без перезагрузки."""
        if request.method != "POST":
            return JsonResponse({"error": "Invalid request"}, status=400)

        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return JsonResponse({"error": "Product not found"}, status=404)

        try:
            data = json.loads(request.body)
            screenshots = data.get("screenshots", [])
            product.screenshots = screenshots
            product.save(update_fields=["screenshots"])
            return JsonResponse({"success": True, "screenshots": screenshots})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    @csrf_exempt
    def ajax_delete(self, request, pk):
        if request.method == "POST":
            obj = self.get_object(request, pk)
            obj.delete()
            return JsonResponse({"success": True, "message": "🗑️ Продукт удалён"})
        return JsonResponse({"error": "Invalid request"}, status=400)

    def ajax_delete_faq(self, request, pk):
        if request.method == "POST":
            try:
                FAQ.objects.get(pk=pk).delete()
                return JsonResponse({"success": True})
            except FAQ.DoesNotExist:
                return JsonResponse({"error": "FAQ not found"}, status=404)
        return JsonResponse({"error": "Invalid request"}, status=400)

    @csrf_exempt
    def ajax_save_faq(self, request, pk=None):
        if request.method != "POST":
            return JsonResponse({"error": "Invalid request"}, status=400)

        data = json.loads(request.body)
        question = data.get("question")
        answer = data.get("answer")

        if not question or not answer:
            return JsonResponse({"error": "Both fields required"}, status=400)

        if pk:
            try:
                faq = FAQ.objects.get(pk=pk)
                faq.question = question
                faq.answer = answer
                faq.save()
            except FAQ.DoesNotExist:
                return JsonResponse({"error": "FAQ not found"}, status=404)
        else:
            product_id = request.GET.get("product_id")
            if not product_id:
                return JsonResponse({"error": "Product ID required"}, status=400)
            faq = FAQ.objects.create(product_id=product_id, question=question, answer=answer)

        return JsonResponse({"success": True, "id": faq.id})

    @csrf_exempt
    def ajax_save_poll(self, request, pk):
        if request.method != "POST":
            return JsonResponse({"success": False, "error": "Invalid request"})

        try:
            data = json.loads(request.body)
            question = data.get("question")
            answers = data.get("answers", [])
            poll_id = request.GET.get("poll_id")

            if not question or not answers:
                return JsonResponse({"success": False, "error": "Incomplete data"})

            product = Product.objects.get(pk=pk)

            if poll_id:
                poll = Poll.objects.filter(pk=poll_id, product=product).first()
                if not poll:
                    return JsonResponse({"success": False, "error": "Poll not found"})
                poll.question = question
                poll.save()
                PollOption.objects.filter(poll=poll).delete()
            else:
                poll = Poll.objects.create(product=product, question=question)

            for ans in answers:
                PollOption.objects.create(poll=poll, text=ans)

            return JsonResponse({"success": True, "poll_id": poll.id})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    @csrf_exempt
    def ajax_delete_poll(self, request, pk, poll_id):
        if request.method != "POST":
            return JsonResponse({"success": False, "error": "Invalid request"})
        try:
            poll = Poll.objects.get(pk=poll_id, product_id=pk)
            poll.delete()
            return JsonResponse({"success": True})
        except Poll.DoesNotExist:
            return JsonResponse({"success": False, "error": "Poll not found"})

    @csrf_exempt
    def toggle_is_active(self, request, pk):
        if request.method == "POST":
            obj = self.get_object(request, pk)
            data = json.loads(request.body)
            obj.is_active = data.get("is_active", False)
            obj.save(update_fields=["is_active"])
            return JsonResponse({"success": True})
        return JsonResponse({"error": "Invalid request"}, status=400)

    @csrf_exempt
    def generate_fake_products_view(self, request):
        if request.method == 'POST':
            count = int(request.POST.get('count', 1))
            call_command('generate_fake_products', count=count)
            messages.success(request, f"Створено {count} фейкових продуктів")
            return redirect('admin:products_product_changelist')

        context = self.admin_site.each_context(request)
        return render(request, 'admin/products/generate_fake.html', context)

    def duplicate_product(self, request, product_id):
        original = Product.objects.get(pk=product_id)
        base_title = original.title
        counter = 1
        new_title = f"{base_title} (Copy)"
        while Product.objects.filter(title=new_title).exists():
            counter += 1
            new_title = f"{base_title} (Copy {counter})"
        new_slug = generate_unique_slug_for_model(Product, new_title)

        # поля, которые не копируем напрямую
        exclude_fields = [
            "id", "slug", "site", "created_at",
            "polls", "best_products", "screenshots",
            "category", "author", "publishers", "developers", "type"
        ]
        original_dict = model_to_dict(original, exclude=exclude_fields)

        new_product = Product(**original_dict)
        new_product.title = new_title
        new_product.slug = new_slug
        new_product.site = original.site
        new_product.category = original.category
        new_product.author = original.author
        new_product.type = original.type

        with transaction.atomic():
            new_product.save()

            # M2M
            new_product.polls.set(original.polls.all())
            new_product.best_products.set(original.best_products.all())

            # JSON‑поля
            new_product.publishers = list(original.publishers or [])
            new_product.developers = list(original.developers or [])
            new_product.screenshots = list(original.screenshots or [])

            new_product.save(update_fields=["publishers", "developers", "screenshots"])

        self.message_user(request, f"Продукт скопійовано як “{new_product.title}”.")
        return redirect(reverse("admin:products_product_change", args=[new_product.id]))

    # ────────── Admin URLs ──────────

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('generate-fake/', self.admin_site.admin_view(self.generate_fake_products_view),
                 name='products_product_generate_fake'),
            path('<int:product_id>/duplicate/', self.admin_site.admin_view(self.duplicate_product),
                 name='product-duplicate'),
            path('<int:pk>/toggle-active/', self.admin_site.admin_view(self.toggle_is_active),
                 name='products_product_toggle_active'),
            path('<int:pk>/delete-confirm/', self.admin_site.admin_view(self.ajax_delete),
                 name='product-delete-confirm'),
            path('upload-screenshot/', self.admin_site.admin_view(self.upload_screenshot),
                 name='product-upload-screenshot'),
            path('<int:pk>/autosave-screenshots/', self.admin_site.admin_view(self.autosave_screenshots),
                 name='products_product_autosave_screenshots'),
            path('get-categories/<str:product_type>/', self.admin_site.admin_view(self.get_categories),
                 name='products_product_get_categories'),
            path('faq/ajax-save/', self.admin_site.admin_view(self.ajax_save_faq),
                 name='faq-inline-save-new'),
            path('faq/<int:pk>/ajax-save/', self.admin_site.admin_view(self.ajax_save_faq),
                 name='faq-inline-save'),
            path('faq/<int:pk>/ajax-delete/', self.admin_site.admin_view(self.ajax_delete_faq),
                 name='faq-inline-delete'),
            path('<int:pk>/ajax-save-poll/', self.admin_site.admin_view(self.ajax_save_poll),
                 name='products_product_ajax_save_poll'),
            path('<int:pk>/ajax-delete-poll/<int:poll_id>/', self.admin_site.admin_view(self.ajax_delete_poll),
                 name='products_product_ajax_delete_poll'),
            path('get-products/<str:product_type>/', self.admin_site.admin_view(self.get_products),
                 name='products_product_get_products'),
            path('best-products-autocomplete/', self.admin_site.admin_view(self.best_products_autocomplete),
                 name='products_product_best_products_autocomplete'),
            path('upload-image/', self.admin_site.admin_view(upload_image),
                 name='products_product_upload_image'),
            path('parse-steam/', steam_parser.parse_steam_view, name='products_product_parse_steam'),
            path('parse-steam/start/', steam_parser.parse_steam_start, name='products_product_parse_steam_start'),
            path('parse-steam/status/<str:job_id>/', steam_parser.parse_steam_status,
                 name='products_product_parse_steam_status'),
            path('parse-steam/cancel/<str:job_id>/', steam_parser.parse_steam_cancel,
                 name='products_product_parse_steam_cancel'),
        ]
        return custom_urls + urls

    def get_categories(self, request, product_type):
        categories = Category.objects.filter(type=product_type)
        data = [{"id": c.id, "display_name": f"{c.name} ({c.get_type_display()})"} for c in categories]
        return JsonResponse(data, safe=False)

    class Media:
        css = {
            'all': (
                'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css',
                'admin/products/css/custom_admin.css',
                'admin/products/css/autocomplete_wide.css',
            )
        }
        js = (
            'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js',
            'admin/products/js/toggle_is_active.js',
            'admin/products/js/delete_modal.js',
            'admin/products/js/product_type_toggle.js',
            'admin/products/js/category_filter.js',
            'admin/products/js/best_products_limit.js',
        )


# ────────────────────────────────
# 💬 Comments (moderation)
# ────────────────────────────────

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("product", "text", "name", "status", "email", "created_at")
    list_filter = ("status", "created_at", ("product__site", RelatedOnlyFieldListFilter))
    search_fields = ("name", "email", "text")
    list_editable = ("status",)
    save_on_top = True

    def changelist_view(self, request, extra_context=None):
        site = request.GET.get("site")
        already_filtered = "product__site__id__exact" in request.GET

        if site and site.isdigit() and not already_filtered:
            new_qs = QueryDict(mutable=True)
            new_qs["product__site__id__exact"] = site
            return redirect(f"{request.path}?{new_qs.urlencode()}")

        extra_context = extra_context or {}
        extra_context["current_site_id"] = request.GET.get("product__site__id__exact", "")
        return super().changelist_view(request, extra_context=extra_context)

    def response_post_save_add(self, request, obj):
        return redirect_back_to_filtered_list(
            request, 'admin:products_comment_changelist', param='product__site__id__exact'
        ) or super().response_post_save_add(request, obj)

    def response_post_save_change(self, request, obj):
        return redirect_back_to_filtered_list(
            request, 'admin:products_comment_changelist', param='product__site__id__exact'
        ) or super().response_post_save_change(request, obj)


# ───────────────────────────────
# ⚙️ Register into custom site
# ───────────────────────────────

custom_admin_site.register(Product, ProductAdmin)
custom_admin_site.register(Comment, CommentAdmin)
custom_admin_site.register(Category, CategoryAdmin)
custom_admin_site.register(Author, admin.ModelAdmin)
