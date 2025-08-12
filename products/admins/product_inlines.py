from django import forms
from django.contrib import admin
from django.db import models
from django.forms.models import BaseInlineFormSet
from django.urls import reverse
from django.utils.html import format_html

from products.forms import FAQInlineForm
from products.models import FAQ, Poll


class FAQInline(admin.TabularInline):
    model = FAQ
    form = FAQInlineForm
    template = "admin/products/product/faq_tabular.html"
    extra = 0
    min_num = 0
    can_delete = False
    show_change_link = False
    fields = ("question", "answer", "actions")
    readonly_fields = ("actions",)

    def actions(self, obj):
        save_btn = (
            '<button type="button" class="button faq-save-button" '
            'style="background-color:green;color:white;margin-right:5px;">💾</button>'
        )
        delete_btn = ""
        if obj and obj.pk:
            url = reverse(f"{self.admin_site.name}:faq-inline-delete", args=[obj.pk])
            delete_btn = f'<button type="button" class="button faq-delete-button" data-url="{url}" style="background:#ef4444;color:#fff;">🗑️</button>'
        return format_html(save_btn + delete_btn)


class PollInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()


class PollInline(admin.TabularInline):
    model = Poll
    formset = PollInlineFormSet
    extra = 0
    min_num = 0
    can_delete = False
    show_change_link = False
    fields = ("question", "actions")
    readonly_fields = ("actions",)
    verbose_name = "📊 Опрос"
    verbose_name_plural = "📊 Опросы продукта"
    template = "admin/products/product/polls_tabular.html"
    formfield_overrides = {
        models.CharField: {"widget": forms.TextInput(attrs={"class": "vTextField"})},
    }

    def actions(self, obj):
        save_btn = (
            '<button type="button" class="button poll-save-button" '
            'style="background-color:#0ea5e9;color:white;margin-right:5px;">💾</button>'
        )
        delete_btn = ""
        if obj and obj.pk:
            url = reverse(
                f"{self.admin_site.name}:products_product_ajax_delete_poll",
                args=[obj.product_id, obj.pk],
            )
            delete_btn = (
                f'<button type="button" class="button delete-button poll-delete-button" '
                f'data-url="{url}" style="background-color:#ef4444;color:white;">🗑️</button>'
            )
        return format_html(save_btn + delete_btn)

    class Media:
        js = ("admin/products/js/poll_inline.js",)
