from django.apps import AppConfig

class PagesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pages"

class ReferencesConfig(AppConfig):
    name = "pages"            # ← python-путь пакета
    label = "references"      # ← уникальный ярлык блока
    verbose_name = "Pages"