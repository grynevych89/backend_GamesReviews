from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from products.admin import custom_admin_site

urlpatterns = [
    path('admin/', custom_admin_site.urls),
    path('tinymce/', include('tinymce.urls')),
    path('api/', include('products.api.urls_api')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)