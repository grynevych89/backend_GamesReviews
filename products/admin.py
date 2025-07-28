import json
from django.forms.models import model_to_dict
from django.contrib import admin, messages
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.text import slugify
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django import forms
from .models import (
    Product, Category, Screenshot, FAQ,
    Poll, PollOption, Comment, Author
)
from .widgets import StarRatingWidget
from .custom_admin import SiteAwareAdminSite
from django.http import QueryDict
from urllib.parse import urlparse, parse_qs

# ────────────────────────────────
# 🧭 Site Configuration
# ────────────────────────────────
admin.site.site_header = "Product Reviews Admin"
admin.site.site_title = "Product Reviews"
admin.site.index_title = "Панель управления"

# ────────────────────────────────
# 🔧 Utilities
# ────────────────────────────────
def generate_unique_slug_for_model(model, title):
    base_slug = slugify(title)
    slug = base_slug
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
class ScreenshotInline(admin.TabularInline):
    model = Screenshot
    extra = 1
    fields = ("custom_preview", "image_file", "image_url", "inline_delete_button")
    readonly_fields = ("custom_preview", "inline_delete_button")

    def has_delete_permission(self, request, obj=None):
        return False

    def custom_preview(self, obj):
        image_url = ""
        if obj.image_file:
            image_url = obj.image_file.url
        elif obj.image_url:
            image_url = obj.image_url
        if image_url:
            return format_html(
                '<img src="{}" style="max-height: 100px; border-radius: 4px; border: 1px solid #444;" />',
                image_url
            )
        return "—"
    custom_preview.short_description = "Preview"

    def inline_delete_button(self, obj):
        if obj.pk:
            return format_html(
                '<a class="button delete-button" style="background:red;color:white;" '
                'data-url="{}">Удалить</a>',
                reverse('admin:products_screenshot_delete', args=[obj.pk])
            )
        return ""
    inline_delete_button.short_description = "Удалить"

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ("name", "email", "text", "status", "created_at")
    readonly_fields = ("created_at",)

class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 2
    fields = ("text",)

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"
        widgets = {
            'rating': StarRatingWidget(),
            "steam_url": forms.TextInput(attrs={"placeholder": "Steam URL"}),
            "app_store_url": forms.TextInput(attrs={"placeholder": "App Store URL"}),
            "android_url": forms.TextInput(attrs={"placeholder": "Android URL"}),
            "playstation_url": forms.TextInput(attrs={"placeholder": "PlayStation URL"}),
            "official_website": forms.TextInput(attrs={"placeholder": "Official Website"}),
        }

    class Media:
        css = {
            'all': ('admin/products/css/star_rating.css',)
        }


