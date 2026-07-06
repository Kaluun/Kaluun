import os
import psycopg2
import psycopg2.extras
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from store.models import (
    Category, Product, Order, OrderItem,
    UserProfile, HeroSlide, Testimonial,
    ContactMessage, NewsletterSubscriber, Notification,
)


class Command(BaseCommand):
    help = 'Importe les données depuis l ancienne DB Render (OLD_DB_URL) vers la DB courante'

    def handle(self, *args, **options):
        old_url = os.environ.get('OLD_DB_URL')
        if not old_url:
            self.stderr.write('Erreur: OLD_DB_URL non défini')
            return

        self.stdout.write(f'Connexion à l ancienne base...')
        src = None
        for sslmode in ['prefer', 'require', 'allow', 'disable']:
            try:
                src = psycopg2.connect(old_url, connect_timeout=15, sslmode=sslmode)
                src.autocommit = True
                self.stdout.write(f'Connecté avec sslmode={sslmode}')
                break
            except Exception as e:
                self.stdout.write(f'sslmode={sslmode} échoué: {e}')
        if src is None:
            self.stderr.write('ECHEC: impossible de se connecter à OLD_DB_URL')
            return

        cur = src.cursor(cursor_factory=psycopg2.extras.DictCursor)
        self.stdout.write(self.style.SUCCESS('Connecté à l ancienne DB Render'))

        with transaction.atomic():
            self._import_categories(cur)
            self._import_products(cur)
            self._import_users(cur)
            self._import_profiles(cur)
            self._import_orders(cur)
            self._import_order_items(cur)
            self._import_slides(cur)
            self._import_testimonials(cur)
            self._import_contacts(cur)
            self._import_newsletters(cur)

        src.close()
        self.stdout.write(self.style.SUCCESS('=== Migration terminée avec succès ==='))

    def _import_categories(self, cur):
        cur.execute('SELECT * FROM store_category ORDER BY id')
        rows = cur.fetchall()
        count = 0
        for r in rows:
            obj, created = Category.objects.update_or_create(
                id=r['id'],
                defaults={
                    'name': r['name'],
                    'slug': r['slug'],
                    'description': r.get('description', ''),
                    'image_url': r.get('image_url', ''),
                }
            )
            if created:
                count += 1
        self.stdout.write(f'  Catégories: {len(rows)} traitées, {count} nouvelles')

    def _import_products(self, cur):
        cur.execute('SELECT * FROM store_product ORDER BY id')
        rows = cur.fetchall()
        count = 0
        for r in rows:
            cat = Category.objects.filter(id=r['category_id']).first() if r.get('category_id') else None
            defaults = {
                'name': r['name'],
                'slug': r['slug'],
                'description': r.get('description', ''),
                'price': r['price'],
                'stock': r.get('stock', 0),
                'unit': r.get('unit', 'kg'),
                'origin': r.get('origin', ''),
                'season': r.get('season', ''),
                'image_url': r.get('image_url', ''),
                'nutritional_info': r.get('nutritional_info', ''),
                'is_featured': r.get('is_featured', False),
                'is_available': r.get('is_available', True),
                'category': cat,
            }
            obj, created = Product.objects.update_or_create(id=r['id'], defaults=defaults)
            if created:
                count += 1
        self.stdout.write(f'  Produits: {len(rows)} traités, {count} nouveaux')

    def _import_users(self, cur):
        cur.execute('SELECT * FROM auth_user ORDER BY id')
        rows = cur.fetchall()
        count = 0
        for r in rows:
            obj, created = User.objects.update_or_create(
                id=r['id'],
                defaults={
                    'password': r['password'],
                    'last_login': r.get('last_login'),
                    'is_superuser': r['is_superuser'],
                    'username': r['username'],
                    'first_name': r.get('first_name', ''),
                    'last_name': r.get('last_name', ''),
                    'email': r.get('email', ''),
                    'is_staff': r['is_staff'],
                    'is_active': r['is_active'],
                    'date_joined': r['date_joined'],
                }
            )
            if created:
                count += 1
        self.stdout.write(f'  Utilisateurs: {len(rows)} traités, {count} nouveaux')

    def _import_profiles(self, cur):
        try:
            cur.execute('SELECT * FROM store_userprofile ORDER BY id')
            rows = cur.fetchall()
            count = 0
            for r in rows:
                user = User.objects.filter(id=r['user_id']).first()
                if not user:
                    continue
                obj, created = UserProfile.objects.update_or_create(
                    user=user,
                    defaults={
                        'phone': r.get('phone', ''),
                        'address': r.get('address', ''),
                        'wilaya': r.get('wilaya', ''),
                    }
                )
                if created:
                    count += 1
            self.stdout.write(f'  Profils: {len(rows)} traités, {count} nouveaux')
        except Exception as e:
            self.stdout.write(f'  Profils: ignorés ({e})')

    def _import_orders(self, cur):
        cur.execute('SELECT * FROM store_order ORDER BY id')
        rows = cur.fetchall()
        count = 0
        for r in rows:
            user = User.objects.filter(id=r['user_id']).first() if r.get('user_id') else None
            defaults = {
                'user': user,
                'full_name': r.get('full_name', ''),
                'email': r.get('email', ''),
                'phone': r.get('phone', ''),
                'delivery_address': r.get('delivery_address', ''),
                'wilaya': r.get('wilaya', ''),
                'notes': r.get('notes', ''),
                'payment_method': r.get('payment_method', 'cash'),
                'transaction_ref': r.get('transaction_ref', ''),
                'total_price': r['total_price'],
                'status': r.get('status', 'pending'),
                'admin_note': r.get('admin_note', ''),
                'cgv_accepted': r.get('cgv_accepted', True),
                'created_at': r['created_at'],
                'updated_at': r.get('updated_at', r['created_at']),
            }
            obj, created = Order.objects.update_or_create(id=r['id'], defaults=defaults)
            if created:
                count += 1
        self.stdout.write(f'  Commandes: {len(rows)} traitées, {count} nouvelles')

    def _import_order_items(self, cur):
        cur.execute('SELECT * FROM store_orderitem ORDER BY id')
        rows = cur.fetchall()
        count = 0
        for r in rows:
            order = Order.objects.filter(id=r['order_id']).first()
            if not order:
                continue
            product = Product.objects.filter(id=r.get('product_id')).first() if r.get('product_id') else None
            defaults = {
                'order': order,
                'product': product,
                'product_name': r.get('product_name', ''),
                'price': r['price'],
                'quantity': r['quantity'],
                'unit': r.get('unit', 'kg'),
            }
            obj, created = OrderItem.objects.update_or_create(id=r['id'], defaults=defaults)
            if created:
                count += 1
        self.stdout.write(f'  Articles commandes: {len(rows)} traités, {count} nouveaux')

    def _import_slides(self, cur):
        try:
            cur.execute('SELECT * FROM store_heroslide ORDER BY id')
            rows = cur.fetchall()
            for r in rows:
                HeroSlide.objects.update_or_create(
                    id=r['id'],
                    defaults={
                        'title': r.get('title', ''),
                        'subtitle': r.get('subtitle', ''),
                        'image_url': r.get('image_url', ''),
                        'is_active': r.get('is_active', True),
                        'order': r.get('order', 0),
                    }
                )
            self.stdout.write(f'  Slides: {len(rows)} traités')
        except Exception as e:
            self.stdout.write(f'  Slides: ignorés ({e})')

    def _import_testimonials(self, cur):
        try:
            cur.execute('SELECT * FROM store_testimonial ORDER BY id')
            rows = cur.fetchall()
            for r in rows:
                Testimonial.objects.update_or_create(
                    id=r['id'],
                    defaults={
                        'name': r.get('name', ''),
                        'content': r.get('content', ''),
                        'rating': r.get('rating', 5),
                        'is_active': r.get('is_active', True),
                        'avatar_url': r.get('avatar_url', ''),
                    }
                )
            self.stdout.write(f'  Témoignages: {len(rows)} traités')
        except Exception as e:
            self.stdout.write(f'  Témoignages: ignorés ({e})')

    def _import_contacts(self, cur):
        try:
            cur.execute('SELECT * FROM store_contactmessage ORDER BY id')
            rows = cur.fetchall()
            for r in rows:
                ContactMessage.objects.update_or_create(
                    id=r['id'],
                    defaults={
                        'name': r.get('name', ''),
                        'email': r.get('email', ''),
                        'subject': r.get('subject', ''),
                        'message': r.get('message', ''),
                        'created_at': r.get('created_at'),
                    }
                )
            self.stdout.write(f'  Messages contact: {len(rows)} traités')
        except Exception as e:
            self.stdout.write(f'  Messages contact: ignorés ({e})')

    def _import_newsletters(self, cur):
        try:
            cur.execute('SELECT * FROM store_newslettersubscriber ORDER BY id')
            rows = cur.fetchall()
            for r in rows:
                NewsletterSubscriber.objects.update_or_create(
                    email=r['email'],
                    defaults={
                        'name': r.get('name', ''),
                        'subscribed_at': r.get('subscribed_at'),
                    }
                )
            self.stdout.write(f'  Newsletter: {len(rows)} traités')
        except Exception as e:
            self.stdout.write(f'  Newsletter: ignorés ({e})')
