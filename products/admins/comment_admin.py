from django.contrib import admin
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.http import QueryDict
from django.shortcuts import redirect
from products.models import Comment
from .site_filtering import redirect_back_to_filtered_list

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("product", "text", "name", "status", "email", "created_at")
    list_filter = ("status", "created_at", ("product__site", RelatedOnlyFieldListFilter))
    search_fields = ("name", "email", "text")
    list_editable = ("status",)
    save_on_top = True

    def changelist_view(self, request, extra_context=None):
        site = request.GET.get("site")
        already = "product__site__id__exact" in request.GET
        if site and site.isdigit() and not already:
            q = QueryDict(mutable=True)
            q["product__site__id__exact"] = site
            return redirect(f"{request.path}?{q.urlencode()}")
        extra_context = extra_context or {}
        extra_context["current_site_id"] = request.GET.get("product__site__id__exact", "")
        return super().changelist_view(request, extra_context=extra_context)

    def response_post_save_add(self, request, obj):
        return redirect_back_to_filtered_list(
            request, 'admin:products_comment_changelist', param='product__site__id__exact'
        ) or super().response_post_save_add(request, obj)

    def response_post_save_change(self, request, obj):
        return redirect_back_to_filtered_list(
            request, 'admin:products_comment_changelist', param='product__site__id__exact'
        ) or super().response_post_save_change(request, obj)
