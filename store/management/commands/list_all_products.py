from django.core.management.base import BaseCommand
from store.models import Product


class Command(BaseCommand):
    help = 'Liste tous les produits de la DB courante'

    def handle(self, *args, **options):
        all_prods = Product.objects.all().order_by('id')
        self.stdout.write(f'=== TOTAL: {all_prods.count()} produits ===')
        for p in all_prods:
            dispo = 'ACTIF' if p.is_available else 'INACTIF'
            self.stdout.write(f'#{p.id} [{dispo}] {p.name} — {p.price} FDJ — cat:{p.category_id}')
