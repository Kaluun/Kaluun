from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from store import views as store_views
from store.sitemaps import StaticViewSitemap, ProductSitemap, CategorySitemap

sitemaps = {
    'static': StaticViewSitemap,
    'products': ProductSitemap,
    'categories': CategorySitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', store_views.robots_txt, name='robots_txt'),
    path('googlee3aa1616e98b6e27.html', store_views.google_site_verification, name='google_site_verification'),
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
