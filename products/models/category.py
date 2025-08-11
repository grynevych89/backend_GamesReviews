from django.db import models
from products.constants import PRODUCT_TYPE_CHOICES

class Category(models.Model):
    name = models.CharField("Category Name", max_length=100)
    type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPE_CHOICES,
        default='game',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"

    def __str__(self):
        return self.name


class Author(models.Model):
    name = models.CharField("Ім’я автора", max_length=100, unique=True)

    def __str__(self):
        return self.name


class StorePlatform(models.Model):
    name = models.CharField("Platform Name", max_length=100, unique=True)
    icon_url = models.URLField("Icon URL", blank=True, help_text="Посилання на іконку платформи")
    store_url = models.URLField("Store URL", blank=True, help_text="Посилання на магазин або гру")

    def __str__(self):
        return self.name
