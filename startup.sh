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

echo "=== Données de production (images statiques) ==="
python manage.py shell << 'EOF'
from store.models import Product, Category
import subprocess

# Recharger si les produits n'ont pas encore d'images /static/
has_static = Product.objects.filter(image_url__startswith='/static/').exists()

if not has_static:
    print("Rechargement avec images statiques...")
    Product.objects.all().delete()
    Category.objects.all().delete()
    r = subprocess.run(
        ['python', 'manage.py', 'loaddata', 'store/fixtures/production_data.json'],
        capture_output=True, text=True
    )
    print(r.stdout.strip() or r.stderr.strip())
    count = Product.objects.count()
    print(f"OK : {count} produits chargés avec images /static/")
else:
    count = Product.objects.count()
    print(f"Données OK : {count} produits avec images statiques")
EOF

echo "=== Démarrage Gunicorn ==="
exec gunicorn kaluun.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
