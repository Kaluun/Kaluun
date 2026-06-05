"""
KALUUN — Système de notifications email
Emails en texte brut = jamais dans les spams
"""
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

ADMIN_EMAIL = getattr(settings, 'ADMIN_EMAIL', 'kaluunexpresse@gmail.com')
SITE_NAME   = 'KALUUN'
SITE_URL    = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')


def _items_text(order):
    """Liste des articles en texte brut."""
    lines = []
    for it in order.items.all():
        lines.append(f"  - {it.product_name} x{it.quantity}{it.unit} = {int(it.price * it.quantity):,} FDJ")
    lines.append(f"\n  TOTAL : {int(order.total_price):,} FDJ")
    return "\n".join(lines)


def _send(subject, to_email, body):
    """Envoie un email en texte brut pur — ne va jamais en spam."""
    if not to_email:
        return
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=f'KALUUN Djibouti <{ADMIN_EMAIL}>',
            recipient_list=[to_email],
            fail_silently=False,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f'Email error to {to_email}: {e}')


def _get_client_email(order):
    """Recupere l email du client depuis la commande ou son compte."""
    return order.email or (order.user.email if order.user else None)


# ══════════════════════════════════════════════════
#  1. NOUVELLE COMMANDE
# ══════════════════════════════════════════════════
def notify_new_order(order):
    articles = _items_text(order)

    # --- Email Admin ---
    _send(
        subject=f'KALUUN - Nouvelle commande #{order.pk} de {order.full_name}',
        to_email=ADMIN_EMAIL,
        body=f"""Bonjour,

Une nouvelle commande a ete passee sur KALUUN.

=== DETAILS COMMANDE #{order.pk} ===

Client     : {order.full_name}
Telephone  : {order.phone}
Email      : {order.email or 'Non renseigne'}
Adresse    : {order.delivery_address}, {order.wilaya}
Paiement   : {order.get_payment_method_display()}
{f'Reference  : {order.transaction_ref}' if order.transaction_ref else ''}
Date       : {order.created_at.strftime('%d/%m/%Y a %H:%M')}

=== ARTICLES ===
{articles}

=== ACTION REQUISE ===
Validez ou rejetez cette commande sur :
{SITE_URL}/gestion/commandes/

---
KALUUN - Poissons frais Djibouti
Tel : +253 77 15 07 89
"""
    )

    # --- Email Client ---
    client_email = _get_client_email(order)
    if client_email:
        _send(
            subject=f'KALUUN - Votre commande #{order.pk} a ete recue',
            to_email=client_email,
            body=f"""Bonjour {order.full_name},

Merci pour votre commande sur KALUUN !

Votre commande #{order.pk} a bien ete enregistree et est en cours de validation par notre equipe.

=== RESUME DE VOTRE COMMANDE ===
{articles}

Livraison a : {order.delivery_address}, {order.wilaya}
Paiement   : {order.get_payment_method_display()}

Notre equipe vous contactera au {order.phone} dans les 30 minutes pour confirmer la livraison.

Pour toute question :
Email : {ADMIN_EMAIL}
Tel   : +253 77 15 07 89

Merci de votre confiance !
L'equipe KALUUN - Djibouti
"""
        )


# ══════════════════════════════════════════════════
#  2. COMMANDE CONFIRMEE
# ══════════════════════════════════════════════════
def notify_order_confirmed(order):
    client_email = _get_client_email(order)
    if not client_email:
        return
    _send(
        subject=f'KALUUN - Commande #{order.pk} confirmee',
        to_email=client_email,
        body=f"""Bonjour {order.full_name},

Bonne nouvelle ! Votre commande #{order.pk} a ete confirmee par notre equipe.

Nous preparons maintenant votre selection de poissons frais avec soin.

Details :
- Montant total : {int(order.total_price):,} FDJ
- Livraison dans les 24 heures
{f'- Note de notre equipe : {order.admin_note}' if order.admin_note else ''}

Notre livreur vous appellera au {order.phone} avant de passer.

L'equipe KALUUN - Djibouti
Tel : +253 77 15 07 89
"""
    )


