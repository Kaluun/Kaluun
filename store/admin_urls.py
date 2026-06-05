from django.urls import path
from . import admin_views

app_name = 'gestadmin'

urlpatterns = [
    path('', admin_views.admin_dashboard, name='dashboard'),
    # Commandes
    path('commandes/', admin_views.admin_orders, name='orders'),
    path('commandes/<int:pk>/valider/', admin_views.order_validate, name='order_validate'),
    path('commandes/<int:pk>/rejeter/', admin_views.order_reject, name='order_reject'),
    path('commandes/<int:pk>/statut/', admin_views.order_set_status, name='order_status'),
    path('commandes/<int:pk>/detail/', admin_views.order_detail, name='order_detail'),
    # Produits — CRUD complet
    path('produits/', admin_views.admin_products, name='products'),
    path('produits/ajouter/', admin_views.product_add, name='product_add'),
    path('produits/<int:pk>/modifier/', admin_views.product_edit, name='product_edit'),
    path('produits/<int:pk>/supprimer/', admin_views.product_delete, name='product_delete'),
    path('produits/<int:pk>/toggle/', admin_views.product_toggle, name='product_toggle'),
    # Utilisateurs — CRUD complet
    path('utilisateurs/', admin_views.admin_users, name='users'),
    path('utilisateurs/<int:pk>/modifier/', admin_views.user_edit, name='user_edit'),
    path('utilisateurs/<int:pk>/toggle/', admin_views.user_toggle, name='user_toggle'),
    path('utilisateurs/<int:pk>/supprimer/', admin_views.user_delete, name='user_delete'),
]
