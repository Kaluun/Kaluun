from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('store.urls')),
    path('comptes/', include('accounts.urls')),
    path('gestion/', include('store.admin_urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = "Kaluun Administration"
admin.site.site_title = "Kaluun Admin"
admin.site.index_title = "Gestion de la Poissonnerie Kaluun"