# ══════════════════════════════════════════════════
#  3. EN PREPARATION
# ══════════════════════════════════════════════════
def notify_order_processing(order):
    client_email = _get_client_email(order)
    if not client_email:
        return
    _send(
        subject=f'KALUUN - Commande #{order.pk} en preparation',
        to_email=client_email,
        body=f"""Bonjour {order.full_name},

Votre commande #{order.pk} est actuellement en preparation.

Nos equipes decoupent et preparent vos poissons frais. La chaine du froid est maintenue entre 0 et 4C.

Livraison prevue a : {order.delivery_address}, {order.wilaya}

L'equipe KALUUN - Djibouti
Tel : +253 77 15 07 89
"""
    )


# ══════════════════════════════════════════════════
#  4. EN LIVRAISON
# ══════════════════════════════════════════════════
def notify_order_delivering(order):
    client_email = _get_client_email(order)
    if not client_email:
        return
    _send(
        subject=f'KALUUN - Votre commande #{order.pk} est en route',
        to_email=client_email,
        body=f"""Bonjour {order.full_name},

Votre commande #{order.pk} est en cours de livraison !

Notre livreur est en route vers :
{order.delivery_address}, {order.wilaya}

Restez disponible au {order.phone}, il peut vous appeler pour confirmation.

L'equipe KALUUN - Djibouti
Tel : +253 77 15 07 89
"""
    )


# ══════════════════════════════════════════════════
#  5. LIVREE
# ══════════════════════════════════════════════════
def notify_order_delivered(order):
    client_email = _get_client_email(order)
    if client_email:
        _send(
            subject=f'KALUUN - Commande #{order.pk} livree - Bon appetit !',
            to_email=client_email,
            body=f"""Bonjour {order.full_name},

Votre commande #{order.pk} a ete livree avec succes.

Montant paye : {int(order.total_price):,} FDJ

Nous esperons que vos poissons frais vous regaleront !
N'hesitez pas a recomander sur KALUUN.

L'equipe KALUUN - Djibouti
Tel : +253 77 15 07 89
Email : {ADMIN_EMAIL}
"""
        )

    # Notifier admin aussi
    _send(
        subject=f'KALUUN - Commande #{order.pk} livree ({order.full_name})',
        to_email=ADMIN_EMAIL,
        body=f"""Commande #{order.pk} marquee comme livree.

Client  : {order.full_name}
Tel     : {order.phone}
Montant : {int(order.total_price):,} FDJ
"""
    )


# ══════════════════════════════════════════════════
#  6. REJETEE / ANNULEE
# ══════════════════════════════════════════════════
def notify_order_rejected(order):
    client_email = _get_client_email(order)
    if not client_email:
        return
    reason = order.admin_note or 'Contactez-nous pour plus d\'informations.'
    _send(
        subject=f'KALUUN - Information sur votre commande #{order.pk}',
        to_email=client_email,
        body=f"""Bonjour {order.full_name},

Nous sommes desoles, votre commande #{order.pk} n'a pas pu etre confirmee.

Motif : {reason}

Pour toute question ou pour repasser une commande :
Email : {ADMIN_EMAIL}
Tel   : +253 77 15 07 89

Nous vous remercions de votre comprehension.
L'equipe KALUUN - Djibouti
"""
    )


# ══════════════════════════════════════════════════
#  DISPATCH selon le statut
# ══════════════════════════════════════════════════
def notify_status_change(order, new_status):
    dispatch = {
        'confirmed':  notify_order_confirmed,
        'processing': notify_order_processing,
        'delivering': notify_order_delivering,
        'delivered':  notify_order_delivered,
        'rejected':   notify_order_rejected,
        'cancelled':  notify_order_rejected,
    }
    fn = dispatch.get(new_status)
    if fn:
        fn(order)


# ══════════════════════════════════════════════════
#  RAPPEL admin commandes en attente
# ══════════════════════════════════════════════════
def notify_admin_pending_orders(count, orders):
    lines = []
    for o in orders:
        lines.append(f"  #{o.pk} - {o.full_name} - {int(o.total_price):,} FDJ - {o.created_at.strftime('%d/%m %H:%M')}")

    _send(
        subject=f'KALUUN - {count} commande(s) en attente de validation',
        to_email=ADMIN_EMAIL,
        body=f"""{count} commande(s) attendent votre validation :

{chr(10).join(lines)}

Validez sur : {SITE_URL}/gestion/commandes/?status=pending

---
KALUUN - Djibouti
"""
    )
