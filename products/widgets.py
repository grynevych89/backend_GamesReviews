from django.forms.widgets import Widget
from django.utils.safestring import mark_safe

class StarRatingWidget(Widget):
    def render(self, name, value, attrs=None, renderer=None):
        value = value or 0
        html = '<div class="star-rating" data-name="{name}">'.format(name=name)
        for i in range(5, 0, -1):
            checked = "checked" if i == value else ""
            html += (
                f'<input type="radio" id="{name}_{i}" name="{name}" value="{i}" {checked}>'
                f'<label for="{name}_{i}">★</label>'
            )
        html += '</div>'
        return mark_safe(html)

    def value_from_datadict(self, data, files, name):
        return data.get(name)