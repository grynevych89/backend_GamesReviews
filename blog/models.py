from django.core.exceptions import FieldError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.sites.models import Site
from pyexpat import model
from tinymce.models import HTMLField
from products.utils.slug import unique_slug
from products.models import Author


class BlogCategory(models.Model):
    name = models.CharField("Name", max_length=150)
    slug = models.SlugField("Slug", max_length=180, unique=True, blank=True)
    seo_title = models.CharField("SEO Title", max_length=255, blank=True, null=True)
    seo_description = models.TextField("SEO Description", blank=True, null=True)

    class Meta:
        verbose_name = "Blog Category"
        verbose_name_plural = "2. Blog Categories"
        ordering = ("name",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug: self.slug = unique_slug(model=BlogCategory, title=self.name, pk=self.pk)
        super().save(*args, **kwargs)


class PublishedManager(models.Manager):
    def get_queryset(self):
        from django.utils import timezone
        return (super().get_queryset()
                .filter(is_active=True, published_at__lte=timezone.now()))


class BlogPost(models.Model):
    title = models.CharField("Title (H1)", max_length=255, help_text="Назва статті (H1)")
    site = models.ForeignKey(Site, on_delete=models.PROTECT, related_name="blog_posts")
    slug = models.SlugField("Slug", max_length=255, blank=True)
    main_image = models.ImageField("Main image (file)", upload_to="blogs/%Y/%m/%d")
    content = HTMLField("Content")
    category = models.ForeignKey(BlogCategory, on_delete=models.PROTECT, verbose_name="Category", null=True, blank=True,)
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, blank=True, related_name="blog_posts")
    seo_title = models.CharField("SEO Title", max_length=255, blank=True, null=True)
    seo_description = models.TextField("SEO Description", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    published_at = models.DateTimeField("Published at", default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Blog"
        verbose_name_plural = "1. Blogs"
        ordering = ("-published_at","-created_at")
        constraints = [models.UniqueConstraint(fields=("site","slug"),
                                               name="uniq_blogpost_slug_per_site")]
        indexes = [models.Index(fields=["site","is_active","published_at"])]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blogs:blog-detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(model=BlogPost, title=self.title, site=self.site, pk=self.pk)
        super().save(*args, **kwargs)
