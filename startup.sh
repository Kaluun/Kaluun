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

echo "=== Chargement données production (si table vide) ==="
python manage.py shell << 'EOF'
from store.models import Product
if Product.objects.count() == 0:
    import subprocess
    r = subprocess.run(
        ['python', 'manage.py', 'loaddata', 'store/fixtures/production_data.json'],
        capture_output=True, text=True
    )
    print(r.stdout or r.stderr)
else:
    print(f"Données déjà présentes : {Product.objects.count()} produits")
EOF

echo "=== Démarrage Gunicorn ==="
exec gunicorn kaluun.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
