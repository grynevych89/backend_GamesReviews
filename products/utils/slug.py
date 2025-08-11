from slugify import slugify


def unique_slug_for_site(model, site, title, pk=None):
    base = slugify(title); s = base; i = 1
    qs = model.objects.filter(site=site, slug=s)
    if pk: qs = qs.exclude(pk=pk)
    while qs.exists():
        i += 1; s = f"{base}-{i}"
        qs = model.objects.filter(site=site, slug=s)
        if pk: qs = qs.exclude(pk=pk)
    return s