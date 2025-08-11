from django.contrib.sites.models import Site
from django.conf import settings

def resolve_site_by_host(request):
    host = request.get_host().split(':', 1)[0]  # без порта
    site = Site.objects.filter(domain__iexact=host).first()
    if site:
        return site
    # запасной вариант — дефолтный SITE_ID (на всякий случай)
    default_id = getattr(settings, "SITE_ID", None)
    return Site.objects.filter(id=default_id).first() or Site.objects.first()
