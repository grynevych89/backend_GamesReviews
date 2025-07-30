from django.forms.widgets import Widget
from django.utils.safestring import mark_safe
from django import forms
import json

class StarRatingWidget(Widget):
    def render(self, name, value, attrs=None, renderer=None):
        try:
            value = int(value or 0)
        except (TypeError, ValueError):
            value = 0
        html = f'<div class="star-rating" data-name="{name}">'
        for i in range(5, 0, -1):
            checked = 'checked' if i == value else ''
            html += (
                f'<input type="radio" id="{name}_{i}" name="{name}" value="{i}" {checked}>'
                f'<label for="{name}_{i}">★</label>'
            )
        html += '</div>'
        return mark_safe(html)

    def value_from_datadict(self, data, files, name):
        val = data.get(name)
        return int(val) if val and val.isdigit() else None


class ScreenshotsWidget(forms.Widget):
    template_name = "admin/widgets/screenshots_widget.html"

    class Media:
        css = {"all": ("admin/products/css/screenshots_widget.css",)}
        js = ("admin/products/js/screenshots_widget.js",)

    def format_value(self, value):
        if not value:
            return "[]"
        if isinstance(value, str):
            return value
        return json.dumps(value)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["value"] = self.format_value(value)
        return context