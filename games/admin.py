from django.contrib import admin, messages
from django.urls import path
from django import forms
from django.shortcuts import render, redirect
from .models import (
    Game, Category, Screenshot, FAQ,
    Poll, PollOption, Comment
)

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
    fields = ("name", "email", "text", "is_approved", "created_at")
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
    list_display = ("title", "developer", "publisher", "is_active", "rating_manual", "rating_external", "created_at")
    search_fields = ("title", "developer", "publisher")
    list_filter = ("categories", "is_active")
    filter_horizontal = ("categories", "polls", "faqs")
    readonly_fields = ("created_at",)

    fieldsets = (
        ("🎮 Основна інформація", {
            "fields": (("title", "steam_id", "is_active", ),
                       ("developer", "publisher",),
                       "categories",)
        }),
        ("📢 Огляд", {
            "fields": ("review_headline", "review_body")
        }),
        ("🖼️ Логотип", {
            "fields": (("logo_file", "logo_url"), )
        }),
        ("⭐ Оцінки", {
            "fields": (("rating_manual", "rating_external"), )
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
    inlines = [ScreenshotInline, CommentInline]

# ────────────────────────────────
# 📊 Poll Admin
# ────────────────────────────────

@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ("question",)
    search_fields = ("question",)
    inlines = [PollOptionInline]

# ────────────────────────────────
#  FAQ
# ────────────────────────────────

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question",)

# ────────────────────────────────
# 🏷️ Category
# ────────────────────────────────

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

# ────────────────────────────────
# 💬 Comments (moderation)
# ────────────────────────────────

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "game", "is_approved", "created_at")
    list_filter = ("is_approved", "game")
    search_fields = ("name", "email", "text")
    actions = ["approve_selected"]

    @admin.action(description="Схвалити вибрані коментарі")
    def approve_selected(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} коментар(ів) схвалено.")
