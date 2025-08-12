from django import forms

from .models import Product, FAQ
from .widgets import StarRatingWidget, ScreenshotsWidget
from django.contrib.admin.widgets import AdminFileWidget
from django.contrib.admin.widgets import AdminURLFieldWidget
from tinymce.widgets import TinyMCE
from products.utils.images import save_upload_as_webp, save_url_as_webp
from django.core.files.storage import default_storage


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
    developers_str = forms.CharField(
        label="Developers",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Developer 1, Developer 2"})
    )
    actors_str = forms.CharField(
        label="Actors",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Actor 1, Actor 2, Actor 3"})
    )

    class Meta:
        model = Product
        exclude = ['site', 'publishers', 'developers', 'actors']
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
            'logo_file': forms.FileInput(),
            'logo_url': forms.URLInput(),
            'review_body': TinyMCE(attrs={'class': 'tinymce-field'}),

        }
        labels = {
            "screenshots": "",
            "logo_file": "",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Инициализация строковых полей из JSON
        if self.instance and self.instance.pk:
            self.fields['publishers_str'].initial = ", ".join(self.instance.publishers or [])
            self.fields['developers_str'].initial = ", ".join(self.instance.developers or [])
            self.fields['actors_str'].initial = ", ".join(self.instance.actors or [])

        # Ограничение best_products по типу
        product_type = self.instance.type if self.instance else self.initial.get('type', None)
        if product_type:
            self.fields['best_products'].queryset = Product.objects.filter(type=product_type)
        self.fields['best_products'].widget.attrs['class'] = 'vSelectMultipleField'
        self.fields['best_products'].widget.can_add_related = False
        self._old_logo_name = (
            getattr(getattr(self.instance, "logo_file", None), "name", None)
            if self.instance and self.instance.pk else None
        )
        self._delete_old_logo_file = False
        self._new_logo_file_result = None

    def clean_publishers_str(self):
        data = self.cleaned_data.get('publishers_str', '')
        return [p.strip() for p in data.split(",") if p.strip()]

    def clean_developers_str(self):
        data = self.cleaned_data.get('developers_str', '')
        return [p.strip() for p in data.split(",") if p.strip()]

    def clean_actors_str(self):
        data = self.cleaned_data.get('actors_str', '')
        return [a.strip() for a in data.split(",") if a.strip()]

    def clean_best_products(self):
        data = self.cleaned_data['best_products']
        if len(data) > 4:
            raise forms.ValidationError("Можно выбрать максимум 4 продукта.")
        return data

    def clean(self):
        data = super().clean()
        uploaded = self.files.get("logo_file")
        url = (data.get("logo_url") or "").strip()

        if uploaded:
            # локальный → конвертируем, URL чистим
            self._new_logo_file_result = save_upload_as_webp(uploaded, base_dir="logos")
            data["logo_url"] = ""
            data["logo_file"] = None
            # удалять старый файл будем, если он был
            if self._old_logo_name:
                self._delete_old_logo_file = True

        elif url:
            # URL → качаем/конвертируем, URL чистим (в БД оставляем только локальный webp)
            self._new_logo_file_result = save_url_as_webp(url, base_dir="logos")
            data["logo_url"] = ""
            data["logo_file"] = None
            # важно: флаг удаления ставим по _old_logo_name (а не по instance после обнуления)
            if self._old_logo_name:
                self._delete_old_logo_file = True
            # обнулим instance, чтобы ModelForm точно не сохранил старый путь
            if getattr(self.instance, "logo_file", None):
                self.instance.logo_file = None

        return data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # твои JSON-поля
        instance.publishers = self.cleaned_data['publishers_str']
        instance.developers = self.cleaned_data['developers_str']
        instance.actors = self.cleaned_data['actors_str']

        # проставляем новый webp
        if self._new_logo_file_result:
            name = self._new_logo_file_result.get("name") or self._new_logo_file_result.get("path")
            if name:
                instance.logo_file.name = name

        if commit:
            instance.save()
            self.finalize_logo_cleanup()  # удаляем старый файл после фактического save()

        return instance


    def finalize_logo_cleanup(self):
        if self._delete_old_logo_file and self._old_logo_name:
            try:
                default_storage.delete(self._old_logo_name)
            except Exception:
                pass

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


class FAQInlineForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ["question", "answer"]
        labels = {
            "question": "",
            "answer": "",
        }
        widgets = {
            "question": forms.TextInput(attrs={"placeholder": "Question"}),
            "answer": forms.TextInput(attrs={"placeholder": "Answer"}),
        }