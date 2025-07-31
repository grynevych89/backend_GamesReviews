from django.contrib.admin import AdminSite
from django.contrib.sites.models import Site

from django.contrib.admin import AdminSite
from django.contrib.sites.models import Site
from urllib.parse import parse_qs

class SiteAwareAdminSite(AdminSite):
    site_header = "Product Reviews Admin"
    site_title = "Product Reviews"
    index_title = "Панель управління"

    def each_context(self, request):
        context = super().each_context(request)

        # Определяем модель по URL
        resolver = getattr(request, "resolver_match", None)
        current_model = None
        if resolver and resolver.url_name:
            current_model = resolver.url_name.split("_")[0]  # product / category / ...

        # 🔹 Категории полностью игнорируют мультисайт
        if current_model == "category":
            context["current_site_id"] = None
            context["site_list"] = []  # ❗ Селектор сайтов не показываем
            return context

        # 🔹 Логика мультисайтов для продуктов
        site_id = request.GET.get("site")

        # "-- Все сайты --" очищает сессию
        if site_id == "" or site_id is None:
            request.session.pop("current_site_id", None)
        else:
            # Если прямого параметра нет — ищем в _changelist_filters
            if not site_id and "_changelist_filters" in request.GET:
                filters = request.GET["_changelist_filters"]
                parsed = parse_qs(filters)
                site_id = parsed.get("site", [None])[0]

            if site_id:
                request.session["current_site_id"] = site_id

        context["current_site_id"] = request.session.get("current_site_id")
        context["site_list"] = Site.objects.all()
        return context

    def get_app_list(self, request, app_label=None):
        resolver = getattr(request, "resolver_match", None)
        current_model = None
        if resolver and resolver.url_name:
            current_model = resolver.url_name.split("_")[0]

        # 🔹 Для категорий возвращаем стандартный список приложений
        if current_model == "category":
            return super().get_app_list(request, app_label)

        # 🔹 Для остальных моделей учитываем site
        app_list = super().get_app_list(request, app_label)
        site_id = request.GET.get("site") or request.session.get("current_site_id")

        if not site_id:
            return app_list

        def model_has_data(model):
            try:
                if hasattr(model, "site"):
                    return model.objects.filter(site__id=site_id).exists()
                return True
            except Exception:
                return True

        for app in app_list:
            app["models"] = [
                m for m in app["models"]
                if model_has_data(m["model"])
            ]
        return app_list
