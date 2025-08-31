from django.contrib import admin
from django.contrib.sites.models import Site

from blog.admin import BlogCategoryAdmin, BlogPostAdmin
from blog.models import BlogCategory, BlogPost
from .custom_admin import SiteAwareAdminSite
from products.models import Product, Comment, Category, Author, Poll
from .poll_admin import PollAdmin
from .product_admin import ProductAdmin
from .comment_admin import CommentAdmin
from .category_admin import CategoryAdmin

from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

class CustomSiteAdmin(admin.ModelAdmin):
    list_display = ('domain', 'name')
    search_fields = ('domain', 'name')

custom_admin_site = SiteAwareAdminSite(name="custom_admin")
custom_admin_site.register(Site, CustomSiteAdmin)

custom_admin_site.register(Product, ProductAdmin)
custom_admin_site.register(Comment, CommentAdmin)
custom_admin_site.register(Category, CategoryAdmin)
custom_admin_site.register(Author, admin.ModelAdmin)
custom_admin_site.register(Poll, PollAdmin)

custom_admin_site.register(BlogCategory, BlogCategoryAdmin)
custom_admin_site.register(BlogPost, BlogPostAdmin)


custom_admin_site.site_header = "Reviews Admin"
custom_admin_site.site_title = "Reviews Admin"
custom_admin_site.index_title = "Панель Управління"

class SuperuserOnlyAdminMixin:
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class CustomUserAdmin(SuperuserOnlyAdminMixin, UserAdmin):
    pass


class CustomGroupAdmin(SuperuserOnlyAdminMixin, GroupAdmin):
    pass


for model in (User, Group):
    try:
        admin.site.unregister(model)
    except admin.sites.NotRegistered:
        pass

# зарегистрировать только в custom_admin_site
custom_admin_site.register(User, CustomUserAdmin)
custom_admin_site.register(Group, CustomGroupAdmin)