from django.contrib.sites.models import Site
from django.utils.text import slugify

def unique_slug(model, title, *, site=None, pk=None, slug_field="slug"):
    if site is None:
        site = Site.objects.get_current()

    base = slugify(title) or "item"
    slug = base
    i = 2

    qs = model._default_manager.all()
    # если у модели есть FK site — фильтруем
    if any(f.name == "site" for f in model._meta.fields):
        qs = qs.filter(site=site)
    if pk:
        qs = qs.exclude(pk=pk)

    while qs.filter(**{slug_field: slug}).exists():
        slug = f"{base}-{i}"
        i += 1
    return slug
