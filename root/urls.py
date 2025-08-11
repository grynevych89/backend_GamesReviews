from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static
from products.admins.admin import custom_admin_site
from django.shortcuts import redirect


urlpatterns = [
    path('admin/', custom_admin_site.urls),
    path('tinymce/', include('tinymce.urls')),
    path('api/', include('products.api.urls_api')),
    path('', lambda request: redirect('/api/', permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)