#!/usr/bin/env bash
set -e

echo "=== Migrations ==="
python manage.py migrate --noinput

echo "=== Superuser admin (si absent) ==="
python manage.py shell << 'EOF'
from django.contrib.auth.models import User
import os
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username=os.environ.get('ADMIN_USERNAME', 'admin'),
        email=os.environ.get('ADMIN_EMAIL_ADDR', 'kaluunexpresse@gmail.com'),
        password=os.environ.get('ADMIN_PASSWORD', 'Kaluun@2024!')
    )
    print("Superuser créé")
else:
    print("Superuser existe déjà")
EOF

echo "=== Chargement données de production ==="
python manage.py shell << 'EOF'
from store.models import Product, Category
import subprocess

# Charger si aucun produit, ou si les produits n'ont pas d'image_url (vieux fixtures)
needs_reload = (
    Product.objects.count() == 0 or
    not Product.objects.filter(image_url__isnull=False).exclude(image_url='').exists()
)

if needs_reload:
    print("Chargement des données de production...")
    Product.objects.all().delete()
    Category.objects.all().delete()
    r = subprocess.run(
        ['python', 'manage.py', 'loaddata', 'store/fixtures/production_data.json'],
        capture_output=True, text=True
    )
    print(r.stdout.strip() or r.stderr.strip())
    print(f"Produits chargés : {Product.objects.count()}")
else:
    print(f"Données OK : {Product.objects.count()} produits avec images")
EOF

echo "=== Démarrage Gunicorn ==="
exec gunicorn kaluun.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
