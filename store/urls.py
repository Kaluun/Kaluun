from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('a-propos/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('produits/', views.product_list, name='product_list'),
    path('produits/categorie/<slug:slug>/', views.products_by_category, name='products_by_category'),
    path('produits/<slug:slug>/', views.product_detail, name='product_detail'),
    path('panier/', views.cart_detail, name='cart_detail'),
    path('panier/json/', views.cart_json, name='cart_json'),
    path('panier/ajouter/<int:product_id>/', views.cart_add, name='cart_add'),
    path('panier/retirer/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('panier/modifier/<int:product_id>/', views.cart_update, name='cart_update'),
    path('panier/vider/', views.cart_clear, name='cart_clear'),
    path('commander/', views.checkout, name='checkout'),
    path('commande/<int:pk>/confirmation/', views.order_confirmation, name='order_confirmation'),
    path('notifications/<int:pk>/lire/', views.notification_read, name='notification_read'),
    path('notifications/tout-lire/', views.notifications_read_all, name='notifications_read_all'),
]
