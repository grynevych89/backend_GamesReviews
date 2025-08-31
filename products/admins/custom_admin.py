from typing import Optional
from urllib.parse import parse_qs
from django.core.exceptions import FieldError
from django.contrib.admin import AdminSite
from django.contrib.sites.models import Site
from products.constants import IGNORED_MODELS


__all__ = ["SiteAwareAdminSite"]


class SiteAwareAdminSite(AdminSite):
    site_header = "Product Reviews Admin"
    site_title = "Product Reviews"
    index_title = "Панель управління"

    @staticmethod
    def _current_model_name(request) -> Optional[str]:
        """
        Возвращает имя модели из admin url_name.
        Пример: products_product_changelist → 'product'.
        """
        rm = getattr(request, "resolver_match", None)
        if rm and rm.url_name:
            parts = rm.url_name.split("_")
            if len(parts) >= 2:
                return parts[1]
        return None

    @staticmethod
    def _get_site_id_from_request(request) -> Optional[int]:
        """
        Определяет выбранный site из querystring/сессии. Поддерживает site=all.
        """
        site_param = request.GET.get("site")
        if site_param == "all":
            return None
        if site_param:
            return int(site_param) if site_param.isdigit() else None

        # поддержка "_changelist_filters" (возврат со страницы изменения)
        filters = request.GET.get("_changelist_filters")
        if filters:
            parsed = parse_qs(filters)
            s = parsed.get("site", [None])[0]
            if s and s.isdigit():
                return int(s)

        return None

    def each_context(self, request):
        context = super().each_context(request)

        current_model = self._current_model_name(request)
        if current_model in IGNORED_MODELS:
            context["current_site_id"] = None
            context["site_list"] = []
            return context

        site_id = self._get_site_id_from_request(request)

        if site_id is None:
            request.session.pop("current_site_id", None)
        else:
            request.session["current_site_id"] = site_id

        context["current_site_id"] = request.session.get("current_site_id")
        context["site_list"] = Site.objects.all().order_by("id")
        context["admin_ns"] = self.name
        return context

    def get_app_list(self, request, app_label=None):
        current_model = self._current_model_name(request)
        if current_model in IGNORED_MODELS:
            return super().get_app_list(request, app_label)

        app_list = super().get_app_list(request, app_label)
        site_id = request.GET.get("site") or request.session.get("current_site_id")
        if not site_id:
            return app_list

        def model_is_visible(model) -> bool:
            try:
                has_site_field = any(f.name == "site" for f in model._meta.fields)
                if not has_site_field:
                    return True

                if model.objects.filter(site_id=site_id).exists():
                    return True

                ma = self._registry.get(model)
                if ma:
                    perms = ma.get_model_perms(request) or {}
                    if perms.get("add") or perms.get("change") or perms.get("view"):
                        return True

                return False
            except Exception:
                return True

        for app in app_list:
            app["models"] = [m for m in app["models"] if model_is_visible(m["model"])]

        return app_list
