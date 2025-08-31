from django.contrib import admin
from products.models import Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "type")
    list_filter = ("type",)
    search_fields = ("name",)
    ordering = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def changelist_view(self, request, extra_context=None):
        request.GET = request.GET.copy()
        request.GET.pop('site', None)
        request.GET.pop('_changelist_filters', None)
        return super().changelist_view(request, extra_context=extra_context)

