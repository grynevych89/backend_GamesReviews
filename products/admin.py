from django.contrib import admin
from django.core.management import call_command
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.html import format_html
from django.urls import path
from django.forms.models import model_to_dict
from django.utils.text import slugify
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.db import transaction
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages


from .models import (
    Product, Category, Screenshot, FAQ,
    Poll, PollOption, Comment, Author, StorePlatform
)

admin.site.site_header = "Product Reviews Admin"
admin.site.site_title = "Product Reviews"
admin.site.index_title = "Панель управления"

def generate_unique_slug_for_model(model, title):
    base_slug = slugify(title)
    slug = base_slug
    counter = 1
    while model.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


# ────────────────────────────────
# 📄 Inlines
# ────────────────────────────────

class ScreenshotInline(admin.TabularInline):
    model = Screenshot
    extra = 1
    fields = ("image_file", "image_url")


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ("name", "email", "text", "status", "created_at")
    readonly_fields = ("created_at",)


class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 2
    fields = ("text",)


# ────────────────────────────────
# 🕹️ Product Admin
# ────────────────────────────────

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "title", "review", "is_active",
        "author", "logo_preview",
        "rating_manual", "rating_external",
        "created_at",
        "action_links",
    )
    list_display_links = ("title", "logo_preview", )
    search_fields = ("title", "author", "developers", "publishers")
    list_filter = ("site", "category", "author", "is_active")
    readonly_fields = ("created_at", "current_url", 'logo_preview',)
    list_editable = ("review", "is_active", )
    save_on_top = True
    view_on_site = True

    fieldsets = (
        ("Управління", {
            "fields": (("review", "site", "steam_id", "slug", ),)
        }),

        ("🎮 Основна інформація", {
            "fields": (
                ("title", "type", "required_age", "release_date", "current_url"),
                ("short_description", "description"),
                ("developers", "publishers"),
                ("category", "genres", "languages"),
                "website"
            )
        }),
        ("🖥️ Платформа", {
            "fields": (
                ("platform_windows", "platform_mac", "platform_linux"),
                ("store_platforms", ), )
        }),
        ("🖥️ Мінімальні вимоги", {
            "fields": (
                ("min_os", "min_processor", "min_ram"),
                ("min_graphics", "min_storage"),
                "min_additional",
            )
        }),
        ("💻 Рекомендовані вимоги", {
            "fields": (
                ("rec_os", "rec_processor", "rec_ram"),
                ("rec_graphics", "rec_storage"),
                "rec_additional",
            )
        }),
        ("📢 Огляд", {
            "fields": (("review_headline", "author",),
                       "review_body")
        }),
        ("⭐ Оцінки", {
            "fields": (("rating_manual", "rating_external"),)
        }),
        ("💸 Ціни", {
            "fields": (
                ("is_free", "price_initial", "price_final", "discount_percent", "currency"),
            )
        }),
        ("✅ Переваги / ❌ Недоліки", {
            "fields": (("pros", "cons"),),
        }),
        ("polls / faqs", {
            "fields": (("polls", "faqs"),),
        }),
        ("🕒 Дата створення", {
            "fields": ("created_at",)
        }),
        ("SEO", {
            "fields": (("seo_title", "seo_keywords", ), "og_image", "seo_description", )
        }),
        ("Кнопки завантаження", {
            "fields": (("download_button_text", "download_button_url",),)
        }),
        ("🖼️ Логотип", {
            "fields": (("logo_preview", "logo_file", "logo_url"),)
        }),
    )
    inlines = [ScreenshotInline]

    def current_url(self, obj):
        if obj.pk:
            url = obj.get_absolute_url()
            return format_html('<a href="{}" target="_blank">{}</a>', url, url)
        return "—"

    current_url.short_description = "Current URL"

    def logo_preview(self, obj):
        logo_url = obj.get_logo()
        if not logo_url:
            return "—"
        request = getattr(self, 'request_for_preview', None)
        if request and request.resolver_match.view_name == "admin:products_product_change":
            # В адмінформі — посилання на картинку
            return format_html('<a href="{0}" target="_blank"><img src="{0}" style="max-height: 100px;" /></a>',
                               logo_url)
        else:
            # В списку — посилання на редагування
            change_url = reverse("admin:products_product_change", args=[obj.pk])
            return format_html('<a href="{0}"><img src="{1}" style="max-height: 80px;" /></a>', change_url, logo_url)

    logo_preview.short_description = "Logo preview"

    def get_queryset(self, request):
        self.request_for_preview = request  # зберігаємо request під правильним ім’ям
        return super().get_queryset(request)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_for_preview = None

    def action_links(self, obj):
        view_url = obj.get_absolute_url()
        change_url = reverse("admin:products_product_change", args=[obj.pk])
        duplicate_url = reverse("admin:product-duplicate", args=[obj.pk])
        delete_url = reverse("admin:product-delete-confirm", args=[obj.pk])  # 👈 AJAX удаление

        return format_html(
            '<a class="button" target="_blank" href="{}">👁️</a>&nbsp;'
            '<a class="button" href="{}">Редактировать</a>&nbsp;'
            '<a class="button" href="{}">Копировать</a>&nbsp;'
            '<a href="#" class="button delete-button" data-url="{}" style="background-color:red;">Удалить</a>',
            view_url,
            change_url,
            duplicate_url,
            delete_url,
        )

    action_links.short_description = "Действия"

    def ajax_delete(self, request, pk):
        if request.method == "POST":
            obj = self.get_object(request, pk)
            obj.delete()
            return JsonResponse({"success": True})
        return JsonResponse({"error": "Invalid request"}, status=400)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('generate-fake/', self.admin_site.admin_view(self.generate_fake_products_view), name='products_product_generate_fake'),
            path('<int:product_id>/duplicate/', self.admin_site.admin_view(self.duplicate_product), name='product-duplicate'),
            path('<int:pk>/toggle-active/', self.admin_site.admin_view(self.toggle_is_active),
                 name='products_product_toggle_active'),
            path('<int:pk>/delete-confirm/', self.admin_site.admin_view(self.ajax_delete),
                 name='product-delete-confirm'),
        ]
        return custom_urls + urls

    @csrf_exempt
    def generate_fake_products_view(self, request):
        if request.method == 'POST':
            count = int(request.POST.get('count', 1))
            call_command('generate_fake_products', count=count)
            messages.success(request, f"Створено {count} фейкових продуктів")
            return redirect('admin:products_product_changelist')

        return render(request, 'admin/products/generate_fake.html', {})

    change_list_template = "admin/products/change_list_with_generate.html"

    @csrf_exempt
    def toggle_is_active(self, request, pk):
        if request.method == "POST":
            obj = self.get_object(request, pk)
            data = json.loads(request.body)
            obj.is_active = data.get("is_active", False)
            obj.save()
            return JsonResponse({"success": True})
        return JsonResponse({"error": "Invalid request"}, status=400)

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
            "category", "author", "store_platforms", "genres", "languages",
            "developers", "publishers", "type"
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
            new_product.store_platforms.set(original.store_platforms.all())
            new_product.polls.set(original.polls.all())
            new_product.faqs.set(original.faqs.all())
            new_product.genres.set(original.genres.all())
            new_product.languages.set(original.languages.all())
            new_product.developers.set(original.developers.all())
            new_product.publishers.set(original.publishers.all())
            for screenshot in original.screenshots.all():
                screenshot.pk = None
                screenshot.product = new_product
                screenshot.save()

        self.message_user(request, f"Продукт скопійовано як “{new_product.title}”.")
        return redirect(reverse("admin:products_product_change", args=[new_product.id]))

    def get_view_on_site_url(self, obj):
        if not obj or not obj.pk:
            return None
        return obj.get_absolute_url()

    def save_model(self, request, obj, form, change):
        if 'is_active_toggle' in request.POST:
            obj.is_active = 'is_active' in request.POST
        super().save_model(request, obj, form, change)

    class Media:
        css = {
            'all': ('admin/products/css/admin_ckeditor_fix.css',
                    'admin/products/css/custom_admin.css',)
        }
        js = ('admin/products/js/toggle_is_active.js',
              'admin/products/js/delete_modal.js',)

# ────────────────────────────────
# 💬 Comments (moderation)
# ────────────────────────────────

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("product", "text", "name", "status", "email", "created_at")
    list_filter = ("status", "created_at",)
    search_fields = ("name", "email", "text")
    list_editable = ("status",)
    save_on_top = True

@admin.register(StorePlatform)
class StorePlatformAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_url', 'store_url')
    search_fields = ('name',)

    def has_module_permission(self, request):
        return False

