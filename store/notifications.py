"""
KALUUN — Notifications dans le dashboard (en plus des emails)
"""
from django.contrib.auth.models import User
from .models import Notification


def _create(recipient, title, message='', link='', icon='fa-bell'):
    if not recipient:
        return
    Notification.objects.create(recipient=recipient, title=title, message=message, link=link, icon=icon)


def push_to_admins(title, message='', link='', icon='fa-bell'):
    for admin in User.objects.filter(is_staff=True):
        _create(admin, title, message, link, icon)


def push_new_order(order):
    push_to_admins(
        title=f'Nouvelle commande #{order.pk}',
        message=f'{order.full_name} — {int(order.total_price):,} FDJ'.replace(',', ' '),
        link='/gestion/commandes/?status=pending',
        icon='fa-receipt',
    )


_STATUS_LABELS = {
    'confirmed':  ('Commande confirmée', 'fa-check-circle'),
    'processing': ('Commande en préparation', 'fa-box-open'),
    'delivering': ('Commande en livraison', 'fa-truck'),
    'delivered':  ('Commande livrée', 'fa-flag-checkered'),
    'rejected':   ('Commande rejetée', 'fa-times-circle'),
    'cancelled':  ('Commande annulée', 'fa-times-circle'),
}


def push_status_change(order, new_status):
    if not order.user:
        return
    label, icon = _STATUS_LABELS.get(new_status, ('Mise à jour de votre commande', 'fa-bell'))
    _create(
        order.user,
        title=f'{label} — #{order.pk}',
        message=f'{int(order.total_price):,} FDJ'.replace(',', ' '),
        link='/comptes/tableau-de-bord/',
        icon=icon,
    )
