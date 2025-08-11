from django.contrib import admin
from django.contrib.sites.models import Site
from .custom_admin import SiteAwareAdminSite
from products.models import Product, Comment, Category, Author
from .product_admin import ProductAdmin
from .comment_admin import CommentAdmin
from .category_admin import CategoryAdmin

class CustomSiteAdmin(admin.ModelAdmin):
    list_display = ('domain', 'name')
    search_fields = ('domain', 'name')

custom_admin_site = SiteAwareAdminSite(name="custom_admin")
custom_admin_site.register(Site, CustomSiteAdmin)

custom_admin_site.register(Product, ProductAdmin)
custom_admin_site.register(Comment, CommentAdmin)
custom_admin_site.register(Category, CategoryAdmin)
custom_admin_site.register(Author, admin.ModelAdmin)

custom_admin_site.site_header = "Reviews Admin"
custom_admin_site.site_title = "Reviews Admin"
custom_admin_site.index_title = "Панель Управління"
