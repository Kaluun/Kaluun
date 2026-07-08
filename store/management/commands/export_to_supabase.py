import os
import psycopg2
import psycopg2.extras
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from store.models import (
    Category, Product, Order, OrderItem,
    UserProfile, HeroSlide, Testimonial,
    ContactMessage, NewsletterSubscriber,
)


class Command(BaseCommand):
    help = 'Exporte toutes les données Django vers Supabase via SUPABASE_URL'

    def handle(self, *args, **options):
        supabase_url = os.environ.get('SUPABASE_URL')
        if not supabase_url:
            self.stdout.write('SUPABASE_URL non défini — export ignoré')
            return

        self.stdout.write('Connexion à Supabase...')
        try:
            dst = psycopg2.connect(supabase_url, connect_timeout=15, sslmode='require')
            dst.autocommit = False
            cur = dst.cursor()
            self.stdout.write(self.style.SUCCESS('Connecté à Supabase'))
        except Exception as e:
            self.stdout.write(f'ERREUR connexion Supabase: {e}')
            return

        try:
            self._export_categories(cur)
            self._export_products(cur)
            self._export_users(cur)
            self._export_profiles(cur)
            self._export_orders(cur)
            self._export_order_items(cur)
            self._export_slides(cur)
            self._export_testimonials(cur)
            self._export_contacts(cur)
            self._export_newsletters(cur)
            dst.commit()
            self.stdout.write(self.style.SUCCESS('=== Export Supabase terminé avec succès ==='))
        except Exception as e:
            dst.rollback()
            self.stdout.write(f'ERREUR pendant export: {e}')
        finally:
            dst.close()

    def _upsert(self, cur, table, cols, values, conflict_col='id'):
        placeholders = ', '.join(['%s'] * len(values))
        col_names = ', '.join(f'"{c}"' for c in cols)
        updates = ', '.join(f'"{c}"=EXCLUDED."{c}"' for c in cols if c != conflict_col)
        sql = f'''
            INSERT INTO {table} ({col_names}) VALUES ({placeholders})
            ON CONFLICT ("{conflict_col}") DO UPDATE SET {updates}
        '''
        cur.execute(sql, values)

    def _export_categories(self, cur):
        qs = Category.objects.all()
        for obj in qs:
            self._upsert(cur, 'store_category',
                ['id', 'name', 'slug', 'description', 'image_url'],
                [obj.id, obj.name, obj.slug,
                 getattr(obj, 'description', ''), getattr(obj, 'image_url', '')])
        self.stdout.write(f'  Catégories: {qs.count()}')

    def _export_products(self, cur):
        qs = Product.objects.all()
        for obj in qs:
            self._upsert(cur, 'store_product',
                ['id', 'name', 'slug', 'description', 'price', 'stock', 'unit',
                 'origin', 'season', 'image_url', 'nutritional_info',
                 'is_featured', 'is_available', 'category_id'],
                [obj.id, obj.name, obj.slug, obj.description, obj.price,
                 obj.stock, obj.unit, obj.origin, getattr(obj, 'season', ''),
                 getattr(obj, 'image_url', ''), getattr(obj, 'nutritional_info', ''),
                 obj.is_featured, obj.is_available,
                 obj.category_id if obj.category_id else None])
        self.stdout.write(f'  Produits: {qs.count()}')

    def _export_users(self, cur):
        qs = User.objects.all()
        for obj in qs:
            self._upsert(cur, 'auth_user',
                ['id', 'password', 'last_login', 'is_superuser', 'username',
                 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'date_joined'],
                [obj.id, obj.password, obj.last_login, obj.is_superuser,
                 obj.username, obj.first_name, obj.last_name, obj.email,
                 obj.is_staff, obj.is_active, obj.date_joined])
        self.stdout.write(f'  Utilisateurs: {qs.count()}')

    def _export_profiles(self, cur):
        qs = UserProfile.objects.all()
        for obj in qs:
            self._upsert(cur, 'store_userprofile',
                ['id', 'user_id', 'phone', 'address', 'wilaya'],
                [obj.id, obj.user_id,
                 getattr(obj, 'phone', ''), getattr(obj, 'address', ''),
                 getattr(obj, 'wilaya', '')])
        self.stdout.write(f'  Profils: {qs.count()}')

    def _export_orders(self, cur):
        qs = Order.objects.all()
        for obj in qs:
            self._upsert(cur, 'store_order',
                ['id', 'user_id', 'full_name', 'email', 'phone',
                 'delivery_address', 'wilaya', 'notes', 'payment_method',
                 'transaction_ref', 'total_price', 'status', 'admin_note',
                 'cgv_accepted', 'created_at', 'updated_at'],
                [obj.id, obj.user_id, obj.full_name, obj.email, obj.phone,
                 obj.delivery_address, getattr(obj, 'wilaya', ''),
                 getattr(obj, 'notes', ''), obj.payment_method,
                 getattr(obj, 'transaction_ref', ''), obj.total_price,
                 obj.status, getattr(obj, 'admin_note', ''),
                 getattr(obj, 'cgv_accepted', True),
                 obj.created_at, obj.updated_at])
        self.stdout.write(f'  Commandes: {qs.count()}')

    def _export_order_items(self, cur):
        qs = OrderItem.objects.all()
        for obj in qs:
            self._upsert(cur, 'store_orderitem',
                ['id', 'order_id', 'product_id', 'product_name', 'price', 'quantity', 'unit'],
                [obj.id, obj.order_id,
                 obj.product_id if obj.product_id else None,
                 obj.product_name, obj.price, obj.quantity,
                 getattr(obj, 'unit', 'kg')])
        self.stdout.write(f'  Articles commandes: {qs.count()}')

    def _export_slides(self, cur):
        try:
            qs = HeroSlide.objects.all()
            for obj in qs:
                self._upsert(cur, 'store_heroslide',
                    ['id', 'title', 'subtitle', 'image_url', 'is_active', 'order'],
                    [obj.id, obj.title, getattr(obj, 'subtitle', ''),
                     getattr(obj, 'image_url', ''), obj.is_active, getattr(obj, 'order', 0)])
            self.stdout.write(f'  Slides: {qs.count()}')
        except Exception as e:
            self.stdout.write(f'  Slides: ignorés ({e})')

    def _export_testimonials(self, cur):
        try:
            qs = Testimonial.objects.all()
            for obj in qs:
                self._upsert(cur, 'store_testimonial',
                    ['id', 'name', 'content', 'rating', 'is_active', 'avatar_url'],
                    [obj.id, obj.name, obj.content, obj.rating,
                     obj.is_active, getattr(obj, 'avatar_url', '')])
            self.stdout.write(f'  Témoignages: {qs.count()}')
        except Exception as e:
            self.stdout.write(f'  Témoignages: ignorés ({e})')

    def _export_contacts(self, cur):
        try:
            qs = ContactMessage.objects.all()
            for obj in qs:
                self._upsert(cur, 'store_contactmessage',
                    ['id', 'name', 'email', 'subject', 'message', 'created_at'],
                    [obj.id, obj.name, obj.email,
                     getattr(obj, 'subject', ''), obj.message, obj.created_at])
            self.stdout.write(f'  Messages contact: {qs.count()}')
        except Exception as e:
            self.stdout.write(f'  Messages contact: ignorés ({e})')

    def _export_newsletters(self, cur):
        try:
            qs = NewsletterSubscriber.objects.all()
            for obj in qs:
                self._upsert(cur, 'store_newslettersubscriber',
                    ['id', 'email', 'name', 'subscribed_at'],
                    [obj.id, obj.email,
                     getattr(obj, 'name', ''), getattr(obj, 'subscribed_at', None)],
                    conflict_col='email')
            self.stdout.write(f'  Newsletter: {qs.count()}')
        except Exception as e:
            self.stdout.write(f'  Newsletter: ignorés ({e})')
