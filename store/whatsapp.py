"""
KALUUN — WhatsApp Cloud API (Meta)
Envoie des messages automatiques aux clients et à l'admin.
"""
import logging
import re
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

GRAPH_URL = "https://graph.facebook.com/v19.0/{phone_id}/messages"

_STATUS_MESSAGES = {
    'confirmed':  ("✅ Confirmée",  "Votre commande est confirmée ! Notre livreur vous appellera bientôt."),
    'processing': ("📦 En préparation", "Votre commande est en cours de préparation."),
    'delivering': ("🛵 En livraison", "Votre commande est en route ! Le livreur arrive."),
    'delivered':  ("🎉 Livrée", "Commande livrée avec succès. Merci de faire confiance à KALUUN !"),
    'rejected':   ("❌ Rejetée", "Votre commande n'a pas pu être traitée. Contactez-nous pour plus d'infos."),
    'cancelled':  ("🚫 Annulée", "Votre commande a été annulée."),
}


def _clean_phone(phone: str) -> str:
    """Normalise un numéro en format international sans '+' (ex: 25377123456)."""
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 8:
        return '253' + digits
    if digits.startswith('00253'):
        return digits[2:]
    if digits.startswith('253') and len(digits) == 11:
        return digits
    return digits


def _send(to: str, template_name: str, params: list[str]) -> bool:
    token = getattr(settings, 'WHATSAPP_TOKEN', '')
    phone_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '')
    if not token or not phone_id:
        logger.warning("WhatsApp : WHATSAPP_TOKEN ou WHATSAPP_PHONE_NUMBER_ID manquant.")
        return False

    components = [
        {
            "type": "body",
            "parameters": [{"type": "text", "text": str(p)} for p in params],
        }
    ]

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "fr"},
            "components": components,
        },
    }

    try:
        r = requests.post(
            GRAPH_URL.format(phone_id=phone_id),
            json=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=8,
        )
        if r.ok:
            logger.info("WhatsApp envoyé → %s (%s)", to, template_name)
            return True
        logger.error("WhatsApp erreur %s : %s", r.status_code, r.text)
    except Exception as e:
        logger.error("WhatsApp exception : %s", e)
    return False


# ── API publique ──────────────────────────────────────────────────────

def notify_new_order(order):
    """Notifie le client (confirmation) + l'admin (nouvelle commande)."""
    customer_phone = _clean_phone(order.phone)
    items_summary = ", ".join(
        f"{i.product_name} x{i.quantity}{i.unit}"
        for i in order.items.all()
    )

    # → Client : confirmation de commande
    _send(
        to=customer_phone,
        template_name=getattr(settings, 'WA_TPL_ORDER_CONFIRM', 'kaluun_nouvelle_commande'),
        params=[
            order.full_name.split()[0],          # {{1}} prénom
            str(order.pk),                        # {{2}} numéro commande
            f"{int(order.total_price):,}".replace(',', ' '),  # {{3}} montant
            items_summary,                        # {{4}} articles
        ],
    )

    # → Admin : alerte nouvelle commande
    admin_phone = getattr(settings, 'WHATSAPP_ADMIN_PHONE', '')
    if admin_phone:
        _send(
            to=_clean_phone(admin_phone),
            template_name=getattr(settings, 'WA_TPL_ADMIN_NEW_ORDER', 'kaluun_admin_nouvelle_commande'),
            params=[
                str(order.pk),
                order.full_name,
                f"{int(order.total_price):,}".replace(',', ' '),
                order.phone,
            ],
        )


def notify_status_change(order, new_status):
    """Notifie le client d'un changement de statut."""
    if not order.phone:
        return
    label, detail = _STATUS_MESSAGES.get(new_status, ("Mise à jour", "Votre commande a été mise à jour."))
    _send(
        to=_clean_phone(order.phone),
        template_name=getattr(settings, 'WA_TPL_STATUS_CHANGE', 'kaluun_statut_commande'),
        params=[
            str(order.pk),   # {{1}} numéro commande
            label,           # {{2}} statut
            detail,          # {{3}} message
        ],
    )
