from django.contrib.admin import AdminSite
from django.contrib.sites.models import Site

class SiteAwareAdminSite(AdminSite):
    site_header = "Product Reviews Admin"
    site_title = "Product Reviews"
    index_title = "Панель управління"

    def each_context(self, request):
        context = super().each_context(request)
        site_id = request.GET.get("site")

        context["current_site_id"] = site_id or ""
        context["site_list"] = Site.objects.all()
        return context

    def get_app_list(self, request, app_label=None):
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
