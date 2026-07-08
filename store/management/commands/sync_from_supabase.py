import os
import psycopg2
import psycopg2.extras
from django.core.management.base import BaseCommand
from store.models import Category, Product


class Command(BaseCommand):
    help = 'Copie les produits/catégories de Supabase vers la DB courante'

    def handle(self, *args, **options):
        supabase_url = os.environ.get('SUPABASE_URL')
        if not supabase_url:
            self.stdout.write('SUPABASE_URL non défini — sync ignoré')
            return

        self.stdout.write('Connexion à Supabase...')
        try:
            src = psycopg2.connect(supabase_url, connect_timeout=15, sslmode='require')
            src.autocommit = True
            cur = src.cursor(cursor_factory=psycopg2.extras.DictCursor)
            self.stdout.write(self.style.SUCCESS('Connecté'))
        except Exception as e:
            self.stdout.write(f'ERREUR connexion Supabase: {e}')
            return

        # Catégories
        cur.execute('SELECT * FROM store_category ORDER BY id')
        cats = cur.fetchall()
        for r in cats:
            Category.objects.update_or_create(
                id=r['id'],
                defaults={
                    'name': r['name'],
                    'slug': r['slug'],
                    'description': r.get('description', ''),
                    'image_url': r.get('image_url', ''),
                }
            )
        self.stdout.write(f'  Catégories sync: {len(cats)}')

        # Produits
        cur.execute('SELECT * FROM store_product ORDER BY id')
        prods = cur.fetchall()
        count = 0
        for r in prods:
            cat = Category.objects.filter(id=r['category_id']).first() if r.get('category_id') else None
            _, created = Product.objects.update_or_create(
                id=r['id'],
                defaults={
                    'name': r['name'],
                    'slug': r['slug'],
                    'description': r.get('description', ''),
                    'price': r['price'],
                    'stock': r.get('stock', 50),
                    'unit': r.get('unit', 'kg'),
                    'origin': r.get('origin', 'Djibouti'),
                    'season': r.get('season', ''),
                    'image_url': r.get('image_url', ''),
                    'nutritional_info': r.get('nutritional_info', ''),
                    'is_featured': r.get('is_featured', False),
                    'is_available': r.get('is_available', True),
                    'category': cat,
                }
            )
            if created:
                count += 1
        self.stdout.write(f'  Produits sync: {len(prods)} ({count} nouveaux)')
        self.stdout.write(self.style.SUCCESS('=== Sync Supabase → Render terminé ==='))
        src.close()
