from django import forms
from .models import Product
from .widgets import StarRatingWidget, ScreenshotsWidget


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
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
        }
        labels = {
            "screenshots": "",
        }

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