# ───────────────────────────────
# 🕹️ Product Admin
# ───────────────────────────────
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "title", "type", "category", "created_at",
        "platform_links", "action_links",
    )
    list_display_links = ("title", )
    search_fields = ("title", "author", "developers", "publishers")
    readonly_fields = ("created_at", "steam_id", 'logo_preview', )
    save_on_top = True
    view_on_site = True
    form = ProductForm
    change_list_template = "admin/products/change_list_with_generate.html"
    inlines = [ScreenshotInline]
    prepopulated_fields = {"slug": ("title",)}

    # ────────── Layout ──────────
    fieldsets = (
        ("⚙️ Управління", {
            "fields": (
                ("site", "steam_id", "slug", "rating", ),)
        }),
        ("🎮 Основна інформація", {
            "fields": (
                ("title", "type", "required_age", "release_date", ),)
        }),
        ("⚙️ Мінімальні вимоги", {
            "fields": (
                ("min_os", "min_processor", "min_ram"),
                ("min_graphics", "min_storage", "min_additional", ),)
        }),
        ("⚙️ Посилання на платформи", {
            "fields": (
                ("official_website", "android_url", "app_store_url",
                 "steam_url", "playstation_url", ),)
        }),
        ("📢 Огляд", {
            "fields": (("review_headline", "author",), "review_body")
        }),
        ("⭐ Оцінки", {
            "fields": (("rating_story", "rating_directing",
                        "rating_soundTrack", "rating_specialEffects", ),)
        }),
        ("✅ Переваги / ❌ Недоліки", {
            "fields": (("pros", "cons"),)
        }),
        # ("📊 Опитування  / ❓ FAQ", {
        #     "fields": (("polls", "faqs"),)
        # }),
        ("🌐 SEO", {
            "fields": (("seo_title", "seo_description",), )
        }),
        ("🖼️ Логотип", {
            "fields": (("logo_preview", "logo_file", "logo_url"),)
        }),
    )

    # ────────── Custom Methods ──────────

    def current_url(self, obj):
        if obj.pk:
            url = obj.get_absolute_url()
            return format_html('<a href="{}" target="_blank">{}</a>', url, url)
        return "—"

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
                '<a href="{0}" target="_blank" class="button" title="{2}" style="padding: 2px 5px;">'
                '<img src="{1}" style="height:18px;" alt="{2}"/></a>',
                url, icon, label
            )
            for url, icon, label in platforms if url and url.strip()
        ])

        return format_html('<div style="display: flex; gap: 4px;">{}</div>', format_html(icons_html))

    platform_links.short_description = "Platform Links"

    def action_links(self, obj):
        view_url = obj.get_absolute_url()
        change_url = reverse("admin:products_product_change", args=[obj.pk])
        duplicate_url = reverse("admin:product-duplicate", args=[obj.pk])
        delete_url = reverse("admin:product-delete-confirm", args=[obj.pk])

        return format_html(
            '<div style="display:flex; gap:4px;">'
            '<a class="button" target="_blank" href="{}">👁️</a>'
            '<a class="button" href="{}">✏️</a>'
            '<a class="button" href="{}">📄</a>'
            '<a href="#" class="button delete-button" data-url="{}" style="background-color:red;">🗑️</a>'
            '</div>',
            view_url, change_url, duplicate_url, delete_url
        )

    action_links.short_description = "Action Links"

    @method_decorator(csrf_exempt)
    def delete_screenshot(self, request, pk):
        if request.method == "POST":
            try:
                Screenshot.objects.get(pk=pk).delete()
                return JsonResponse({"success": True})
            except Screenshot.DoesNotExist:
                return JsonResponse({"success": False, "error": "Не найдено"})
        return JsonResponse({"success": False, "error": "Недопустимый метод"})

    # ────────── Lifecycle ──────────
    def get_queryset(self, request):
        site_id = request.GET.get("site")
        qs = super().get_queryset(request)

        if site_id and site_id.isdigit():
            return qs.filter(site_id=int(site_id))
        return qs

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save_model(self, request, obj, form, change):
        if 'is_active_toggle' in request.POST:
            obj.is_active = 'is_active' in request.POST
        super().save_model(request, obj, form, change)

    # ────────── Custom Admin URLs ──────────
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "screenshot/<int:pk>/delete/",
                self.admin_site.admin_view(self.delete_screenshot),
                name="products_screenshot_delete",
            ),
            path('generate-fake/', self.admin_site.admin_view(self.generate_fake_products_view), name='products_product_generate_fake'),
            path('<int:product_id>/duplicate/', self.admin_site.admin_view(self.duplicate_product), name='product-duplicate'),
            path('<int:pk>/toggle-active/', self.admin_site.admin_view(self.toggle_is_active), name='products_product_toggle_active'),
            path('<int:pk>/delete-confirm/', self.admin_site.admin_view(self.ajax_delete), name='product-delete-confirm'),
        ]
        return custom_urls + urls

    @csrf_exempt
    def ajax_delete(self, request, pk):
        if request.method == "POST":
            obj = self.get_object(request, pk)
            obj.delete()
            return JsonResponse({"success": True})
        return JsonResponse({"error": "Invalid request"}, status=400)

    @csrf_exempt
    def toggle_is_active(self, request, pk):
        if request.method == "POST":
            obj = self.get_object(request, pk)
            data = json.loads(request.body)
            obj.is_active = data.get("is_active", False)
            obj.save()
            return JsonResponse({"success": True})
        return JsonResponse({"error": "Invalid request"}, status=400)

    @csrf_exempt
    def generate_fake_products_view(self, request):
        if request.method == 'POST':
            count = int(request.POST.get('count', 1))
            call_command('generate_fake_products', count=count)
            messages.success(request, f"Створено {count} фейкових продуктів")
            return redirect('admin:products_product_changelist')
        return render(request, 'admin/products/generate_fake.html', {})

    def duplicate_product(self, request, product_id):
        original = Product.objects.get(pk=product_id)
        base_title = original.title
        counter = 1
        new_title = f"{base_title} (Copy)"
        while Product.objects.filter(title=new_title).exists():
            counter += 1
            new_title = f"{base_title} (Copy {counter})"
        new_slug = generate_unique_slug_for_model(Product, new_title)

        exclude_fields = [
            "id", "slug", "site", "created_at", "polls", "faqs", "screenshots",
            "category", "author", "publishers", "type"
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
            new_product.polls.set(original.polls.all())
            new_product.faqs.set(original.faqs.all())

            new_product.publishers.set(original.publishers.all())
            for screenshot in original.screenshots.all():
                screenshot.pk = None
                screenshot.product = new_product
                screenshot.save()

        self.message_user(request, f"Продукт скопійовано як “{new_product.title}”.")
        return redirect(reverse("admin:products_product_change", args=[new_product.id]))

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        site = request.GET.get("site") or request.session.get("current_site_id")
        if site:
            initial["site"] = site
        return initial

    def response_post_save_add(self, request, obj):
        return redirect_back_to_filtered_list(
            request, 'admin:products_product_changelist', param='site') \
            or super().response_post_save_add(request, obj)

    def response_post_save_change(self, request, obj):
        return redirect_back_to_filtered_list(
            request, 'admin:products_product_changelist', param='site') \
            or super().response_post_save_change(request, obj)

    class Media:
        css = {
            'all': (
                'admin/products/css/admin_ckeditor_fix.css',
                'admin/products/css/custom_admin.css',
            )
        }
        js = (
            'admin/products/js/toggle_is_active.js',
            'admin/products/js/delete_modal.js',
        )

# ────────────────────────────────
# 💬 Comments (moderation)
# ────────────────────────────────
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("product", "text", "name", "status", "email", "created_at")
    list_filter = ("status", "created_at", )
    search_fields = ("name", "email", "text")
    list_editable = ("status",)
    save_on_top = True

    def changelist_view(self, request, extra_context=None):
        site = request.GET.get("site")
        already_filtered = "product__site__id__exact" in request.GET

        if site and site.isdigit() and not already_filtered:
            # Формируем новый чистый QueryDict
            new_qs = QueryDict(mutable=True)
            new_qs["product__site__id__exact"] = site
            return redirect(f"{request.path}?{new_qs.urlencode()}")

        extra_context = extra_context or {}
        extra_context["current_site_id"] = request.GET.get("product__site__id__exact", "")
        return super().changelist_view(request, extra_context=extra_context)

    def response_post_save_add(self, request, obj):
        return redirect_back_to_filtered_list(
            request, 'admin:products_comment_changelist', param='product__site__id__exact') \
            or super().response_post_save_add(request, obj)

    def response_post_save_change(self, request, obj):
        return redirect_back_to_filtered_list(
            request, 'admin:products_comment_changelist', param='product__site__id__exact') \
            or super().response_post_save_change(request, obj)


# ───────────────────────────────
# ⚙️ Hide unused models
# ───────────────────────────────
class CustomSiteAdmin(admin.ModelAdmin):
    list_display = ('domain', 'name', 'link_to_products', 'link_to_comments')
    search_fields = ('domain', 'name')

    def link_to_products(self, obj):
        url = reverse('admin:products_product_changelist') + f"?site={obj.id}"
        return format_html('<a class="button" href="{}">📦 Продукти</a>', url)

    def link_to_comments(self, obj):
        url = reverse('admin:products_comment_changelist') + f"?site={obj.id}"
        return format_html('<a class="button" href="{}">🗨️ Коментарі</a>', url)

    link_to_products.short_description = "Продукти"
    link_to_comments.short_description = "Коментарі"

custom_admin_site = SiteAwareAdminSite(name="custom_admin")
custom_admin_site.register(Product, ProductAdmin)
custom_admin_site.register(Comment, CommentAdmin)
custom_admin_site.register(Site, CustomSiteAdmin)
