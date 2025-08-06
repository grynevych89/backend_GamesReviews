from django import forms
from .models import Product
from .widgets import StarRatingWidget, ScreenshotsWidget
from django.contrib.admin.widgets import AdminFileWidget
from django.contrib.admin.widgets import AdminURLFieldWidget


class CustomFileWidget(AdminFileWidget):
    template_name = 'admin/widgets/custom_file_input.html'

class CustomURLWidget(AdminURLFieldWidget):
    template_name = 'admin/widgets/custom_url_input.html'

class ProductForm(forms.ModelForm):
    publishers_str = forms.CharField(
        label="Publishers",
        required=False,
        disabled=False,  # Можно редактировать
        widget=forms.TextInput(attrs={"placeholder": "Ubisoft, EA, Sony"})
    )
    actors_str = forms.CharField(
        label="Actors",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Actor 1, Actor 2, Actor 3"})
    )

    class Meta:
        model = Product
        exclude = ['site', 'publishers', 'actors']
        fields = "__all__"
        widgets = {
            'rating': StarRatingWidget(attrs={'class': 'top-rating-widget'}),
            "steam_url": forms.TextInput(attrs={"placeholder": "Steam URL"}),
            "app_store_url": forms.TextInput(attrs={"placeholder": "App Store URL"}),
            "android_url": forms.TextInput(attrs={"placeholder": "Android URL"}),
            "playstation_url": forms.TextInput(attrs={"placeholder": "PlayStation URL"}),
            "official_website": forms.TextInput(attrs={"placeholder": "Official Website"}),
            'pros': forms.Textarea(attrs={'rows': 10, 'cols': 50}),
            'cons': forms.Textarea(attrs={'rows': 10, 'cols': 50}),
            "screenshots": ScreenshotsWidget(),
            'rating_1': forms.NumberInput(attrs={'min': 4, 'max': 10, 'step': 0.5, 'oninput': 'validateRating(this)'}),
            'rating_2': forms.NumberInput(attrs={'min': 4, 'max': 10, 'step': 0.5, 'oninput': 'validateRating(this)'}),
            'rating_3': forms.NumberInput(attrs={'min': 4, 'max': 10, 'step': 0.5, 'oninput': 'validateRating(this)'}),
            'rating_4': forms.NumberInput(attrs={'min': 4, 'max': 10, 'step': 0.5, 'oninput': 'validateRating(this)'}),
            'logo_file': CustomFileWidget(),
            'logo_url': CustomURLWidget(),
        }
        labels = {
            "screenshots": "",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Инициализация строковых полей из JSON
        if self.instance and self.instance.pk:
            self.fields['publishers_str'].initial = ", ".join(self.instance.publishers or [])
            self.fields['actors_str'].initial = ", ".join(self.instance.actors or [])

        # Ограничение best_products по типу
        product_type = self.instance.type if self.instance else self.initial.get('type', None)
        if product_type:
            self.fields['best_products'].queryset = Product.objects.filter(type=product_type)
        self.fields['best_products'].widget.attrs['class'] = 'vSelectMultipleField'
        self.fields['best_products'].widget.can_add_related = False

    def clean_publishers_str(self):
        data = self.cleaned_data.get('publishers_str', '')
        return [p.strip() for p in data.split(",") if p.strip()]

    def clean_actors_str(self):
        data = self.cleaned_data.get('actors_str', '')
        return [a.strip() for a in data.split(",") if a.strip()]

    def clean_best_products(self):
        data = self.cleaned_data['best_products']
        if len(data) > 4:
            raise forms.ValidationError("Можно выбрать максимум 4 продукта.")
        return data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Сохраняем JSON-поля
        instance.publishers = self.cleaned_data['publishers_str']
        instance.actors = self.cleaned_data['actors_str']
        if commit:
            instance.save()
        return instance

    class Media:
        css = {
            'all': (
                'admin/products/css/star_rating.css',
                'admin/products/css/screenshots_widget.css',
            )
        }
        js = (
            'admin/products/js/screenshots_widget.js',
        )
