from django.contrib import admin
from django.shortcuts import redirect
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

from .models import (
    Game, Category, Screenshot, FAQ,
    Poll, PollOption, Comment, Author
)

admin.site.site_header = "Game Reviews Admin"
admin.site.site_title = "Game Reviews"
admin.site.index_title = "Панель управления"


def generate_unique_slug(model, title):
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
# 🕹️ Game Admin
# ────────────────────────────────

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = (
        "site", "title",
        "author", "developer", "publisher",
        "rating_manual", "rating_external",
        "created_at",
        "is_active",
        "action_links",
    )
    list_display_links = ("title",)
    search_fields = ("title", "author", "developer", "publisher")
    list_filter = ("site", "category", "author", "is_active")
    readonly_fields = ("created_at", "current_url",)
    list_editable = ("is_active",)

    save_on_top = True
    view_on_site = True

    fieldsets = (
        ("Управління", {
            "fields": (("site", "steam_id", "slug",),)
        }),

        ("🎮 Основна інформація", {
            "fields": (("title", "current_url",),
                       ("author", "developer", "publisher",),
                       "category",)
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
            "fields": ("review_headline", "review_body")
        }),
        ("🖼️ Логотип", {
            "fields": (("logo_file", "logo_url"),)
        }),
        ("⭐ Оцінки", {
            "fields": (("rating_manual", "rating_external"),)
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
    )
    inlines = [ScreenshotInline]

    def current_url(self, obj):
        if obj.pk:
            url = obj.get_absolute_url()
            return format_html('<a href="{}" target="_blank">{}</a>', url, url)
        return "—"

    current_url.short_description = "Current URL"

    def action_links(self, obj):
        return format_html(
            '<a class="button" href="{}">Копировать</a>&nbsp;'
            '<a class="button" style="background-color:red;" href="{}">Удалить</a>',
            reverse("admin:game-duplicate", args=[obj.id]),
            reverse("admin:games_game_delete", args=[obj.id]),
        )

    action_links.short_description = "Действия"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:game_id>/duplicate/', self.admin_site.admin_view(self.duplicate_game), name='game-duplicate'),
            path('<int:pk>/toggle-active/', self.admin_site.admin_view(self.toggle_is_active),
                 name='games_game_toggle_active'),
        ]
        return custom_urls + urls

    @csrf_exempt
    def toggle_is_active(self, request, pk):
        if request.method == "POST":
            obj = self.get_object(request, pk)
            data = json.loads(request.body)
            obj.is_active = data.get("is_active", False)
            obj.save()
            return JsonResponse({"success": True})
        return JsonResponse({"error": "Invalid request"}, status=400)

    def duplicate_game(self, request, game_id):
        original = Game.objects.get(pk=game_id)

        # Исключаем ForeignKey поля, чтобы не получить их ID
        original_dict = model_to_dict(
            original,
            exclude=["id", "slug", "site", "created_at", "polls", "faqs", "screenshots", "category", "author"]
        )

        # Вручную присваиваем ForeignKey объекты
        new_game = Game(**original_dict)
        new_game.title += " (Copy)"
        new_game.slug = generate_unique_slug(Game, new_game.title)
        new_game.site = original.site
        new_game.category = original.category
        new_game.author = original.author
        new_game.save()

        # ManyToMany: polls и faqs
        new_game.polls.set(original.polls.all())
        new_game.faqs.set(original.faqs.all())

        # Копируем скриншоты
        for screenshot in original.screenshots.all():
            screenshot.pk = None
            screenshot.game = new_game
            screenshot.save()

        self.message_user(request, "Гра скопійована — змініть slug або сайт, якщо потрібно.")
        change_url = reverse("admin:games_game_change", args=[new_game.id])
        return redirect(change_url)

    def get_view_on_site_url(self, obj):
        return obj.get_absolute_url()

    def save_model(self, request, obj, form, change):
        if 'is_active_toggle' in request.POST:
            obj.is_active = 'is_active' in request.POST
        super().save_model(request, obj, form, change)

    class Media:
        css = {
            'all': ('games/css/admin_ckeditor_fix.css',
                    'games/css/custom_admin.css',)
        }
        js = ('games/js/toggle_is_active.js',)


# ────────────────────────────────
# 📊 Poll Admin
# ────────────────────────────────

# @admin.register(Poll)
# class PollAdmin(admin.ModelAdmin):
#     list_display = ("question",)
#     search_fields = ("question",)
#     inlines = [PollOptionInline]

# ────────────────────────────────
#  FAQ
# ────────────────────────────────

# @admin.register(FAQ)
# class FAQAdmin(admin.ModelAdmin):
#     list_display = ("question",)

# ────────────────────────────────
# 🏷️ Category
# ────────────────────────────────

# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ("name",)
#     search_fields = ("name",)

# ────────────────────────────────
# 💬 Comments (moderation)
# ────────────────────────────────

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("game", "text", "name", "status", "email", "created_at")
    list_filter = ("status", "created_at",)
    search_fields = ("name", "email", "text")
    list_editable = ("status",)
    save_on_top = True

#
# @admin.register(Author)
# class AuthorAdmin(admin.ModelAdmin):
#     list_display = ("name", )
#     search_fields = ("name",)
