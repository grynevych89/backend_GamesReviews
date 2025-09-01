from django.contrib import admin

class AuthorProxyAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
