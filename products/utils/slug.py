from slugify import slugify

def unique_slug(*, model, title, site, pk=None, slug_field="slug"):
    base = slugify(title) or "item"
    qs = model.objects.filter(site=site, **{f"{slug_field}__startswith": base})
    if pk:
        qs = qs.exclude(pk=pk)

    if not qs.filter(**{slug_field: base}).exists():
        return base

    i = 2
    while True:
        candidate = f"{base}-{i}"
        if not qs.filter(**{slug_field: candidate}).exists():
            return candidate
        i += 1
