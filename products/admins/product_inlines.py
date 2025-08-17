from django import forms
from django.contrib import admin
from django.core.files.storage import default_storage
from django.db import models
from django.db.models.fields.files import FieldFile
from django.forms.models import BaseInlineFormSet
from django.urls import reverse
from django.utils.html import format_html

from products.forms import FAQInlineForm, PollForm
from products.models import FAQ, Poll
from products.utils.images import save_upload_as_webp


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
    def _extract_upload(self, form):
        uploaded = form.cleaned_data.get("image")
        if uploaded:
            if isinstance(uploaded, FieldFile) and getattr(uploaded, "name", "").startswith("polls/"):
                return None
            return uploaded
        f = form.files.get(form.add_prefix("image"))
        if hasattr(f, "name") and isinstance(f, FieldFile) and f.name.startswith("polls/"):
            return None
        return f

    def _assign_image(self, obj, uploaded, old_name=None):
        if not uploaded:
            return False
        res = save_upload_as_webp(uploaded, base_dir="polls")
        name = res.get("name") or res.get("relative") or res.get("path")
        if not name:
            return False

        if getattr(obj, "image", None) is not None:
            obj.image.name = name
        else:
            obj.image = name

        if old_name and old_name != getattr(getattr(obj, "image", None), "name", None):
            try:
                default_storage.delete(old_name)
            except Exception:
                pass
        return True

    def save_new(self, form, commit=True):
        poll_id = form.data.get(form.add_prefix("id"))
        if poll_id:
            try:
                obj = Poll.objects.get(pk=int(poll_id))
            except Poll.DoesNotExist:
                obj = super().save_new(form, commit=False)
        else:
            obj = super().save_new(form, commit=False)

        uploaded = self._extract_upload(form)
        if uploaded:
            old = getattr(obj.image, "name", None)
            self._assign_image(obj, uploaded, old_name=old)

        if commit:
            obj.save()
        return obj

    def save_existing(self, form, instance, commit=True):
        obj = super().save_existing(form, instance, commit=False)
        uploaded = self._extract_upload(form)
        old = getattr(instance.image, "name", None)
        self._assign_image(obj, uploaded, old_name=old)
        if commit:
            obj.save()
        return obj


class PollInline(admin.TabularInline):
    model = Poll
    form = PollForm
    formset = PollInlineFormSet
    extra = 0
    min_num = 0
    can_delete = False
    show_change_link = False

    fields = ("title", "question", "actions", "_preview", "image")
    readonly_fields = ("actions", "_preview")

    verbose_name = "📊 Опрос"
    verbose_name_plural = "📊 Опросы продукта"
    template = "admin/products/product/polls_tabular.html"

    formfield_overrides = {
        models.CharField: {"widget": forms.TextInput(attrs={"class": "vTextField"})},
    }

    def _preview(self, obj):
        if obj and getattr(obj, "image", None):
            return format_html(
                '<div class="poll-preview" style="width:240px;height:140px;border:1px solid #2a2a2a;background:#111;">'
                '<img src="{}" style="width:100%;height:100%;object-fit:contain;display:block;" />'
                '</div>',
                obj.image.url
            )
        return format_html(
            '<div class="poll-preview" style="width:240px;height:140px;border:1px solid #2a2a2a;background:#111;"></div>'
        )

    _preview.short_description = "Preview"

    def actions(self, obj):
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
        else:
            delete_btn = (
                '<button type="button" class="button delete-button poll-delete-button" '
                'style="background-color:#ef4444;color:white;opacity:.6;cursor:not-allowed;" '
                'title="Сохраните опрос, чтобы удалить">🗑️</button>'
            )
        return format_html(delete_btn)

    class Media:
        js = ("admin/products/js/poll_inline.js",)
        css = {"all": ("admin/products/css/polls_inline.css",)}
