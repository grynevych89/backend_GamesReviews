from django.contrib import admin
from products.models import Poll, PollOption

class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 4
    verbose_name = "Вариант"
    verbose_name_plural = "Варианты ответа"

@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ("question", "product")
    inlines = [PollOptionInline]